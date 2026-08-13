"""
=========================================================
Evaluation Script

Part 1
Loads the trained model and performs inference on the
test dataset.

Author : CP
Project : NeuroVision AI
=========================================================
"""

# ==========================================================
# Evaluation Folder
# ==========================================================

import shutil

import cv2

import json
from pathlib import Path



import pandas as pd

from sklearn.metrics import (
    classification_report
)

from src.metrics import (
    full_evaluation
)
import torch
from torch.amp import autocast
from tqdm import tqdm



# --------------------------------------------------------
# Configuration
# --------------------------------------------------------

from configs.config import *

# --------------------------------------------------------
# Model
# --------------------------------------------------------
# ==========================================================
# Evaluation Folder
# ==========================================================

EVALUATION_DIR = OUTPUT_DIR / "evaluation"

EVALUATION_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ==========================================================
# Misclassified Images Folder
# ==========================================================

MISCLASSIFIED_DIR = OUTPUT_DIR / "misclassified"

MISCLASSIFIED_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ==========================================================
# Grad-CAM Folder
# ==========================================================

GRADCAM_DIR = OUTPUT_DIR / "gradcam"

GRADCAM_DIR.mkdir(
    parents=True,
    exist_ok=True
)

from src.gradcam import GradCAM

from models.resnet50 import build_model

# --------------------------------------------------------
# Data
# --------------------------------------------------------

from src.dataloader import get_dataloaders

# --------------------------------------------------------
# Checkpoint
# --------------------------------------------------------

from src.checkpoint import load_checkpoint

from src.visualization import (
    plot_confusion_matrix,
    plot_roc_curve,
    plot_confidence_histogram
)


# ========================================================
# Inference
# ========================================================

def run_inference(model, dataloader, device):

    model.eval()

    predictions = []
    labels = []
    probabilities = []
    confidences = []
    image_paths = []

    progress_bar = tqdm(
        dataloader,
        desc="Testing"
    )

    with torch.no_grad():

        for batch in progress_bar:

            # -----------------------------------------
            # Dataset returns either
            # (images, labels)
            # or
            # (images, labels, paths)
            # -----------------------------------------

            if len(batch) == 3:

                images, targets, paths = batch

                image_paths.extend(paths)

            else:

                images, targets = batch

            images = images.to(device)

            targets = targets.to(device)

            with autocast("cuda"):

                outputs = model(images)

            probs = torch.softmax(outputs.float(), dim=1)

           

            conf, preds = torch.max(probs, dim=1)

            predictions.extend(
                preds.cpu().numpy().tolist()
            )

            labels.extend(
                targets.cpu().numpy().tolist()
            )

            probabilities.extend(
                probs.cpu().numpy().tolist()
            )

            confidences.extend(
                conf.cpu().numpy().tolist()
            )

    return {

        "labels": labels,

        "predictions": predictions,

        "probabilities": probabilities,

        "confidences": confidences,

        "image_paths": image_paths

    }
# ==========================================================
# Evaluate Results
# ==========================================================

