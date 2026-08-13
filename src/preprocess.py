"""
preprocess.py

Contains all image preprocessing and augmentation
pipelines used throughout the project.
"""

from torchvision import transforms

# ==========================================================
# IMAGE CONFIGURATION
# ==========================================================

IMAGE_SIZE = (224, 224)

# ==========================================================
# IMAGENET NORMALIZATION
# (Required for pretrained ImageNet models)
# ==========================================================

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# ==========================================================
# TRAIN TRANSFORMS
# ==========================================================

train_transform = transforms.Compose([

    # Resize every image
    transforms.Resize(IMAGE_SIZE),

    # Small random rotation
    transforms.RandomRotation(degrees=10),

    # Small translation and zoom
    transforms.RandomAffine(
        degrees=0,
        translate=(0.05, 0.05),
        scale=(0.95, 1.05)
    ),

    # Convert PIL Image → Tensor
    transforms.ToTensor(),

    # Normalize pixels
    transforms.Normalize(
        mean=IMAGENET_MEAN,
        std=IMAGENET_STD
    )

])

# ==========================================================
# VALIDATION / TEST TRANSFORMS
# ==========================================================

test_transform = transforms.Compose([

    transforms.Resize(IMAGE_SIZE),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=IMAGENET_MEAN,
        std=IMAGENET_STD
    )

])