# “菜先知” - 模型训练模块 (`caixianzhi_trainer`)

本项目是“菜先知”系统的核心算法模块，负责蔬菜目标检测模型的训练。它基于 `ultralytics` (YOLO) 框架，提供从数据预处理、数据增强到模型训练、结果可视化的完整工作流。

整个模块被设计为可由外部 API（如 `caixianzhi_backend` 项目）驱动，实现自动化、参数化的训练任务。

## 模块技术栈

- **核心框架**: [Ultralytics (YOLO)](https://ultralytics.com/)
- **数据处理**: OpenCV, Albumentations
- **辅助库**: Matplotlib, Pandas

## 文件与目录结构详解

```
caixianzhi_trainer/
│
├── vegetable_preprocess.py     # 核心脚本1: 数据预处理与增强
├── train_yolov11_vegetable.py  # 核心脚本2: 模型训练
│
├── yolo11n.pt                  # 默认的预训练权重文件 (可扩展)
│
├── vegetable-datasets/         # 目录: 存放原始的、待处理的数据集
├── vegetable_preprocessed/     # (自动生成) 目录: 存放预处理后的YOLO格式数据集
└── runs/                       # (自动生成) 目录: 存放YOLO训练日志、权重和结果图表
```

### 1. 核心脚本

#### `vegetable_preprocess.py`

此脚本负责将任何格式的原始数据集转换为符合 YOLO 训练标准的格式，并进行数据增强。

- **功能**:
  1.  **统一尺寸**: 将所有图片和对应的边界框（Bounding Box）调整到指定尺寸（如 `640x640`）。
  2.  **数据增强 (Data Augmentation)**: 对训练集应用一系列视觉变换，以扩充数据量、提升模型泛化能力。
  3.  **格式转换**: 读取 YOLO 格式的`.txt`标注文件。
- **技术实现**:
  - 使用 `cv2` (OpenCV) 读取和写入图片。
  - 使用 `albumentations` 库构建强大的数据增强管道 (`get_aug_pipeline` 函数)，包含水平翻转、亮度对比度调整、旋转、模糊等。
  - `process_split` 函数负责处理单个数据子集（训练/验证/测试），对训练集应用数据增强，并保存结果。
  - 脚本通过 `argparse` 接收命令行参数，可以灵活指定输入/输出目录、图片尺寸和增强数量。

#### `train_yolov11_vegetable.py`

此脚本是模型训练的执行入口，封装了 YOLOv11 的训练过程。

- **功能**:
  1.  **参数化训练**: 定义了一个核心函数 `start_training`，接收所有必要的训练参数（如数据集配置、预训练模型、轮数、批大小等），使其能被其他程序方便地调用。
  2.  **模型加载**: 使用 `ultralytics.YOLO` 类加载一个预训练好的模型（如 `yolo11n.pt`），在此基础上进行微调（Transfer Learning）。
  3.  **结果可视化**: 定义了 `plot_curves` 函数，用于在训练结束后，读取 `results.csv` 文件并使用 `matplotlib` 绘制损失和 mAP（平均精度均值）曲线图，帮助分析训练效果。
- **技术实现**:
  - 直接调用 `model.train()` 方法启动 `ultralytics` 框架的内置训练循环。
  - 训练配置中启用了 `save_period=1`，确保每一轮的权重都被保存，便于中断后恢复。
  - 训练结果（包含权重、日志、CSV 文件、曲线图等）会自动保存在 `runs/` 目录下的一个以任务名命名的子文件夹中。

### 2. 核心目录

- **`vegetable-datasets/`**
  - **用途**: 存放原始数据集的地方。理想的结构是包含 `train`, `val`, `test` 三个子目录，每个子目录内再分别包含 `images` 和 `labels` 文件夹。
- **`vegetable_preprocessed/`**
  - **用途**: 由 `vegetable_preprocess.py` 自动生成的目录，存放处理好的、可直接用于训练的数据。其结构与 `vegetable-datasets/` 相同，但图片和标注都经过了尺寸统一和数据增强。
- **`runs/`**
  - **用途**: 由 `ultralytics` 框架在训练时自动生成的目录。每次调用 `start_training` 都会在这里创建一个新的子目录（如 `runs/detect/train1/`），其中包含：
    - `weights/`: 存放模型权重，`best.pt` 是其中最重要的最佳模型。
    - `results.csv`: 包含每一轮训练的详细指标数据。
    - `loss_curve.png`, `map_curve.png`: 由本项目的脚本生成的训练曲线图。
    - 其他 `ultralytics` 生成的验证结果图表。

## 完整使用流程

### 1. 环境准备

确保已安装所有必要的 Python 库。

```bash
pip install ultralytics opencv-python albumentations matplotlib pandas tqdm
```

### 2. 准备原始数据集

将您的数据集放入 `vegetable-datasets/` 目录。目录结构应如下所示：

```
vegetable-datasets/
├── train/
│   ├── images/
│   │   ├── 001.jpg
│   │   └── ...
│   └── labels/
│       ├── 001.txt
│       └── ...
└── val/
    ├── images/
    └── labels/
```

_标注文件 (`.txt`) 应为 YOLO 格式: `<class_id> <x_center> <y_center> <width> <height>`_。

### 3. 执行数据预处理

运行预处理脚本，生成可用于训练的数据集。

```bash
python vegetable_preprocess.py --input_dir ./vegetable-datasets --output_dir ./vegetable_preprocessed --img_size 640 640 --num_aug 3
```

- `--input_dir`: 原始数据目录。
- `--output_dir`: 处理后数据的存放目录。
- `--img_size`: 目标图片尺寸（宽 高）。
- `--num_aug`: 为每张训练图片生成多少个增强副本。

### 4. （可选）本地直接执行训练

如果您想在本地快速测试训练过程，可以修改 `train_yolov11_vegetable.py` 中的参数，然后直接运行：

```bash
# 1. (可选) 修改 train_yolov11_vegetable.py 脚本底部的参数
# 2. 运行脚本
python train_yolov11_vegetable.py
```

### 5. API 驱动的训练（标准用法）

在实际项目中，`caixianzhi_backend` 服务会直接导入并调用 `train_yolov11_vegetable.py` 中的 `start_training` 函数，并动态传入从前端页面获取的参数。

### 6. 获取最终模型

训练完成后，进入最新生成的 `runs/detect/trainX` 目录，在 `weights/` 子文件夹中找到 `best.pt` 文件。这就是您训练出的最佳模型，可以将其部署到后端用于识别。