def evaluate_results(results):

    labels = results["labels"]

    predictions = results["predictions"]

    probabilities = results["probabilities"]

    import numpy as np

    print("Labels shape:", np.array(labels).shape)
    print("Probabilities shape:", np.array(probabilities).shape)
    print("Unique labels:", np.unique(labels))

    # ------------------------------------------------------
    # Overall Metrics
    # ------------------------------------------------------

    metrics = full_evaluation(

        labels,

        predictions,

        probabilities

    )

    plot_confusion_matrix(

        confusion_matrix=metrics["confusion_matrix"],

        class_names=CLASS_NAMES,

        save_path=EVALUATION_DIR / "confusion_matrix.png",

        model_name=MODEL_NAME

    )

    plot_roc_curve(

        labels=labels,

        probabilities=probabilities,

        class_names=CLASS_NAMES,

        save_path=EVALUATION_DIR / "roc_curve.png",

        model_name=MODEL_NAME

    )

    plot_confidence_histogram(

        confidences=results["confidences"],

        save_path=EVALUATION_DIR /

        "confidence_histogram.png",

        model_name=MODEL_NAME

    )

    print()

    print("=" * 60)

    print("Evaluation Results")

    print("=" * 60)

    print(f"Accuracy            : {metrics['accuracy']:.4f}")

    print(f"Balanced Accuracy   : {metrics['balanced_accuracy']:.4f}")

    print(f"Precision           : {metrics['precision']:.4f}")

    print(f"Recall              : {metrics['recall']:.4f}")

    print(f"F1 Score            : {metrics['f1']:.4f}")

    print(f"MCC                 : {metrics['mcc']:.4f}")

    if metrics["roc_auc"] is not None:
        print(f"ROC AUC             : {metrics['roc_auc']:.4f}")
    else:
        print("ROC AUC             : Not Available")

    print("=" * 60)

    # ------------------------------------------------------
    # Save metrics.json
    # ------------------------------------------------------

    json_metrics = metrics.copy()

    json_metrics["confusion_matrix"] = (

        json_metrics["confusion_matrix"]

        .tolist()

    )

    with open(

        EVALUATION_DIR / "metrics.json",

        "w"

    ) as f:

        json.dump(

            json_metrics,

            f,

            indent=4

        )

    # ------------------------------------------------------
    # Per-Class Metrics
    # ------------------------------------------------------

    report = classification_report(

        labels,

        predictions,

        target_names=CLASS_NAMES,

        output_dict=True,

        zero_division=0

    )

    # ------------------------------------------------------
    # Save Classification Report (.txt)
    # ------------------------------------------------------

    report_text = classification_report(

        labels,

        predictions,

        target_names=CLASS_NAMES,

        zero_division=0

    )

    with open(

        EVALUATION_DIR / "classification_report.txt",

        "w"

    ) as f:

        f.write("=" * 60 + "\n")
        f.write("NeuroVision AI\n")
        f.write("Classification Report\n")
        f.write("=" * 60 + "\n\n")

        f.write(report_text)

    print("Saved Classification Report ->",
        EVALUATION_DIR / "classification_report.txt")

    df = pd.DataFrame(report).transpose()

    df.to_csv(

        EVALUATION_DIR /

        "per_class_metrics.csv"

    )

    print()

    print("Per-Class Metrics")

    print(df)

    return metrics

# ========================================================
# Main
# ========================================================

# ==========================================================
# Save Predictions CSV
# ==========================================================

def save_predictions(results):

    labels = results["labels"]

    predictions = results["predictions"]

    confidences = results["confidences"]

    image_paths = results["image_paths"]

    # ------------------------------------------------------
    # If dataset does not return image paths
    # ------------------------------------------------------

    if len(image_paths) == 0:

        image_paths = [

            f"Image_{i+1}"

            for i in range(len(labels))

        ]

    df = pd.DataFrame({

        "Image": image_paths,

        "Ground Truth": [

            CLASS_NAMES[i]

            for i in labels

        ],

        "Prediction": [

            CLASS_NAMES[i]

            for i in predictions

        ],

        "Confidence (%)": [

            round(c * 100, 2)

            for c in confidences

        ]

    })

    save_path = EVALUATION_DIR / "predictions.csv"

    df.to_csv(

        save_path,

        index=False

    )

    print()

    print(f"Saved Predictions CSV -> {save_path}")

# ==========================================================
# Save Misclassified Images
# ==========================================================

