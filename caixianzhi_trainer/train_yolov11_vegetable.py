# -*- coding: utf-8 -*-
"""
训练 YOLOv11n 蔬菜目标检测模型
--------------------------------------------------
- 直接 `python train_yolov11_veg.py` 运行，无需再手动传参。
- 环境依赖：
    pip install ultralytics matplotlib pandas
- 功能：
    * 读取指定 dataset.yaml
    * 使用预训练权重 yolo11n.pt 进行微调
    * 自动早停（mAP50-95 连续 PATIENCE 轮不提升）
    * 每轮保存权重到 runs/<run_name>/weights
    * 训练结束后绘制 loss 与 mAP 曲线
"""

import os
import multiprocessing
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from ultralytics import YOLO

# =========【参数区域】=========================================================
PROJECT_DIR   = Path(__file__).parent.resolve()                      # 项目根目录
DATA_YAML     = PROJECT_DIR / "vegetable_preprocessed/dataset.yaml"  # 数据集 YAML
PRETRAIN_WT   = PROJECT_DIR / "yolo11n.pt"                          # 预训练权重
EPOCHS        = 1                                                  # 训练轮数 (为了在3分钟内快速看到结果，设置为1)
BATCH_SIZE    = 8                                                    # 批大小 (CPU 建议 <=8)
IMG_SIZE      = 320                                                  # 输入尺寸
PATIENCE      = 4                                                  # 早停耐心轮数
WORKERS       = max(1, multiprocessing.cpu_count() // 2)            # DataLoader 进程数
# ============================================================================


def plot_curves(csv_path: Path):
    """根据 ultralytics 的 results.csv 绘制 Loss 与 mAP 曲线, 并合并为一张图"""
    df = pd.read_csv(csv_path)
    
    # ultralytics 的 epoch 从0开始计数，但显示时我们希望从1开始
    epochs_display = df["epoch"] + 1
    save_dir = csv_path.parent

    # 创建一个 1x2 的子图布局
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Training Metrics', fontsize=16)

    # --- Loss 曲线 (ax1) ---
    ax1.plot(epochs_display, df["train/box_loss"], 'o-', label="Train Box Loss")
    ax1.plot(epochs_display, df["val/box_loss"], 'o-',  label="Val Box Loss")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.set_title("Box Loss vs Epoch")
    ax1.legend()
    ax1.grid(True)

    # --- mAP 曲线 (ax2) ---
    ax2.plot(epochs_display, df["metrics/mAP50(B)"], 'o-', label="mAP@0.5")
    ax2.plot(epochs_display, df["metrics/mAP50-95(B)"], 'o-', label="mAP@0.5:0.95")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("mAP")
    ax2.set_title("mAP vs Epoch")
    ax2.legend()
    ax2.grid(True)
    
    # 调整布局并保存为一张图
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # 调整布局以适应主标题
    # 后端需要名为 'results.png' 的文件
    plt.savefig(save_dir / "results.png")
    plt.close(fig)


def start_training(
    data_yaml_path: str,
    base_model_path: str,
    epochs: int,
    batch_size: int,
    project_dir: str,
    name: str,
    device: str = 'cpu'  # 增加 device 参数，默认为 'cpu'
):
    """
    一个可被外部调用的、参数化的训练函数。

    :param data_yaml_path: 数据集 YAML 文件的完整路径。
    :param base_model_path: 预训练模型 (.pt) 的完整路径。
    :param epochs: 训练轮数。
    :param batch_size: 批大小。
    :param project_dir: 训练输出的总目录 (例如 'media/training_runs')。
    :param name: 本次训练的特定名称 (例如任务ID)。
    :param device: 训练设备 ('cpu' 或 '0', '1' 等)。
    :return: 训练结果的路径。
    """
    # 检查文件路径
    assert Path(data_yaml_path).exists(), f"数据集 YAML 不存在: {data_yaml_path}"
    assert Path(base_model_path).exists(), f"预训练权重不存在: {base_model_path}"

    print(f"[INFO] 训练输出将被保存到: {project_dir}/{name}")

    # 加载模型
    model = YOLO(base_model_path)

    # 启动训练
    results = model.train(
        data=data_yaml_path,
        epochs=epochs,
        batch=batch_size,
        imgsz=320,
        device=device,  # 使用传入的 device 参数
        workers=0,
        amp=False,       
        optimizer='SGD',
        project=project_dir,
        name=name,
        save_period=1,  # 每轮都保存 checkpoint
        verbose=True,
    )

    # 训练后自动生成图表
    csv_path = Path(results.save_dir) / 'results.csv'
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            if len(df) >= 1: # 只要有数据就尝试绘制
                plot_curves(csv_path)
                print(f"[INFO] 成功生成结果图表: {csv_path.parent / 'results.png'}")
            else:
                print(f"[WARN] results.csv 为空，无法绘制曲线图。")
        except Exception as e:
            # 增加更详细的错误输出
            print(f"[WARN] 绘制曲线图失败。错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"[WARN] 训练后未找到 results.csv，无法绘制自定义曲线图。")

    print(f"[DONE] 训练结束！查看 {results.save_dir} 目录获取权重与图表。")
    return results.save_dir

# 原始的 main 函数和绘图函数可以保留，用于独立的命令行调试，
# 但需要将其保护在 if __name__ == '__main__': 块中。
# 为简化与后端的集成，此处暂时移除它们。
# 您未来可以根据需要将它们加回来用于本地测试。
