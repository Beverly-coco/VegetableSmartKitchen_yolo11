import cv2
import numpy as np
import albumentations as A
from rembg import remove
from PIL import Image

# 1. 定义一个用于推理的预处理管道：尺寸标准化
preprocess_pipeline = A.Compose([
    A.Resize(width=640, height=640)
])

# 2. 定义一个可选的图像增强管道，可用于未来的模型训练
augmentation_pipeline = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(p=0.2),
    A.Rotate(limit=25, p=0.5),
])

def preprocess_image_for_inference(input_path: str, output_path: str) -> str:
    """
    对单张图像进行推理前的预处理。
    流程：去除背景 -> 尺寸标准化 (640x640)

    :param input_path: 原始图片的完整路径
    :param output_path: 处理后图片的保存路径
    :return: 处理后图片的保存路径
    """
    try:
        # 1. 使用 rembg 去除背景
        with open(input_path, 'rb') as i:
            with open(output_path, 'wb') as o:
                input_data = i.read()
                output_data = remove(input_data)
                o.write(output_data)

        # 2. 读取去背景后的图片 (OpenCV 需要 BGR 格式)
        # PIL 用于读取可能带 Alpha 通道的 PNG，然后转为 RGB
        img_pil = Image.open(output_path).convert('RGB')
        img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

        # 3. 使用 albumentations 统一尺寸
        processed = preprocess_pipeline(image=img_bgr)
        processed_image = processed['image']

        # 4. 保存最终处理好的图片
        cv2.imwrite(output_path, processed_image)

        return output_path

    except Exception as e:
        print(f"Error during image preprocessing: {e}")
        raise

def apply_augmentations(image_path: str):
    """
    对单张图像应用数据增强，此函数主要用于未来训练流程。
    """
    try:
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        augmented = augmentation_pipeline(image=image)
        augmented_image = augmented['image']
        
        # 返回增强后的图像数据，可以在训练脚本中直接使用
        return cv2.cvtColor(augmented_image, cv2.COLOR_RGB2BGR)
        
    except Exception as e:
        print(f"Error during image augmentation: {e}")
        raise 