import os
import shutil
import argparse
from pathlib import Path
from tqdm import tqdm
import cv2
import albumentations as A

# ---------------------------
# Utility functions
# ---------------------------

def read_yolo_labels(label_path):
    """Read YOLO txt label file and return (classes, boxes) lists.
    boxes are in YOLO format: (xc, yc, w, h) normalised to [0,1]."""
    classes, boxes = [], []
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue
            classes.append(int(parts[0]))
            boxes.append([float(x) for x in parts[1:]])
    return classes, boxes


def write_yolo_labels(label_path, classes, boxes):
    """Write YOLO txt label file from (classes, boxes) lists."""
    with open(label_path, 'w') as f:
        for cls, box in zip(classes, boxes):
            f.write(f"{cls} {' '.join(f'{v:.6f}' for v in box)}\n")


# ---------------------------
# Albumentations pipelines
# ---------------------------

def get_resize_pipeline(size):
    # size: (w, h)
    return A.Compose([
        A.Resize(size[1], size[0])
    ], bbox_params=A.BboxParams(format='yolo', label_fields=['category_ids']))


def get_aug_pipeline(size):
    # Basic but effective augmentations for small datasets
    return A.Compose([
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.2),
        A.RandomBrightnessContrast(p=0.3),
        A.ShiftScaleRotate(shift_limit=0.05, scale_limit=0.15, rotate_limit=20, border_mode=cv2.BORDER_CONSTANT, p=0.5),
        A.MotionBlur(blur_limit=5, p=0.1)
    ], bbox_params=A.BboxParams(format='yolo', label_fields=['category_ids']))


# ---------------------------
# Core processing routine
# ---------------------------

def process_split(input_dir: Path, output_dir: Path, img_size=(640, 640), split='train', num_aug=2):
    images_dir = input_dir / split / 'images'
    labels_dir = input_dir / split / 'labels'

    out_images_dir = output_dir / split / 'images'
    out_labels_dir = output_dir / split / 'labels'

    out_images_dir.mkdir(parents=True, exist_ok=True)
    out_labels_dir.mkdir(parents=True, exist_ok=True)

    resize_pipeline = get_resize_pipeline(img_size)
    aug_pipeline = get_aug_pipeline(img_size)

    img_files = [f for f in images_dir.iterdir() if f.suffix.lower() in {'.jpg', '.jpeg', '.png'}]

    print(f"Processing {split} set ({len(img_files)} images)…")
    for img_path in tqdm(img_files):
        label_path = labels_dir / (img_path.stem + '.txt')

        # Read image + labels
        image = cv2.imread(str(img_path))
        if image is None:
            continue  # skip unreadable
        if label_path.exists():
            classes, boxes = read_yolo_labels(label_path)
        else:
            classes, boxes = [], []

        # --- 1. Save resized original ---
        resized = resize_pipeline(image=image, bboxes=boxes, category_ids=classes)
        base_img_out = out_images_dir / img_path.name
        base_lbl_out = out_labels_dir / label_path.name
        cv2.imwrite(str(base_img_out), resized['image'])
        write_yolo_labels(base_lbl_out, resized['category_ids'], resized['bboxes'])

        # --- 2. Data augmentation for training set ---
        if split == 'train' and num_aug > 0 and boxes:
            for i in range(num_aug):
                aug = aug_pipeline(image=image, bboxes=boxes, category_ids=classes)
                final = resize_pipeline(image=aug['image'], bboxes=aug['bboxes'], category_ids=aug['category_ids'])

                aug_img_name = f"{img_path.stem}_aug{i}{img_path.suffix}"
                aug_lbl_name = f"{img_path.stem}_aug{i}.txt"

                cv2.imwrite(str(out_images_dir / aug_img_name), final['image'])
                write_yolo_labels(out_labels_dir / aug_lbl_name, final['category_ids'], final['bboxes'])


# ---------------------------
# Main entry point
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Preprocess and (optionally) augment YOLO-v11 vegetable dataset.")
    parser.add_argument('--input_dir', required=True, help='Path to original dataset root (vegetable-datasets)')
    parser.add_argument('--output_dir', required=True, help='Path to save processed dataset')
    parser.add_argument('--img_size', type=int, nargs=2, default=[640, 640], metavar=('W', 'H'), help='Final image size')
    parser.add_argument('--num_aug', type=int, default=2, help='Number of augmented copies per training image')
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)

    for split in ['train', 'val', 'test']:
        process_split(input_path, output_path, tuple(args.img_size), split, args.num_aug if split == 'train' else 0)


if __name__ == '__main__':
    main()
