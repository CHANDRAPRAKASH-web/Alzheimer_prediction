"""
=========================================================
NeuroVision AI - Inference Engine

Loads the trained Alzheimer's classification model and
performs inference on a single MRI image.

Returns:
- Predicted class
- Confidence score
- Class probabilities

Author  : CP
Project : NeuroVision AI
=========================================================
"""


import numpy as np
import cv2


from src.gradcam import GradCAM

from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

# --------------------------------------------------------
# Configuration
# --------------------------------------------------------

from configs.config import *

# --------------------------------------------------------
# Model
# --------------------------------------------------------

from models.resnet50 import build_model

# --------------------------------------------------------
# Checkpoint
# --------------------------------------------------------

from src.checkpoint import load_checkpoint


# =========================================================
# Inference Transform
# =========================================================

def get_inference_transform():
    """
    Returns the preprocessing pipeline used for inference.

    IMPORTANT:
    The normalization values must match the validation/test
    preprocessing used during model training.
    """

    transform = transforms.Compose([

        transforms.Resize(
            (IMAGE_SIZE, IMAGE_SIZE)
        ),

        transforms.ToTensor(),

        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )

    ])

    return transform


# =========================================================
# Load Model
# =========================================================

def load_inference_model(device):
    """
    Builds the model and loads the best trained checkpoint.

    Parameters
    ----------
    device : torch.device

    Returns
    -------
    model : torch.nn.Module
        Trained model ready for inference.
    """

    # -----------------------------------------------------
    # Build Model Architecture
    # -----------------------------------------------------

    model = build_model()

    model = model.to(device)

    # -----------------------------------------------------
    # Load Best Checkpoint
    # -----------------------------------------------------

    checkpoint_path = (
        CHECKPOINT_DIR / "best_model.pth"
    )

    model, _, _, epoch, metrics = load_checkpoint(

        checkpoint_path,

        model

    )

    # -----------------------------------------------------
    # Evaluation Mode
    # -----------------------------------------------------

    model.eval()

    print(
        f"Loaded best model from epoch: {epoch}"
    )

    return model


# =========================================================
# Prepare Image
# =========================================================

def prepare_image(image):
    """
    Converts an input image into a model-ready tensor.

    Parameters
    ----------
    image : PIL.Image.Image

    Returns
    -------
    image_tensor : torch.Tensor
        Shape = (1, C, H, W)
    """

    # -----------------------------------------------------
    # Ensure RGB
    # -----------------------------------------------------

    image = image.convert("RGB")

    # -----------------------------------------------------
    # Apply Inference Transform
    # -----------------------------------------------------

    transform = get_inference_transform()

    image_tensor = transform(image)

    # -----------------------------------------------------
    # Add Batch Dimension
    #
    # (C, H, W)
    #       ↓
    # (1, C, H, W)
    # -----------------------------------------------------

    image_tensor = image_tensor.unsqueeze(0)

    return image_tensor


# =========================================================
# Predict
# =========================================================

def predict_image(
    model,
    image,
    device
):
    """
    Performs inference on a single MRI image.

    Parameters
    ----------
    model : torch.nn.Module
        Trained classification model.

    image : PIL.Image.Image
        Input MRI image.

    device : torch.device
        CPU or CUDA device.

    Returns
    -------
    result : dict

        {
            "predicted_class": str,
            "predicted_index": int,
            "confidence": float,
            "probabilities": dict
        }
    """

    # -----------------------------------------------------
    # Prepare Image
    # -----------------------------------------------------

    image_tensor = prepare_image(image)

    image_tensor = image_tensor.to(device)

    # -----------------------------------------------------
    # Inference
    # -----------------------------------------------------

    with torch.no_grad():

        outputs = model(image_tensor)

        # Use FP32 before softmax for numerical stability
        probabilities = torch.softmax(
            outputs.float(),
            dim=1
        )

    # -----------------------------------------------------
    # Get Prediction
    # -----------------------------------------------------

    confidence, predicted_index = torch.max(

        probabilities,

        dim=1

    )

    predicted_index = predicted_index.item()

    confidence = confidence.item()

    # -----------------------------------------------------
    # Convert Probabilities to Python Dictionary
    # -----------------------------------------------------

    probabilities = (

        probabilities
        .squeeze(0)
        .cpu()
        .numpy()
        .tolist()

    )

    class_probabilities = {

        class_name: probability

        for class_name, probability in zip(

            CLASS_NAMES,

            probabilities

        )

    }

    # -----------------------------------------------------
    # Result
    # -----------------------------------------------------

    result = {

        "predicted_class":
            CLASS_NAMES[predicted_index],

        "predicted_index":
            predicted_index,

        "confidence":
            confidence,

        "probabilities":
            class_probabilities

    }

    return result

# =========================================================
# Grad-CAM Explanation
# =========================================================

def generate_gradcam_explanation(
    model,
    image,
    device
):
    """
    Generates a Grad-CAM explanation for an uploaded MRI.

    Parameters
    ----------
    model : torch.nn.Module
        Trained classification model.

    image : PIL.Image.Image
        Original uploaded MRI image.

    device : torch.device
        CPU or CUDA device.

    Returns
    -------
    overlay_rgb : numpy.ndarray
        Grad-CAM overlay in RGB format.

    heatmap : numpy.ndarray
        Raw normalized Grad-CAM heatmap.

    predicted_class_idx : int
        Class index used to generate Grad-CAM.
    """

    # -----------------------------------------------------
    # Prepare Original Image
    # -----------------------------------------------------

    original_image = image.convert("RGB")

    original_array = np.array(
        original_image
    )

    # -----------------------------------------------------
    # Apply Inference Transform
    # -----------------------------------------------------

    transform = get_inference_transform()

    image_tensor = transform(
        original_image
    )

    image_tensor = (
        image_tensor
        .unsqueeze(0)
        .to(device)
    )

    # -----------------------------------------------------
    # Create Grad-CAM
    # -----------------------------------------------------

    gradcam = GradCAM(
        model=model,
        target_layer=model.layer4[-1]
    )

    # -----------------------------------------------------
    # Generate Heatmap
    #
    # IMPORTANT:
    # Grad-CAM requires gradients.
    # Do NOT wrap this section in torch.no_grad().
    # -----------------------------------------------------

    with torch.enable_grad():

        heatmap = gradcam.generate(
            image_tensor
        )

    # -----------------------------------------------------
    # Get Predicted Class
    # -----------------------------------------------------

    with torch.no_grad():

        outputs = model(
            image_tensor
        )

        predicted_class_idx = (
            torch.argmax(
                outputs,
                dim=1
            ).item()
        )

    # -----------------------------------------------------
    # Create Overlay
    #
    # Existing GradCAM.overlay() uses OpenCV.
    # Convert RGB -> BGR before passing the image.
    # -----------------------------------------------------

    original_bgr = cv2.cvtColor(
        original_array,
        cv2.COLOR_RGB2BGR
    )

    overlay_bgr = gradcam.overlay(
        original_image=original_bgr,
        heatmap=heatmap,
        alpha=0.4
    )

    # -----------------------------------------------------
    # Convert Back to RGB for Streamlit
    # -----------------------------------------------------

    overlay_rgb = cv2.cvtColor(
        overlay_bgr,
        cv2.COLOR_BGR2RGB
    )

    return (
        overlay_rgb,
        heatmap,
        predicted_class_idx
    )