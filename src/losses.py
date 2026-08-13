"""
Loss Functions
"""

import torch.nn as nn


def get_loss():

    criterion = nn.CrossEntropyLoss()

    return criterion