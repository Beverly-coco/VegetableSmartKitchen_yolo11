# 导入 Django 渲染和响应模块
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.core.files.storage import FileSystemStorage
from django.conf import settings

# 导入标准库模块
import os
import uuid
import shutil
import zipfile
import tempfile
import threading
import sys
import json
import pandas as pd
import traceback
import cv2
import random
import yaml

# 用户验证和权限
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

# 序列化器和模型
from .serializers import UserSerializer
from .models import Profile

# YOLOv11 模型（使用 ultralytics 库）
from ultralytics import YOLO

from .utils.preprocess import preprocess_image_for_inference

# 动态添加 caixianzhi_trainer 目录到系统路径
sys.path.append(os.path.join(settings.BASE_DIR, '..', 'caixianzhi_trainer'))
from train_yolov11_vegetable import start_training

# -------------- 辅助函数：持久化训练任务状态 --------------
def _get_task_status_path(task_id):
    """获取指定任务ID的状态文件路径。"""
    return os.path.join(settings.MEDIA_ROOT, 'training_runs', str(task_id), 'status.json')

def _read_task_status(task_id):
    """从文件读取任务状态。"""
    status_path = _get_task_status_path(task_id)
    if not os.path.exists(status_path):
        return None
    try:
        with open(status_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def _write_task_status(task_id, status_info):
    """将任务状态写入文件。"""
    task_dir = os.path.join(settings.MEDIA_ROOT, 'training_runs', str(task_id))
    os.makedirs(task_dir, exist_ok=True)
    status_path = _get_task_status_path(task_id)
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(status_info, f, indent=4)

def _update_task_status(task_id, new_data):
    """更新任务状态文件中的字段。"""
    status_info = _read_task_status(task_id) or {}
    status_info.update(new_data)
    _write_task_status(task_id, status_info)

# -------------------------------------------------------------

# --- 知识库加载 ---
KNOWLEDGE_BASE = {}
try:
    knowledge_base_path = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
    with open(knowledge_base_path, 'r', encoding='utf-8') as f:
        KNOWLEDGE_BASE = json.load(f)
except FileNotFoundError:
    print("[WARN] 知识库(knowledge_base.json)未找到。营养信息将不可用。")
except json.JSONDecodeError:
    print("[WARN] 解析 knowledge_base.json 失败，请检查文件语法。")
# --------------------

# -------------- YOLO 模型加载部分 --------------
MODEL_PATH = os.path.join(settings.BASE_DIR, 'yolo11n.pt') # 训练好的模型路径

try:
    # 加载模型并立即将其移动到CPU，以避免占用GPU资源
    model = YOLO(MODEL_PATH).to('cpu')
    print("默认识别模型已成功加载到 CPU。")
except Exception as e:
    print(f"加载默认识别模型失败: {e}")
    model = None  # 如果加载失败，则设为 None
# --------------------------------------------

# "菜先知"单张图片识别视图
class DetectionView(APIView):
    permission_classes = [IsAuthenticated]  # 仅认证用户可访问

    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get("image")  # 从请求中获取图片文件
        if not image_file:
            return Response({'error': 'No image file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # 保存上传的原始图片
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))
        ext = os.path.splitext(image_file.name)[1]  # 获取扩展名
        unique_filename = f"{uuid.uuid4()}{ext}"  # 生成唯一文件名
        original_image_path = fs.save(unique_filename, image_file)  # 保存图片
        full_original_path = os.path.join(settings.MEDIA_ROOT, 'uploads', original_image_path)  # 获取完整路径

        # --- 新增：调用图像预处理模块 ---
        processed_filename = f"processed_{unique_filename}"
        full_processed_path = os.path.join(settings.MEDIA_ROOT, 'uploads', processed_filename)
        try:
            preprocess_image_for_inference(full_original_path, full_processed_path)
            # 使用预处理后的图片进行推理
            inference_image_path = full_processed_path
        except Exception as e:
            # 如果预处理失败，可以选择记录日志，并继续使用原图进行推理
            print(f"Image preprocessing failed: {e}. Falling back to original image.")
            inference_image_path = full_original_path
        # --------------------------------

        # -------- YOLO 实际预测逻辑 -----------
        if model is None:
            return Response({'error': 'YOLO model not loaded. Check MODEL_PATH.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # 在CPU上执行模型推理
            results = model(inference_image_path, device='cpu')
            
            # --- 增强：解析结果并附上知识库信息 ---
            detections = []
            if results:
                result = results[0]  # 处理单张图片的结果
                
                # --- 3. 修改图片保存方式 ---
                # 绘制检测框并获取图像数据
                result_image_array = result.plot() 
                
                # 定义保存路径
                result_image_dir = os.path.join(settings.MEDIA_ROOT, 'results')
                os.makedirs(result_image_dir, exist_ok=True)
                result_image_path = os.path.join(result_image_dir, unique_filename)
                
                # 使用 OpenCV 保存图像，对中文路径更友好
                cv2.imwrite(result_image_path, result_image_array)
                # -------------------------

                # 提取详细信息
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    class_name_en = result.names[class_id]
                    confidence = float(box.conf[0])
                    coords = box.xyxy[0].tolist()

                    knowledge = KNOWLEDGE_BASE.get(class_name_en, {
                        "name": class_name_en,
                        "description": "暂无该蔬菜的营养信息。",
                        "nutrition": {}
                    })

                    detections.append({
                        "class_name": class_name_en,
                        "chinese_name": knowledge.get('name'),
                        "confidence": confidence,
                        "box_coords": coords,
                        "knowledge": knowledge
                    })
            # ------------------------------------------

        except Exception as e:
            # --- 4. 增加详细错误日志打印 ---
            print("--- AN EXCEPTION OCCURRED ---")
            traceback.print_exc()
            print("---------------------------")
            return Response({'error': f'模型推理时发生错误: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 构建结果图像的访问 URL
        result_image_url = request.build_absolute_uri(
            os.path.join(settings.MEDIA_URL, 'results', unique_filename).replace('\\', '/')
        )
        return Response({
            'imageUrl': result_image_url,
            'detections': detections
        })

def process_dataset_zip(zip_file_path, destination_dir):
    """
    解压并验证数据集 ZIP 文件, 并自动创建 data.yaml 和划分数据集。(超强健壮版)
    """
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as z:
            namelist = [p.replace('\\\\', '/') for p in z.namelist()]
            
            # --- 1. 基础验证 ---
            images_dir_in_zip = next((p for p in namelist if p.endswith('images/')), None)
            labels_dir_in_zip = next((p for p in namelist if p.endswith('labels/')), None)

            if not images_dir_in_zip or not labels_dir_in_zip:
                return False, "压缩包中必须包含 'images/' 和 'labels/' 目录。"

            # --- 2. 解压 ---
            if os.path.exists(destination_dir):
                shutil.rmtree(destination_dir)
            z.extractall(path=destination_dir)
            

            # --- 3. 智能移动文件到根目录 ---
            # ... (代码与之前类似，处理二级目录问题)
            root_dirs = [d.split('/')[0] for d in namelist if '/' in d and not d.startswith('.') and d != '/']
            if root_dirs and len(set(root_dirs)) == 1:
                common_root_name = list(set(root_dirs))[0]
                common_root_path = os.path.join(destination_dir, common_root_name)
                if os.path.isdir(common_root_path):
                    for item in os.listdir(common_root_path):
                        shutil.move(os.path.join(common_root_path, item), os.path.join(destination_dir, item))
                    os.rmdir(common_root_path)

            images_dir = os.path.join(destination_dir, 'images')
            labels_dir = os.path.join(destination_dir, 'labels')

            # --- 4. 确定类别信息 ---
            nc = 0
            names = []
            classes_txt_path = os.path.join(destination_dir, 'classes.txt')
            if os.path.exists(classes_txt_path):
                with open(classes_txt_path, 'r', encoding='utf-8') as f:
                    names = [line.strip() for line in f if line.strip()]
                nc = len(names)
            else:
                max_id = -1
                for label_file in os.listdir(labels_dir):
                    if label_file.endswith('.txt'):
                        with open(os.path.join(labels_dir, label_file), 'r') as f:
                            for line in f:
                                max_id = max(max_id, int(line.split()[0]))
                nc = max_id + 1
                names = [f'class_{i}' for i in range(nc)]
            
            if nc == 0:
                return False, "无法确定数据集的类别数量。请确保标签文件存在或提供 classes.txt。"

            # --- 5. 划分训练/验证集 ---
            os.makedirs(os.path.join(images_dir, 'train'), exist_ok=True)
            os.makedirs(os.path.join(images_dir, 'valid'), exist_ok=True)
            os.makedirs(os.path.join(labels_dir, 'train'), exist_ok=True)
            os.makedirs(os.path.join(labels_dir, 'valid'), exist_ok=True)

            image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            random.shuffle(image_files)
            split_index = int(len(image_files) * 0.8)
            train_files = image_files[:split_index]
            valid_files = image_files[split_index:]

            for f in train_files:
                basename = os.path.splitext(f)[0]
                shutil.move(os.path.join(images_dir, f), os.path.join(images_dir, 'train', f))
                shutil.move(os.path.join(labels_dir, f'{basename}.txt'), os.path.join(labels_dir, 'train', f'{basename}.txt'))
            
            for f in valid_files:
                basename = os.path.splitext(f)[0]
                shutil.move(os.path.join(images_dir, f), os.path.join(images_dir, 'valid', f))
                shutil.move(os.path.join(labels_dir, f'{basename}.txt'), os.path.join(labels_dir, 'valid', f'{basename}.txt'))

            # --- 6. 创建 data.yaml ---
            yaml_path = os.path.join(destination_dir, 'data.yaml')
            yaml_content = {
                # 'path': os.path.abspath(destination_dir), # 移除绝对路径，让路径相对于 data.yaml
                'train': os.path.join('images', 'train'),
                'val': os.path.join('images', 'valid'),
                'nc': nc,
                'names': names
            }
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_content, f, allow_unicode=True)

        return True, "数据集处理和配置成功。"
    except Exception as e:
        traceback.print_exc()
        return False, f"处理数据集时发生严重错误: {e}"


class DatasetUploadView(APIView):
    """
    处理数据集上传（ZIP包）的视图。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        zip_file = request.FILES.get("dataset")
        if not zip_file or not zip_file.name.endswith('.zip'):
            return Response({'error': '必须上传一个 .zip 格式的数据集文件。'}, status=status.HTTP_400_BAD_REQUEST)

        # 使用临时目录安全地处理上传的文件
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_zip_path = os.path.join(temp_dir, zip_file.name)
            
            # 将上传的ZIP文件写入临时路径
            with open(temp_zip_path, 'wb+') as temp_f:
                for chunk in zip_file.chunks():
                    temp_f.write(chunk)

            # 定义最终数据集的存储路径
            dataset_name = os.path.splitext(zip_file.name)[0]
            destination_path = os.path.join(settings.MEDIA_ROOT, 'datasets', dataset_name)
            
            # 调用函数处理ZIP文件
            success, message = process_dataset_zip(temp_zip_path, destination_path)
            
            if not success:
                # 如果处理失败，删除可能已创建的空目录
                if os.path.exists(destination_path):
                    shutil.rmtree(destination_path)
                return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': '数据集上传和处理成功。',
            'dataset_name': dataset_name,
            'storage_path': destination_path
        })

def run_yolo_training_background(task_id, dataset_name, epochs, batch_size, base_model_name):
    """
    一个在后台线程中运行的函数，用于执行实际的 YOLO 训练。
    """
    # --- 解决 OMP: Error #15 ---
    # 在导入任何可能使用 OpenMP 的库 (如 PyTorch) 之前设置此环境变量。
    # 这可以防止因链接了多个 OpenMP 运行时而导致的程序崩溃。
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    try:
        # 1. 初始状态：标记为"进行中"
        _update_task_status(task_id, {"status": "running", "progress": 0, "message": "训练准备中..."})
        
        # 准备路径
        dataset_dir = os.path.join(settings.MEDIA_ROOT, 'datasets', dataset_name)
        data_yaml_path = os.path.join(dataset_dir, 'data.yaml')
        base_model_path = os.path.join(settings.BASE_DIR, '..', 'caixianzhi_trainer', base_model_name)
        project_dir = os.path.join(settings.MEDIA_ROOT, 'training_runs')

        # 调用核心训练函数，并获取实际的保存路径
        save_dir = start_training(
            data_yaml_path=data_yaml_path,
            base_model_path=base_model_path,
            epochs=epochs,
            batch_size=batch_size,
            project_dir=project_dir,
            name=str(task_id),
            device='cpu'  # 显式指定使用 CPU
        )

        # 更新状态，包含实际的保存路径
        _update_task_status(task_id, {
            'status': 'completed',
            'save_dir': str(save_dir)
        })

    except Exception as e:
        # 捕获任何异常，记录为失败状态
        error_message = traceback.format_exc()
        _update_task_status(task_id, {'status': 'failed', 'error': str(e)})
        print(f"--- 训练任务 {task_id} 失败 ---\n{error_message}")


class TrainView(APIView):
    """
    启动一个异步训练任务。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        dataset_name = request.data.get('dataset_name')
        epochs = int(request.data.get('epochs', 10))
        batch_size = int(request.data.get('batch_size', 8))
        base_model = request.data.get('base_model', 'yolo11n.pt')
        
        # 简单的输入验证
        dataset_path = os.path.join(settings.MEDIA_ROOT, 'datasets', dataset_name)
        if not dataset_name or not os.path.isdir(dataset_path):
            return Response({'error': f"数据集 '{dataset_name}' 不存在。"}, status=status.HTTP_400_BAD_REQUEST)

        # 创建任务ID并初始化状态
        task_id = uuid.uuid4()
        _write_task_status(task_id, {
            'task_id': str(task_id),
            'status': 'starting',
            'error': None,
        })

        # 在后台线程中启动训练
        thread = threading.Thread(
            target=run_yolo_training_background,
            args=(task_id, dataset_name, epochs, batch_size, base_model)
        )
        thread.start()

        # 立即返回成功响应
        return Response({
            'message': '训练任务已成功启动，您可以在稍后查看结果。',
            'task_id': str(task_id)
        }, status=status.HTTP_202_ACCEPTED)


class TrainResultView(APIView):
    """
    获取指定训练任务的结果。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id, *args, **kwargs):
        task_info = _read_task_status(task_id)
        if not task_info:
            return Response({'error': '未找到该训练任务'}, status=status.HTTP_404_NOT_FOUND)

        response_data = {
            'status': task_info.get('status'),
            'visualization_url': None,
            'error': task_info.get('error')
        }

        # 如果训练完成，则构建可视化图片的URL
        if response_data['status'] == 'completed':
            # 优先从 status 文件中获取准确的 run 目录
            results_dir = task_info.get('save_dir')
            
            # 兼容旧任务，如果 status 中没有 save_dir，则使用旧方法拼接
            if not results_dir:
                results_dir = os.path.join(settings.MEDIA_ROOT, 'training_runs', str(task_id))

            result_image_path = os.path.join(results_dir, 'results.png') 
            
            if os.path.exists(result_image_path):
                # 从完整的 results_dir 中提取出相对路径部分用于URL构建
                relative_results_dir = os.path.relpath(results_dir, settings.MEDIA_ROOT)
                url = request.build_absolute_uri(
                    os.path.join(settings.MEDIA_URL, relative_results_dir, 'results.png').replace('\\', '/')
                )
                response_data['visualization_url'] = url
        
        return Response(response_data)


class AvailableModelsView(APIView):
    """
    提供可选的预训练基础模型列表。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        models = []
        try:
            trainer_dir = os.path.join(settings.BASE_DIR, '..', 'caixianzhi_trainer')
            for filename in os.listdir(trainer_dir):
                if filename.lower().endswith('.pt'):
                    models.append(filename)
        except Exception as e:
            print(f"Error scanning for pre-trained models: {e}")
            return Response({'error': '无法扫描可用的基础模型。'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(models)

class AvailableDatasetsView(APIView):
    """
    提供已上传的数据集列表。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        datasets = []
        try:
            datasets_dir = os.path.join(settings.MEDIA_ROOT, 'datasets')
            if os.path.isdir(datasets_dir):
                for dirname in os.listdir(datasets_dir):
                    # 确保它是一个目录
                    if os.path.isdir(os.path.join(datasets_dir, dirname)):
                        datasets.append(dirname)
        except Exception as e:
            print(f"Error scanning for datasets: {e}")
            return Response({'error': '无法扫描可用的数据集。'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(datasets)

# 登录视图类
class LoginView(APIView):
    authentication_classes = []  # 登录视图不需要认证
    permission_classes = []      # 登录视图不需要权限

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")  # 获取用户名
        password = request.data.get("password")  # 获取密码
        user = authenticate(username=username, password=password)  # 验证用户

        if user:
            token, created = Token.objects.get_or_create(user=user)  # 获取或创建 token
            return Response({"token": token.key})  # 返回 token
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)  # 登录失败

# 登出视图类
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # 必须登录

    def post(self, request, *args, **kwargs):
        try:
            request.user.auth_token.delete()  # 删除 token
            return Response(status=status.HTTP_204_NO_CONTENT)  # 返回空响应表示成功
        except (AttributeError, Token.DoesNotExist):
            return Response({"error": "No token found"}, status=status.HTTP_400_BAD_REQUEST)  # 找不到 token

# 用户资料视图类
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]  # 必须登录

    # 获取用户资料
    def get(self, request, *args, **kwargs):
        Profile.objects.get_or_create(user=request.user)  # 若无则创建用户扩展信息
        serializer = UserSerializer(request.user)  # 序列化用户信息
        return Response(serializer.data)  # 返回序列化数据

    # 修改用户资料
    def post(self, request, *args, **kwargs):
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)  # 获取或创建扩展资料

        serializer = UserSerializer(user, data=request.data, partial=True)  # 用请求数据填充序列化器
        if serializer.is_valid():
            # 更新用户信息
            user.username = request.data.get('username', user.username)
            profile.gender = request.data.get('gender', profile.gender)

            # 如果上传了新头像，则替换
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']

            # 保存更新
            user.save()
            profile.save()

            return Response(UserSerializer(user).data)  # 返回更新后的用户数据
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # 校验失败返回错误信息
