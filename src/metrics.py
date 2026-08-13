"""
=========================================================
Metrics for Alzheimer's Disease Classification
=========================================================

This module computes all evaluation metrics used during
training and evaluation.

Included Metrics:
-----------------
- Accuracy
- Balanced Accuracy
- Precision
- Recall
- F1 Score
- Matthews Correlation Coefficient (MCC)
- Confusion Matrix
- ROC-AUC (One-vs-Rest Multiclass)

Author : CP
Project : NeuroVision AI
=========================================================
"""

import numpy as np

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    matthews_corrcoef,
    confusion_matrix,
    roc_auc_score,
)


# =========================================================
# Accuracy
# =========================================================

def calculate_accuracy(y_true, y_pred):
    return accuracy_score(y_true, y_pred)


# =========================================================
# Balanced Accuracy
# =========================================================

def calculate_balanced_accuracy(y_true, y_pred):
    return balanced_accuracy_score(y_true, y_pred)


# =========================================================
# Precision
# =========================================================

def calculate_precision(y_true, y_pred):

    return precision_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )


# =========================================================
# Recall
# =========================================================

def calculate_recall(y_true, y_pred):

    return recall_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )


# =========================================================
# F1 Score
# =========================================================

def calculate_f1(y_true, y_pred):

    return f1_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )


# =========================================================
# Matthews Correlation Coefficient
# =========================================================

def calculate_mcc(y_true, y_pred):

    return matthews_corrcoef(
        y_true,
        y_pred
    )


# =========================================================
# Confusion Matrix
# =========================================================

def calculate_confusion_matrix(y_true, y_pred):

    return confusion_matrix(
        y_true,
        y_pred
    )


# =========================================================
# ROC AUC (Multiclass)
# =========================================================

def calculate_roc_auc(y_true, y_prob):

    """
    Parameters
    ----------
    y_true : Ground truth labels

    y_prob : Predicted probabilities
             Shape = (N, Number_of_Classes)

    Returns
    -------
    Weighted ROC-AUC

    """

   
    print(type(y_prob))
    print(np.asarray(y_prob).shape)

    y_true = np.asarray(y_true)

    y_prob = np.asarray(y_prob)


    return roc_auc_score(
        y_true,
        y_prob,
        multi_class="ovr",
        average="weighted"
    )


# =========================================================
# Complete Metrics
# =========================================================

def calculate_metrics(y_true, y_pred):

    """
    Returns all metrics except ROC-AUC.

    ROC-AUC requires prediction probabilities,
    therefore it is computed separately.
    """

    metrics = {

        "accuracy":
            calculate_accuracy(y_true, y_pred),

        "balanced_accuracy":
            calculate_balanced_accuracy(y_true, y_pred),

        "precision":
            calculate_precision(y_true, y_pred),

        "recall":
            calculate_recall(y_true, y_pred),

        "f1":
            calculate_f1(y_true, y_pred),

        "mcc":
            calculate_mcc(y_true, y_pred),

    }

    return metrics


# =========================================================
# Complete Evaluation
# =========================================================

def full_evaluation(y_true, y_pred, y_prob=None):

    """
    Returns a dictionary containing every evaluation metric.

    If probabilities are supplied,
    ROC-AUC is also calculated.
    """

    results = calculate_metrics(y_true, y_pred)

    results["confusion_matrix"] = calculate_confusion_matrix(
        y_true,
        y_pred
    )

    if y_prob is not None:

        try:

            results["roc_auc"] = calculate_roc_auc(
                y_true,
                y_prob
            )

        except Exception as e:


            print("\n========== ROC AUC ERROR ==========")
            print(type(e).__name__)
            print(e)
            print("===================================\n")

            raise



    else:

        results["roc_auc"] = None

    return results