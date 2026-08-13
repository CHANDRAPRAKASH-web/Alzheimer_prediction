"""
=========================================================
Experiment Logger

Creates a unique CSV file for every experiment and
logs training metrics after each epoch.

Author  : CP
Project : NeuroVision AI
=========================================================
"""

from pathlib import Path
from datetime import datetime
import pandas as pd

from configs.config import LOG_DIR


# ==========================================================
# Create Log Directory
# ==========================================================

Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


# ==========================================================
# CSV Columns
# ==========================================================

COLUMNS = [

    "Model",

    "Epoch",

    "Train Loss",

    "Validation Loss",

    "Accuracy",

    "Balanced Accuracy",

    "Precision",

    "Recall",

    "F1 Score",

    "MCC",

    "ROC AUC",

    "Learning Rate",

    "Batch Size",

    "Epoch Time (s)",

    "GPU Memory (MB)",

    "Best Model"

]


# ==========================================================
# Create Experiment Log
# ==========================================================

def create_log_file(model_name,
                    batch_size,
                    learning_rate):
    """
    Creates a new CSV file for each experiment.

    Example
    -------
    ResNet50_B32_LR1e-4_20260710_213455.csv
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    lr = f"{learning_rate:.0e}"

    filename = (
        f"{model_name}"
        f"_B{batch_size}"
        f"_LR{lr}"
        f"_{timestamp}.csv"
    )

    log_file = LOG_DIR / filename

    df = pd.DataFrame(columns=COLUMNS)

    df.to_csv(
        log_file,
        index=False
    )

    return log_file


# ==========================================================
# Log One Epoch
# ==========================================================

def log_epoch(

        log_file,

        model_name,

        epoch,

        train_loss,

        val_loss,

        accuracy,

        balanced_accuracy,

        precision,

        recall,

        f1,

        mcc,

        roc_auc,

        learning_rate,

        batch_size,

        epoch_time,

        gpu_memory,

        best_model

):

    row = {

        "Model": model_name,

        "Epoch": epoch,

        "Train Loss": round(train_loss, 6),

        "Validation Loss": round(val_loss, 6),

        "Accuracy": round(accuracy, 4),

        "Balanced Accuracy": round(balanced_accuracy, 4),

        "Precision": round(precision, 4),

        "Recall": round(recall, 4),

        "F1 Score": round(f1, 4),

        "MCC": round(mcc, 4),

        "ROC AUC": (
            round(roc_auc, 4)
            if roc_auc is not None
            else None
        ),

        "Learning Rate": learning_rate,

        "Batch Size": batch_size,

        "Epoch Time (s)": round(epoch_time, 2),

        "GPU Memory (MB)": gpu_memory,

        "Best Model": best_model

    }

    pd.DataFrame([row]).to_csv(

        log_file,

        mode="a",

        header=False,

        index=False

    )


# ==========================================================
# Read Experiment
# ==========================================================

def read_logs(log_file):

    return pd.read_csv(log_file)


# ==========================================================
# List All Experiments
# ==========================================================

def list_experiments():

    return sorted(LOG_DIR.glob("*.csv"))


# ==========================================================
# Latest Experiment
# ==========================================================

def latest_experiment():

    files = list_experiments()

    if len(files) == 0:
        return None

    return files[-1]