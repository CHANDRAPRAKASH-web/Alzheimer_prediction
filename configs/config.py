import torch
from pathlib import Path

# ==========================================================
# PROJECT PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_ROOT / "dataset"

TRAIN_DIR = DATASET_DIR / "split" / "train"
VAL_DIR = DATASET_DIR / "split" / "val"
TEST_DIR = DATASET_DIR / "split" / "test"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
LOG_DIR = OUTPUT_DIR / "logs"
PLOT_DIR = OUTPUT_DIR / "plots"

# ==========================================================
# TRAINING
# ==========================================================

IMAGE_SIZE = 224

NUM_CLASSES = 4

BATCH_SIZE = 32

EPOCHS = 30

LEARNING_RATE = 1e-4

WEIGHT_DECAY = 1e-4

RANDOM_SEED = 42

# ==========================================================
# DEVICE
# ==========================================================

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

# ==========================================================
# MODEL
# ==========================================================

MODEL_NAME = "ResNet50"

# ==========================================================
# CHECKPOINT SETTINGS
# ==========================================================

SAVE_BEST_BY = "f1"

SAVE_LAST_MODEL = True

# ==========================================================
# CLASS NAMES
# ==========================================================

CLASS_NAMES = [
    "Non Demented",
    "Very Mild Demented",
    "Mild Demented",
    "Moderate Demented"
]