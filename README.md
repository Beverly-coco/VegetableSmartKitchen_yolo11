# 菜先知 - 后端服务 (caixianzhi_backend)

本项目是“菜先知”蔬菜识别系统的后端部分，基于 Django 和 Django REST Framework 构建，负责处理所有核心业务逻辑，包括用户认证、图像识别、数据集管理和模型训练。

## 核心技术栈

- **Web 框架**: Django 5.2.3
- **API 框架**: Django REST Framework
- **对象检测**: Ultralytics YOLOv11
- **数据库**: MySQL (通过 `mysqlclient`)
- **跨域处理**: `django-cors-headers`
- **图像处理**: `opencv-python`, `Pillow`

## 环境设置与启动

1.  **安装依赖**:

    ```bash
    pip install -r requirements.txt
    ```

2.  **配置数据库**:
    打开 `config/settings.py` 文件，找到 `DATABASES` 配置项，根据你的本地 MySQL 环境修改数据库名、用户名和密码。

3.  **执行数据库迁移**:

    ```bash
    python manage.py migrate
    ```

4.  **启动服务 (重要)**:
    为了保证模型训练过程的稳定性，**必须**使用 `--noreload` 参数启动服务器，以防止其在训练文件变化时自动重启。
    ```bash
    python manage.py runserver --noreload
    ```
    服务将在 `http://127.0.0.1:8000/` 启动。

## 项目结构详解

```
caixianzhi_backend/
├── manage.py           # Django 项目管理入口脚本
├── requirements.txt    # 项目所有Python依赖库列表
├── media/              # 存放用户上传和系统生成的媒体文件
│   ├── uploads/        # 存放用户上传的原始图片
│   ├── results/        # 存放图片识别后的结果图
│   ├── datasets/       # 存放用户上传的数据集
│   └── training_runs/  # 存放所有模型训练的输出（权重、图表、日志、状态文件）
├── api/                # 核心业务逻辑应用
│   ├── urls.py         # 定义本应用所有API端点的路由
│   ├── views.py        # 包含所有API接口的视图逻辑（核心文件）
│   ├── models.py       # 定义数据库模型（如用户资料Profile）
│   ├── serializers.py  # 定义数据序列化器，用于模型与JSON的转换
│   ├── knowledge_base.json # 存储蔬菜营养信息的本地知识库
│   └── ...
└── config/             # Django 项目全局配置
    ├── settings.py     # 项目总配置文件（数据库、应用、中间件、媒体文件等）
    ├── urls.py         # 项目根路由配置，将 /api/ 请求分发到 api.urls
    └── ...
```

## 功能模块与技术实现

### 1. 用户认证与个人资料

- **技术**: 使用 Django REST Framework 内置的 `TokenAuthentication` 实现基于令牌的无状态认证。
- **流程**:
  - 用户通过 `POST /api/login/` 发送用户名和密码。
  - `LoginView` 使用 `authenticate` 函数验证用户，成功后返回一个唯一的 Token。
  - 前端需在后续所有请求的 `Authorization` 头中携带此 Token (例如: `Authorization: Token <your_token>`)。
- **相关文件**:
  - `api/views.py`: `LoginView`, `LogoutView`, `ProfileView`
  - `api/models.py`: `Profile` 模型通过 `OneToOneField` 扩展了 Django 的 User 模型，增加了性别和头像字段。
  - `api/serializers.py`: `UserSerializer` 和 `ProfileSerializer` 负责将用户数据安全地转换为 JSON 格式。

### 2. 蔬菜识别

- **功能**: 接收用户上传的单张图片，返回识别出的蔬菜类别、位置、置信度及相关营养知识。
- **技术实现**:
  - **模型**: 使用预训练的 `YOLOv11` 模型。
  - **资源管理**: 为了将宝贵的 GPU 资源留给模型训练，识别功能被强制在 **CPU** 上运行。
    - 在 `views.py` 启动时，通过 `model = YOLO(MODEL_PATH).to('cpu')` 将全局识别模型加载到 CPU。
    - 在 `DetectionView` 中，通过 `model(..., device='cpu')` 明确指定使用 CPU 进行推理。
  - **知识库**: 识别出的英文类别名会用于查询 `knowledge_base.json`，以附加中文名和营养信息。
