"""
Optimizer
"""

import torch.optim as optim


def get_optimizer(model, lr, weight_decay):

    optimizer = optim.AdamW(
        model.parameters(),
        lr=lr,
        weight_decay=weight_decay
    )

    return optimizer