def save_misclassified(results):

    labels = results["labels"]
    predictions = results["predictions"]
    confidences = results["confidences"]
    image_paths = results["image_paths"]

    rows = []

    total = 0

    for label, pred, conf, image_path in zip(

            labels,
            predictions,
            confidences,
            image_paths

    ):

        if label == pred:
            continue

        total += 1

        true_name = CLASS_NAMES[label]
        pred_name = CLASS_NAMES[pred]

        folder = (

            MISCLASSIFIED_DIR /

            f"{true_name}_to_{pred_name}"

        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        source = Path(image_path)

        destination = folder / source.name

        shutil.copy2(
            source,
            destination
        )

        rows.append({

            "Image": source.name,

            "Ground Truth": true_name,

            "Prediction": pred_name,

            "Confidence (%)": round(conf * 100, 2)

        })

    df = pd.DataFrame(rows)

    df.to_csv(

        EVALUATION_DIR /

        "misclassified.csv",

        index=False

    )

    print()

    print(f"Misclassified Images : {total}")

    print(

        "Saved Misclassified CSV ->",

        EVALUATION_DIR / "misclassified.csv"

    )

    print(

        "Saved Images ->",

        MISCLASSIFIED_DIR

    )

# ==========================================================
# Generate Grad-CAM Images
# ==========================================================

# ==========================================================
# Generate Grad-CAM Images
# ==========================================================

def generate_gradcam_examples(
        model,
        dataloader,
        device,
        max_correct=5,
        max_wrong=5
):
    """
    Generates Grad-CAM visualizations for a few
    correctly classified and misclassified images.
    """

    gradcam = GradCAM(
        model=model,
        target_layer=model.layer4[-1]
    )

    model.eval()

    correct_count = 0
    wrong_count = 0

    for batch in dataloader:

        images, labels, paths = batch

        images = images.to(device)
        labels = labels.to(device)

        # Forward pass ONLY for prediction
        outputs = model(images)
        preds = outputs.argmax(dim=1)

        for i in range(len(images)):

            is_correct = preds[i].item() == labels[i].item()

            if is_correct and correct_count >= max_correct:
                continue

            if (not is_correct) and wrong_count >= max_wrong:
                continue

            # Single image
            image = images[i].unsqueeze(0)

            # Generate Grad-CAM
            heatmap = gradcam.generate(
                image=image,
                class_idx=preds[i].item()
            )

            # Read original image
            original = cv2.imread(paths[i])

            if original is None:
                continue

            overlay = gradcam.overlay(
                original_image=original,
                heatmap=heatmap
            )

            if is_correct:

                save_dir = GRADCAM_DIR / "Correct"
                correct_count += 1

            else:

                save_dir = GRADCAM_DIR / "Misclassified"
                wrong_count += 1

            gradcam.save(
                overlay,
                save_dir / Path(paths[i]).name
            )

        if (
            correct_count >= max_correct
            and
            wrong_count >= max_wrong
        ):
            break

    print()
    print("=" * 60)
    print("Grad-CAM Generation Completed")
    print(f"Correct Images       : {correct_count}")
    print(f"Misclassified Images : {wrong_count}")
    print("=" * 60)

def main():

    print("=" * 60)
    print("NeuroVision AI")
    print("Model Evaluation")
    print("=" * 60)

    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "cpu"
    )

    print(f"Device : {device}")

    # ----------------------------------------------------
    # Test Loader
    # ----------------------------------------------------

    _, _, test_loader = get_dataloaders()

    print("Test Data Loaded")

    # ----------------------------------------------------
    # Build Model
    # ----------------------------------------------------

    model = build_model()

    model.to(device)

    print("Model Built")

    # ----------------------------------------------------
    # Load Best Model
    # ----------------------------------------------------

    model, _, _, epoch, metrics = load_checkpoint(

        CHECKPOINT_DIR / "best_model.pth",

        model

    )

    print(f"Loaded Best Model From Epoch : {epoch}")

    # ----------------------------------------------------
    # Inference
    # ----------------------------------------------------

    results = run_inference(

        model,

        test_loader,

        device

    )
    metrics = evaluate_results(results)

    save_predictions(results)

    save_misclassified(results)

    generate_gradcam_examples(

        model,

        test_loader,

        device

    )


    print()

    print("Inference Completed")

    print(f"Images Evaluated : {len(results['labels'])}")

    return results


if __name__ == "__main__":

    main()