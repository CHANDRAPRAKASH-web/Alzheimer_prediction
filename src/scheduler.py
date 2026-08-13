"""
Learning Rate Scheduler
"""

from torch.optim.lr_scheduler import ReduceLROnPlateau


def get_scheduler(optimizer):

    scheduler = ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=3
    )

    return scheduler