"""
ResNet50 Model
"""

import torch.nn as nn
from torchvision import models


def build_model(num_classes=4):

    # Load pretrained ResNet50
    model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)

    # Replace classifier
    in_features = model.fc.in_features

    model.fc = nn.Linear(
        in_features,
        num_classes
    )

    return model