"""
dataset.py

Custom Dataset for Alzheimer's MRI Classification
"""

import os
from PIL import Image
from torch.utils.data import Dataset


class AlzheimerDataset(Dataset):

    def __init__(self, root_dir, transform=None):

        self.root_dir = root_dir
        self.transform = transform

        # =====================================================
        # Disease stages in clinical order
        # =====================================================

        self.classes = [
            "NonDemented",
            "VeryMildDemented",
            "MildDemented",
            "ModerateDemented"
        ]

        # =====================================================
        # Class → Label Mapping
        # =====================================================

        self.class_to_idx = {
            cls: idx
            for idx, cls in enumerate(self.classes)
        }

        # Reverse Mapping (Label → Class)

        self.idx_to_class = {
            idx: cls
            for cls, idx in self.class_to_idx.items()
        }

        # =====================================================
        # Store all image paths
        # =====================================================

        self.samples = []

        for cls in self.classes:

            class_path = os.path.join(root_dir, cls)

            if not os.path.isdir(class_path):
                continue

            for image_name in os.listdir(class_path):

                image_path = os.path.join(class_path, image_name)

                self.samples.append(
                    (
                        image_path,
                        self.class_to_idx[cls]
                    )
                )

    # =====================================================
    # Number of images
    # =====================================================

    def __len__(self):
        return len(self.samples)

    # =====================================================
    # Get one image
    # =====================================================

    def __getitem__(self, idx):

        image_path, label = self.samples[idx]

        image = Image.open(image_path).convert("RGB")

        if self.transform:
            image = self.transform(image)

        return image, label, image_path