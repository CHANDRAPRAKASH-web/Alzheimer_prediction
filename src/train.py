"""
=========================================================
Training Script

Main entry point for training the Alzheimer's classifier.

Author : CP
Project : NeuroVision AI
=========================================================
"""

from src.checkpoint import (
    save_checkpoint,
    save_best_model,
    load_best_metrics,
    is_best
)
import torch
from torch.amp import GradScaler
import time

from src.logger import (
    create_log_file,
    log_epoch
)

# ----------------------------
# Configuration
# ----------------------------

from configs.config import *

# ----------------------------
# Data
# ----------------------------

from src.dataloader import get_dataloaders

# ----------------------------
# Model
# ----------------------------

from models.resnet50 import build_model

# ----------------------------
# Training Components
# ----------------------------

from src.losses import get_loss
from src.optimizer import get_optimizer
from src.scheduler import get_scheduler
from src.metrics import calculate_roc_auc

# ----------------------------
# Engine
# ----------------------------

from src.engine import (
    train_one_epoch,
    validate_one_epoch
)


def main():

    print("=" * 60)
    print("NeuroVision AI")
    print("Alzheimer's Disease Classification")
    print("=" * 60)

    # -----------------------------------------
    # Device
    # -----------------------------------------

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Device : {device}")

    # -----------------------------------------
    # Data
    # -----------------------------------------

    train_loader, val_loader, test_loader = get_dataloaders()

    print("Data Loaded")

    # -----------------------------------------
    # Model
    # -----------------------------------------

    model = build_model()

    model.to(device)

    print("Model Loaded")

    # -----------------------------------------
    # Loss
    # -----------------------------------------

    criterion = get_loss()

    # -----------------------------------------
    # Optimizer
    # -----------------------------------------

    optimizer = get_optimizer(
        model,
        LEARNING_RATE,
        WEIGHT_DECAY
    )

    # -----------------------------------------
    # Scheduler
    # -----------------------------------------

    scheduler = get_scheduler(
        optimizer
    )
    # -----------------------------------------
    # Experiment Logger
    # -----------------------------------------

    log_file = create_log_file(
        model_name=MODEL_NAME,
        batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE
    )

    print(f"Experiment Log : {log_file}")
        

    # -----------------------------------------
    # AMP
    # -----------------------------------------

    scaler = GradScaler("cuda")

    # -----------------------------------------
    # Training Loop
    # -----------------------------------------

    print()

    print("Training Started...")

    print()
    print(f"Logging Results To : {log_file}")
    print()
    # -----------------------------------------
    # Best Model Tracking
    # -----------------------------------------

    best_metrics = load_best_metrics()

    for epoch in range(EPOCHS):

        print("-" * 60)

        print(f"Epoch {epoch + 1}/{EPOCHS}")

        start_time = time.time()

        train_metrics = train_one_epoch(

            model=model,

            dataloader=train_loader,

            criterion=criterion,

            optimizer=optimizer,

            device=device,

            scaler=scaler

        )

        val_metrics = validate_one_epoch(

            model=model,

            dataloader=val_loader,

            criterion=criterion,

            device=device

        )
        val_roc_auc = calculate_roc_auc(
            val_metrics["labels"],
            val_metrics["probabilities"]
        )
        epoch_time = time.time() - start_time

        scheduler.step(
            val_metrics["loss"]
        )
        # -----------------------------------------
        # Save Last Checkpoint
        # -----------------------------------------

        save_checkpoint(

            model=model,

            optimizer=optimizer,

            scheduler=scheduler,

            epoch=epoch + 1,

            metrics=val_metrics

        )
        # -----------------------------------------
        # Save Best Model
        # -----------------------------------------

        best_model = False

        if is_best(val_metrics, best_metrics):

            save_best_model(

                model=model,

                optimizer=optimizer,

                scheduler=scheduler,

                epoch=epoch + 1,

                metrics=val_metrics

            )

            best_metrics = val_metrics.copy()

            best_model = True

            print(
                f"⭐ New Best Model Saved! "
                f"Validation F1 = {val_metrics['f1']:.4f}"
            )
        if torch.cuda.is_available():

            gpu_memory = round(
                torch.cuda.max_memory_allocated() / 1024**2,
                2
            )

        else:

            gpu_memory = 0
        log_epoch(

            log_file=log_file,

            model_name=MODEL_NAME,

            epoch=epoch + 1,

            train_loss=train_metrics["loss"],

            val_loss=val_metrics["loss"],

            accuracy=val_metrics["accuracy"],

            balanced_accuracy=val_metrics["balanced_accuracy"],

            precision=val_metrics["precision"],

            recall=val_metrics["recall"],

            f1=val_metrics["f1"],

            mcc=val_metrics["mcc"],

            roc_auc=val_roc_auc,

            learning_rate=optimizer.param_groups[0]["lr"],

            batch_size=BATCH_SIZE,

            epoch_time=epoch_time,

            gpu_memory=gpu_memory,

            best_model=best_model

        )

        print()

        print(f"Train Loss : {train_metrics['loss']:.4f}")
        print(f"Val Loss   : {val_metrics['loss']:.4f}")

        print()

        print(f"Train Accuracy : {train_metrics['accuracy']:.4f}")
        print(f"Val Accuracy   : {val_metrics['accuracy']:.4f}")

        print()

        print(f"Train Accuracy : {train_metrics['accuracy']:.4f}")
        print(f"Val Accuracy   : {val_metrics['accuracy']:.4f}")

        print(f"Precision      : {val_metrics['precision']:.4f}")
        print(f"Recall         : {val_metrics['recall']:.4f}")
        print(f"F1 Score       : {val_metrics['f1']:.4f}")
        print(f"MCC            : {val_metrics['mcc']:.4f}")

        print(f"Learning Rate  : {optimizer.param_groups[0]['lr']:.6f}")

        print()

    print("=" * 60)

    print("Training Completed")

    print("=" * 60)


if __name__ == "__main__":

    main()