"""
=========================================================
Inference Test

Tests the NeuroVision AI inference pipeline on one MRI.

Author  : CP
Project : NeuroVision AI
=========================================================
"""

import torch
from PIL import Image

from app.inference import (
    load_inference_model,
    predict_image
)


def main():

    print("=" * 60)
    print("NeuroVision AI")
    print("Inference Test")
    print("=" * 60)

    # -----------------------------------------------------
    # Device
    # -----------------------------------------------------

    device = torch.device(
        "cuda" if torch.cuda.is_available()
        else "cpu"
    )

    print(f"Device : {device}")

    # -----------------------------------------------------
    # Load Model
    # -----------------------------------------------------

    model = load_inference_model(device)

    print("Model Loaded")

    # -----------------------------------------------------
    # MRI Image Path
    # -----------------------------------------------------

    image_path = (
        "dataset/split/test/MildDemented/0a623e21-da2a-422d-90ae-2fd10760f07d.jpg"
    )

    # -----------------------------------------------------
    # Load Image
    # -----------------------------------------------------

    image = Image.open(image_path)

    print(f"Image Loaded : {image_path}")

    # -----------------------------------------------------
    # Prediction
    # -----------------------------------------------------

    result = predict_image(
        model=model,
        image=image,
        device=device
    )

    # -----------------------------------------------------
    # Display Results
    # -----------------------------------------------------

    print()
    print("=" * 60)
    print("Prediction Results")
    print("=" * 60)

    print(
        f"Predicted Class : "
        f"{result['predicted_class']}"
    )

    print(
        f"Confidence      : "
        f"{result['confidence'] * 100:.2f}%"
    )

    print()
    print("Class Probabilities")
    print("-" * 60)

    for class_name, probability in (
        result["probabilities"].items()
    ):

        print(
            f"{class_name:<25} "
            f": {probability * 100:.4f}%"
        )

    print("=" * 60)


if __name__ == "__main__":

    main()