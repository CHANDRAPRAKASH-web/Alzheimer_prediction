"""
=========================================================
Checkpoint Manager

Handles saving and loading model checkpoints.

Author  : CP
Project : NeuroVision AI
=========================================================
"""

from pathlib import Path
import json
import torch

from configs.config import (
    CHECKPOINT_DIR,
    SAVE_BEST_BY,
    SAVE_LAST_MODEL,
)

# ==========================================================
# Create Folder
# ==========================================================

Path(CHECKPOINT_DIR).mkdir(
    parents=True,
    exist_ok=True
)

BEST_MODEL = CHECKPOINT_DIR / "best_model.pth"
LAST_MODEL = CHECKPOINT_DIR / "last_model.pth"
BEST_METRICS = CHECKPOINT_DIR / "best_metrics.json"


# ==========================================================
# Save Checkpoint
# ==========================================================

def save_checkpoint(
        model,
        optimizer,
        scheduler,
        epoch,
        metrics
):
    """
    Saves the complete training state.
    """

    checkpoint = {

        "epoch": epoch,

        "model_state_dict":
            model.state_dict(),

        "optimizer_state_dict":
            optimizer.state_dict(),

        "scheduler_state_dict":
            scheduler.state_dict(),

        "metrics":
            metrics

    }

    if SAVE_LAST_MODEL:

        torch.save(
            checkpoint,
            LAST_MODEL
        )


# ==========================================================
# Save Best Model
# ==========================================================

def save_best_model(
        model,
        optimizer,
        scheduler,
        epoch,
        metrics
):
    """
    Saves the best model and metrics.
    """

    checkpoint = {

        "epoch": epoch,

        "model_state_dict":
            model.state_dict(),

        "optimizer_state_dict":
            optimizer.state_dict(),

        "scheduler_state_dict":
            scheduler.state_dict(),

        "metrics":
            metrics

    }

    torch.save(
        checkpoint,
        BEST_MODEL
    )

    with open(
            BEST_METRICS,
            "w"
    ) as f:

        json.dump(
            metrics,
            f,
            indent=4
        )


# ==========================================================
# Load Checkpoint
# ==========================================================

def load_checkpoint(
        checkpoint_path,
        model,
        optimizer=None,
        scheduler=None
):
    """
    Loads a saved checkpoint.
    """

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu"
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    if optimizer is not None:

        optimizer.load_state_dict(
            checkpoint["optimizer_state_dict"]
        )

    if scheduler is not None:

        scheduler.load_state_dict(
            checkpoint["scheduler_state_dict"]
        )

    epoch = checkpoint["epoch"]

    metrics = checkpoint["metrics"]

    return (
        model,
        optimizer,
        scheduler,
        epoch,
        metrics
    )


# ==========================================================
# Check Improvement
# ==========================================================

def is_best(
        current_metrics,
        best_metrics
):
    """
    Returns True if current model is better.
    """

    metric = SAVE_BEST_BY

    if best_metrics is None:

        return True

    return (
        current_metrics[metric]
        >
        best_metrics[metric]
    )


# ==========================================================
# Load Best Metrics
# ==========================================================

def load_best_metrics():

    if not BEST_METRICS.exists():

        return None

    with open(
            BEST_METRICS,
            "r"
    ) as f:

        return json.load(f)


# ==========================================================
# Check Existing Model
# ==========================================================

def best_model_exists():

    return BEST_MODEL.exists()


# ==========================================================
# Last Model Exists
# ==========================================================

def last_model_exists():

    return LAST_MODEL.exists()