"""
=========================================================
NeuroVision AI - Streamlit Application

Interactive interface for Alzheimer's disease
classification from brain MRI images.

Features:
- MRI image upload
- Alzheimer's stage prediction
- Prediction confidence
- Class probability distribution

Author  : CP
Project : NeuroVision AI
=========================================================
"""

import streamlit as st
import torch
from PIL import Image

from app.inference import (
    load_inference_model,
    predict_image,
    generate_gradcam_explanation
)



# =========================================================
# Page Configuration
# =========================================================

st.set_page_config(
    page_title="NeuroVision AI",
    page_icon="🧠",
    layout="wide"
)


# =========================================================
# Device
# =========================================================

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)


# =========================================================
# Load Model
# =========================================================

@st.cache_resource
def get_model():
    """
    Loads the trained model once and caches it.

    This prevents the model from being reloaded every time
    the Streamlit application reruns.
    """

    model = load_inference_model(
        DEVICE
    )

    return model


# =========================================================
# Main Application
# =========================================================

def main():

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    st.title(
        "🧠 NeuroVision AI"
    )

    st.subheader(
        "Alzheimer's Disease Classification from Brain MRI"
    )

    st.write(
        """
        Upload a brain MRI image to obtain the model's
        predicted Alzheimer's disease classification and
        confidence scores.
        """
    )

    st.divider()

    # -----------------------------------------------------
    # Load Model
    # -----------------------------------------------------

    with st.spinner(
        "Loading NeuroVision AI model..."
    ):

        model = get_model()

    # -----------------------------------------------------
    # MRI Upload
    # -----------------------------------------------------

    uploaded_file = st.file_uploader(

        "Upload Brain MRI",

        type=[
            "jpg",
            "jpeg",
            "png"
        ]

    )

    # -----------------------------------------------------
    # No Image Uploaded
    # -----------------------------------------------------

    if uploaded_file is None:

        st.info(
            "Upload an MRI image to begin analysis."
        )

        return

    # -----------------------------------------------------
    # Open Image
    # -----------------------------------------------------

    try:

        image = Image.open(
            uploaded_file
        ).convert("RGB")

    except Exception:

        st.error(
            "The uploaded file could not be opened as an image."
        )

        return

    # -----------------------------------------------------
    # Display Uploaded Image
    # -----------------------------------------------------

    st.subheader(
        "Uploaded MRI"
    )

    st.image(

        image,

        caption="Uploaded Brain MRI",

        width=400

    )

    st.divider()

    # -----------------------------------------------------
    # Run Prediction
    # -----------------------------------------------------

    with st.spinner(
        "Analyzing MRI..."
    ):

        result = predict_image(

            model=model,

            image=image,

            device=DEVICE

        )

        gradcam_image, heatmap, gradcam_class_idx = (
            generate_gradcam_explanation(
                model=model,
                image=image,
                device=DEVICE
            )
        )

    # -----------------------------------------------------
    # Prediction Result
    # -----------------------------------------------------

    st.subheader(
        "Prediction Result"
    )

    prediction = result[
        "predicted_class"
    ]

    confidence = result[
        "confidence"
    ]

    # -----------------------------------------------------
    # Main Metrics
    # -----------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.metric(

            label="Predicted Class",

            value=prediction

        )

    with col2:

        st.metric(

            label="Confidence",

            value=f"{confidence * 100:.2f}%"

        )

    # -----------------------------------------------------
    # Class Probabilities
    # -----------------------------------------------------

    st.subheader(
        "Class Probabilities"
    )

    probabilities = result[
        "probabilities"
    ]

    for class_name, probability in probabilities.items():

        st.write(

            f"**{class_name}** — "
            f"{probability * 100:.2f}%"

        )

        st.progress(
            float(probability)
        )
    # =========================================================
    # Grad-CAM Explanation
    # =========================================================

    st.divider()

    st.subheader(
        "Model Explanation"
    )

    st.write(
        """
        Grad-CAM highlights the image regions that contributed
        most strongly to the model's prediction.
        """
    )

    col1, col2 = st.columns(2)

    with col1:

        st.image(
            image,
            caption="Original MRI",
            use_container_width=True
        )

    with col2:

        st.image(
            gradcam_image,
            caption=(
                f"Grad-CAM — "
                f"{result['predicted_class']}"
            ),
            use_container_width=True
        )

    # -----------------------------------------------------
    # Disclaimer
    # -----------------------------------------------------

    st.divider()

    st.warning(
        """
        Research Use Only: NeuroVision AI is an experimental
        machine-learning system and is not a medical diagnostic
        tool. Its predictions should not be used as a substitute
        for evaluation by qualified healthcare professionals.
        """
    )


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":

    main()