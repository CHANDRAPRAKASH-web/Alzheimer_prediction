"""
=========================================================
Visualization Utilities

Generates publication-quality evaluation plots.

Author : CP
Project : NeuroVision AI
=========================================================
"""

from pathlib import Path

from sklearn.metrics import (
    roc_curve,
    auc
)

from sklearn.preprocessing import label_binarize

import matplotlib.pyplot as plt
import numpy as np

from sklearn.metrics import ConfusionMatrixDisplay

# ==========================================================
# Confusion Matrix
# ==========================================================

def plot_confusion_matrix(

        confusion_matrix,

        class_names,

        save_path,

        model_name

):
    """
    Generates a publication-quality confusion matrix.

    Parameters
    ----------
    confusion_matrix : ndarray

    class_names : list

    save_path : Path

    model_name : str
    """

    save_path = Path(save_path)

    save_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.figure(figsize=(10, 8))

    display = ConfusionMatrixDisplay(

        confusion_matrix=confusion_matrix,

        display_labels=class_names

    )

    display.plot(

        cmap="Blues",

        values_format="d",

        colorbar=True

    )

    plt.title(

        f"{model_name}\nConfusion Matrix",

        fontsize=18,

        fontweight="bold"

    )

    plt.xlabel(

        "Predicted Label",

        fontsize=14

    )

    plt.ylabel(

        "True Label",

        fontsize=14

    )

    plt.xticks(rotation=20)

    plt.tight_layout()

    plt.savefig(

        save_path,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()

    print()

    print(f"Saved Confusion Matrix → {save_path}")

# ==========================================================
# ROC Curve
# ==========================================================

def plot_roc_curve(

        labels,

        probabilities,

        class_names,

        save_path,

        model_name

):
    """
    Generates publication-quality multiclass ROC curve.
    """

    save_path = Path(save_path)

    save_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    labels = np.asarray(labels)

    probabilities = np.asarray(
        probabilities,
        dtype=np.float64
    )

    n_classes = len(class_names)

    labels = label_binarize(
        labels,
        classes=np.arange(n_classes)
    )

    plt.figure(figsize=(10, 8))

    # Random Guess
    plt.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        linewidth=2,
        color="black",
        label="Random Guess"
    )

    # ROC for every class
    for i in range(n_classes):

        fpr, tpr, _ = roc_curve(

            labels[:, i],

            probabilities[:, i]

        )

        roc_auc = auc(
            fpr,
            tpr
        )

        plt.plot(

            fpr,

            tpr,

            linewidth=2,

            label=f"{class_names[i]} (AUC = {roc_auc:.4f})"

        )

    plt.xlim([0.0, 1.0])

    plt.ylim([0.0, 1.05])

    plt.xlabel(
        "False Positive Rate",
        fontsize=14
    )

    plt.ylabel(
        "True Positive Rate",
        fontsize=14
    )

    plt.title(

        f"{model_name}\nMulticlass ROC Curve",

        fontsize=18,

        fontweight="bold"

    )

    plt.legend(

        loc="lower right",

        fontsize=10

    )

    plt.grid(alpha=0.3)

    plt.tight_layout()

    plt.savefig(

        save_path,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()

    print()

    print(f"Saved ROC Curve -> {save_path}")

# ==========================================================
# Confidence Histogram
# ==========================================================

def plot_confidence_histogram(

        confidences,

        save_path,

        model_name

):
    """
    Generates prediction confidence histogram.
    """

    save_path = Path(save_path)

    save_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    confidences = np.asarray(confidences) * 100

    plt.figure(figsize=(10, 6))

    plt.hist(

        confidences,

        bins=20,

        edgecolor="black"

    )

    plt.title(

        f"{model_name}\nPrediction Confidence Distribution",

        fontsize=18,

        fontweight="bold"

    )

    plt.xlabel(

        "Prediction Confidence (%)",

        fontsize=14

    )

    plt.ylabel(

        "Number of Images",

        fontsize=14

    )

    plt.grid(alpha=0.3)

    plt.tight_layout()

    plt.savefig(

        save_path,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()

    print()

    print(f"Saved Confidence Histogram -> {save_path}")
