"""
=========================================================
Aid Axis - NeuroVision AI Module

Brain MRI Image Classification & Grad-CAM Model Explanation.
Preserves 100% of the existing model weights, preprocessing,
classification pipeline, and Grad-CAM visualization.
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
from app.cognitive.styles import render_metric_card

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)


@st.cache_resource
def get_model():
    """
    Loads the trained model once and caches it.
    Prevents reloading every time Streamlit reruns.
    """
    return load_inference_model(DEVICE)


def render_neurovision():
    """
    Renders the NeuroVision AI MRI Analysis module within Aid Axis.
    """
    st.markdown("## 🧠 NeuroVision AI — MRI Analysis")
    st.markdown(
        "<p style='color: #94A3B8; font-size: 1.05rem; margin-top: -0.5rem;'>"
        "Deep learning classification & Grad-CAM visual interpretability for brain MRI scans."
        "</p>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="aidaxis-notice">
            Upload an axial T1-weighted brain MRI scan to evaluate the deep learning classification 
            (ResNet50 backbone) and visualize localized activation heatmaps via Grad-CAM.
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # Load Model
    # -----------------------------------------------------
    with st.spinner("Initializing NeuroVision AI inference engine..."):
        model = get_model()

    # -----------------------------------------------------
    # MRI Upload
    # -----------------------------------------------------
    uploaded_file = st.file_uploader(
        "Upload Brain MRI Scan",
        type=["jpg", "jpeg", "png"],
        help="Supported formats: JPEG, PNG"
    )

    # -----------------------------------------------------
    # No Image Uploaded
    # -----------------------------------------------------
    if uploaded_file is None:
        st.markdown(
            """
            <div class="aidaxis-card" style="text-align: center; padding: 2.5rem 1rem; margin-top: 1rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📥</div>
                <h4 style="color: #F8FAFC;">Awaiting MRI Upload</h4>
                <p style="color: #94A3B8; font-size: 0.9rem; max-width: 440px; margin: 0 auto;">
                    Select or drag-and-drop a brain MRI image file to initiate automated 
                    classification and visual explanation.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # -----------------------------------------------------
    # Open Image
    # -----------------------------------------------------
    try:
        image = Image.open(uploaded_file).convert("RGB")
    except Exception:
        st.error("The uploaded file could not be opened as a valid image.")
        return

    # -----------------------------------------------------
    # Display Uploaded Image & Run Prediction
    # -----------------------------------------------------
    col_img, col_info = st.columns([1, 1])

    with col_img:
        st.markdown("#### Uploaded Brain MRI")
        st.image(image, caption="Uploaded Scan", use_container_width=True)

    with col_info:
        st.markdown("#### Model Inference")
        with st.spinner("Computing class probabilities and Grad-CAM activations..."):
            result = predict_image(
                model=model,
                image=image,
                device=DEVICE
            )
            gradcam_image, heatmap, gradcam_class_idx = generate_gradcam_explanation(
                model=model,
                image=image,
                device=DEVICE
            )

        pred_class = result["predicted_class"]
        conf = result["confidence"]
        
        # Color accent based on prediction
        accent = "teal" if "Non Demented" in pred_class else ("amber" if "Mild" in pred_class else "violet")

        render_metric_card(
            title="Predicted Classification",
            value=pred_class,
            subtitle="ResNet50 Deep Convolutional Network",
            accent_type=accent
        )

        render_metric_card(
            title="Prediction Confidence",
            value=f"{conf * 100:.2f}%",
            subtitle="Softmax output probability",
            accent_type="violet"
        )

    # -----------------------------------------------------
    # Class Probabilities
    # -----------------------------------------------------
    st.divider()
    st.markdown("### 📊 Class Probability Distribution")
    
    probabilities = result["probabilities"]
    cols_prob = st.columns(len(probabilities))
    
    for idx, (class_name, prob) in enumerate(probabilities.items()):
        with cols_prob[idx]:
            is_pred = (class_name == pred_class)
            pct_val = prob * 100.0
            border_c = "aidaxis-card-teal" if is_pred else ""
            st.markdown(
                f"""
                <div class="aidaxis-card {border_c}" style="padding: 0.9rem; margin-bottom: 0.5rem;">
                    <div style="font-size: 0.75rem; color: #94A3B8;">{class_name}</div>
                    <div style="font-size: 1.35rem; font-weight: 700; color: #F8FAFC; margin: 0.2rem 0;">
                        {pct_val:.2f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.progress(float(prob))

    # -----------------------------------------------------
    # Grad-CAM Explanation
    # -----------------------------------------------------
    st.divider()
    st.markdown("### 🔍 Grad-CAM Visual Model Explanation")
    st.write(
        "Gradient-weighted Class Activation Mapping (Grad-CAM) highlights the anatomical "
        "regions within the MRI scan that contributed most prominently to the classification decision."
    )

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.image(image, caption="Original Input MRI", use_container_width=True)
    with g_col2:
        st.image(
            gradcam_image,
            caption=f"Grad-CAM Heatmap Overlay — Class: {pred_class}",
            use_container_width=True
        )

    # -----------------------------------------------------
    # Clinical Research Disclaimer
    # -----------------------------------------------------
    st.markdown(
        """
        <div class="aidaxis-disclaimer">
            <strong>Research Use Only:</strong> NeuroVision AI is an experimental machine-learning 
            system and is not an approved medical diagnostic device. Its predictions and visual 
            explanations must not be used as a substitute for professional neurological evaluation 
            or clinical diagnosis.
        </div>
        """,
        unsafe_allow_html=True
    )
