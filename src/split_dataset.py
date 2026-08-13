import os
import shutil
from sklearn.model_selection import train_test_split

# =====================================================
# PATHS
# =====================================================

SOURCE_DIR = "dataset/raw/combined_images"
DESTINATION_DIR = "dataset/split"

# =====================================================
# SPLIT RATIO
# =====================================================

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

RANDOM_STATE = 42

# =====================================================
# CREATE FOLDERS
# =====================================================

for split in ["train", "val", "test"]:

    split_path = os.path.join(DESTINATION_DIR, split)

    os.makedirs(split_path, exist_ok=True)

# =====================================================
# PROCESS EACH CLASS
# =====================================================

classes = sorted(os.listdir(SOURCE_DIR))

for cls in classes:

    class_path = os.path.join(SOURCE_DIR, cls)

    if not os.path.isdir(class_path):
        continue

    images = os.listdir(class_path)

    # -----------------------
    # Train Split
    # -----------------------

    train_images, temp_images = train_test_split(
        images,
        train_size=TRAIN_RATIO,
        random_state=RANDOM_STATE,
        shuffle=True
    )

    # -----------------------
    # Validation + Test
    # -----------------------

    val_images, test_images = train_test_split(
        temp_images,
        test_size=0.5,
        random_state=RANDOM_STATE,
        shuffle=True
    )

    # -----------------------
    # Create folders
    # -----------------------

    for split in ["train", "val", "test"]:

        os.makedirs(
            os.path.join(DESTINATION_DIR, split, cls),
            exist_ok=True
        )

    # -----------------------
    # Copy Images
    # -----------------------

    def copy_images(image_list, split):

        for image in image_list:

            src = os.path.join(class_path, image)

            dst = os.path.join(
                DESTINATION_DIR,
                split,
                cls,
                image
            )

            shutil.copy2(src, dst)

    copy_images(train_images, "train")
    copy_images(val_images, "val")
    copy_images(test_images, "test")

    print(f"{cls} completed.")

print("\nDataset Split Successfully!")