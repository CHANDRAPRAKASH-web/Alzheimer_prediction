"""
=========================================================
Training Engine

Part 1
Training Loop

Author : CP
Project : NeuroVision AI
=========================================================
"""

import torch
from torch.amp import autocast, GradScaler
from tqdm import tqdm

from src.metrics import calculate_metrics


# ==========================================================
# Train One Epoch
# ==========================================================

def train_one_epoch(
    model,
    dataloader,
    criterion,
    optimizer,
    device,
    scaler,
    gradient_clip=1.0
):
    """
    Train model for one epoch.

    Returns
    -------
    Dictionary containing:
        loss
        accuracy
        precision
        recall
        f1
        mcc
        predictions
        labels
        probabilities
    """

    # --------------------------------------------
    # Training Mode
    # --------------------------------------------

    model.train()

    running_loss = 0.0

    total_samples = 0

    predictions = []

    labels_list = []

    probabilities = []

    progress_bar = tqdm(
        dataloader,
        desc="Training",
        leave=False
    )

    # --------------------------------------------
    # Batch Loop
    # --------------------------------------------

    for batch in progress_bar:

        # ----------------------------------------
        # Move to GPU
        # ----------------------------------------

        if len(batch) == 3:
            images, labels, _ = batch
        else:
            images, labels = batch

        images = images.to(device)
        labels = labels.to(device)
        # ----------------------------------------
        # Zero Gradients
        # ----------------------------------------

        optimizer.zero_grad(set_to_none=True)

        # ----------------------------------------
        # Mixed Precision
        # ----------------------------------------

        with autocast(device_type="cuda"):

            outputs = model(images)

            loss = criterion(outputs, labels)

        # ----------------------------------------
        # Backward Pass
        # ----------------------------------------

        scaler.scale(loss).backward()

        # ----------------------------------------
        # Gradient Clipping
        # ----------------------------------------

        scaler.unscale_(optimizer)

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            gradient_clip
        )

        # ----------------------------------------
        # Optimizer Step
        # ----------------------------------------

        scaler.step(optimizer)

        scaler.update()

        # ----------------------------------------
        # Running Loss
        # ----------------------------------------

        batch_size = images.size(0)

        running_loss += loss.item() * batch_size

        total_samples += batch_size

        # ----------------------------------------
        # Predictions
        # ----------------------------------------

        probs = torch.softmax(outputs.float(), dim=1)

        preds = torch.argmax(probs, dim=1)

        predictions.extend(
            preds.cpu().numpy().tolist()
        )

        labels_list.extend(
            labels.cpu().numpy().tolist()
        )

        probabilities.extend(
            probs.detach().cpu().numpy().tolist()
        )

        # ----------------------------------------
        # Live Accuracy
        # ----------------------------------------

        correct = (
            torch.tensor(predictions)
            ==
            torch.tensor(labels_list)
        ).sum().item()

        accuracy = correct / len(labels_list)

        progress_bar.set_postfix({

            "Loss": f"{loss.item():.4f}",

            "Acc": f"{accuracy:.4f}"

        })



    # --------------------------------------------
    # Epoch Loss
    # --------------------------------------------

    epoch_loss = running_loss / total_samples

    # --------------------------------------------
    # Metrics
    # --------------------------------------------

    metrics = calculate_metrics(
        labels_list,
        predictions
    )

    metrics["loss"] = epoch_loss

    metrics["predictions"] = predictions

    metrics["labels"] = labels_list

    metrics["probabilities"] = probabilities

    return metrics

# ==========================================================
# Validation One Epoch
# ==========================================================

def validate_one_epoch(
    model,
    dataloader,
    criterion,
    device
):
    """
    Validate model for one epoch.

    Returns
    -------
    Dictionary containing:
        loss
        accuracy
        precision
        recall
        f1
        mcc
        predictions
        labels
        probabilities
    """

    # --------------------------------------------
    # Evaluation Mode
    # --------------------------------------------

    model.eval()

    running_loss = 0.0

    total_samples = 0

    predictions = []

    labels_list = []

    probabilities = []

    progress_bar = tqdm(
        dataloader,
        desc="Validation",
        leave=False
    )

    # --------------------------------------------
    # Disable Gradient Computation
    # --------------------------------------------

    with torch.no_grad():

        for batch in progress_bar:


            # ------------------------------------
            # Move to GPU
            # ------------------------------------

            if len(batch) == 3:
                images, labels, _ = batch
            else:
                images, labels = batch

            images = images.to(device)
            labels = labels.to(device)
            # ------------------------------------
            # Mixed Precision
            # ------------------------------------

            with autocast(device_type="cuda"):

                outputs = model(images)

                loss = criterion(outputs, labels)

            batch_size = images.size(0)

            running_loss += loss.item() * batch_size

            total_samples += batch_size

            probs = torch.softmax(outputs.float(), dim=1)

            preds = torch.argmax(probs, dim=1)

            predictions.extend(
                preds.cpu().numpy().tolist()
            )

            labels_list.extend(
                labels.cpu().numpy().tolist()
            )

            probabilities.extend(
                probs.cpu().numpy().tolist()
            )

            # ------------------------------------
            # Live Accuracy
            # ------------------------------------

            correct = (
                torch.tensor(predictions)
                ==
                torch.tensor(labels_list)
            ).sum().item()

            accuracy = correct / len(labels_list)

            progress_bar.set_postfix({

                "Loss": f"{loss.item():.4f}",

                "Acc": f"{accuracy:.4f}"

            })

    # --------------------------------------------
    # Epoch Loss
    # --------------------------------------------

    epoch_loss = running_loss / total_samples

    metrics = calculate_metrics(

        labels_list,

        predictions

    )

    metrics["loss"] = epoch_loss

    metrics["predictions"] = predictions

    metrics["labels"] = labels_list

    metrics["probabilities"] = probabilities

    return metrics