"""
dataloader.py

Creates train, validation and test dataloaders.
"""

import torch
from torch.utils.data import DataLoader

from src.dataset import AlzheimerDataset
from src.preprocess import train_transform, test_transform

# ==========================================================
# PATHS
# ==========================================================

TRAIN_DIR = "dataset/split/train"
VAL_DIR = "dataset/split/val"
TEST_DIR = "dataset/split/test"

# ==========================================================
# SETTINGS
# ==========================================================

BATCH_SIZE = 32

# ==========================================================
# DATASETS
# ==========================================================

train_dataset = AlzheimerDataset(
    root_dir=TRAIN_DIR,
    transform=train_transform
)

val_dataset = AlzheimerDataset(
    root_dir=VAL_DIR,
    transform=test_transform
)

test_dataset = AlzheimerDataset(
    root_dir=TEST_DIR,
    transform=test_transform
)

# ==========================================================
# DATALOADERS
# ==========================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)

# ==========================================================
# Get DataLoaders
# ==========================================================

def get_dataloaders():
    """
    Returns:
        train_loader,
        val_loader,
        test_loader
    """
    return train_loader, val_loader, test_loader