- **相关文件**:
  - `api/views.py`: `DetectionView`

### 3. 数据集管理

- **功能**: 支持用户上传 ZIP 格式的数据集，并自动进行预处理。
- **技术实现**:
  - `DatasetUploadView` 接收 ZIP 文件。
  - `process_dataset_zip` 是一个强大的辅助函数，它会自动完成以下操作：
    1.  解压 ZIP 包。
    2.  智能处理二级目录问题（将文件从解压后的根目录中移出）。
    3.  自动划分训练集和验证集（默认 80/20 比例）。
    4.  根据标签文件或 `classes.txt` 自动生成 `data.yaml` 配置文件，供 YOLO 训练使用。
- **相关文件**:
  - `api/views.py`: `DatasetUploadView`, `process_dataset_zip`

### 4. 异步模型训练

- **功能**: 提供一个稳定、可靠的异步模型训练流程，并允许前端查询最终结果。
- **技术实现**:
  - **异步处理**:
    - `TrainView` 在接收到训练请求后，会立即创建一个后台 `threading.Thread` 来执行耗时的训练任务，并马上返回 `202 ACCEPTED` 响应，告知前端"任务已启动"。
  - **状态持久化 (核心)**:
    - 为了防止服务重启导致训练状态丢失，每个训练任务的状态都被持久化到其专属结果目录下的 `status.json` 文件中。
    - `_write_task_status`, `_read_task_status` 等辅助函数提供了对这个 JSON 文件的原子读写操作。
  - **后台执行**:
    - `run_yolo_training_background` 函数在后台线程中被调用。它会更新 `status.json` 的状态('running', 'completed', 'failed')，并调用 `caixianzhi_trainer` 模块中的 `start_training` 函数来执行真正的 YOLO 训练。
    - 为了避免内存溢出，`start_training` 函数中已将 `amp`（自动混合精度）参数设置为 `False`。
  - **结果获取**:
    - 前端可以通过轮询 `GET /api/train/result/<task_id>/` 接口来获取最新状态。
    - `TrainResultView` 负责读取 `status.json` 文件。当状态为 `'completed'` 时，它会构建并返回最终结果图片 (`results.png`) 的完整 URL。
- **相关文件**:
  - `api/views.py`: `TrainView`, `TrainResultView`, `run_yolo_training_background` 及状态读写辅助函数。
  - `caixianzhi_trainer/train_yolov11_vegetable.py`: 核心的 YOLO 训练脚本。

## API 端点 (Endpoints)

| 功能                 | HTTP 方法  | URL                                 | 认证需求 | 描述                                           |
| -------------------- | ---------- | ----------------------------------- | -------- | ---------------------------------------------- |
| **用户认证**         |            |                                     |          |                                                |
| 登录                 | `POST`     | `/api/login/`                       | 否       | 使用用户名和密码获取认证 Token。               |
| 登出                 | `POST`     | `/api/logout/`                      | 是       | 使当前用户的 Token 失效。                      |
| 获取/修改用户资料    | `GET/POST` | `/api/profile/`                     | 是       | 获取或更新用户的个人信息（如头像、性别）。     |
| **蔬菜识别**         |            |                                     |          |                                                |
| 上传单张图片识别     | `POST`     | `/api/upload-single/`               | 是       | 上传图片进行识别，返回结果图和结构化数据。     |
| **数据集与训练**     |            |                                     |          |                                                |
| 上传数据集           | `POST`     | `/api/upload-dataset/`              | 是       | 上传 ZIP 格式的数据集进行自动预处理。          |
| 获取可用数据集列表   | `GET`      | `/api/datasets/`                    | 是       | 返回所有已上传并处理好的数据集名称。           |
| 获取可用基础模型列表 | `GET`      | `/api/train/available-models/`      | 是       | 返回所有可用于微调的预训练模型文件。           |
| 启动异步训练         | `POST`     | `/api/train/`                       | 是       | 启动一个后台训练任务，并立即返回任务 ID。      |
| 获取训练结果         | `GET`      | `/api/train/result/<uuid:task_id>/` | 是       | 轮询此接口获取训练状态和最终的可视化图片 URL。 |
