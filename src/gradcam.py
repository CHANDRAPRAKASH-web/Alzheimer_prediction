"""
=========================================================
Grad-CAM

Explainable AI (XAI)

Generates Grad-CAM heatmaps for CNN models.

Author : CP
Project : NeuroVision AI
=========================================================
"""

import torch

import cv2
import numpy as np


# ==========================================================
# GradCAM
# ==========================================================

class GradCAM:

    """
    Grad-CAM implementation.

    Parameters
    ----------
    model : torch.nn.Module

    target_layer : torch.nn.Module
    """

    def __init__(

            self,

            model,

            target_layer

    ):

        self.model = model

        self.target_layer = target_layer

        self.activations = None

        self.gradients = None

        self._register_hooks()

    # ======================================================
    # Forward Hook
    # ======================================================

    def _forward_hook(

            self,

            module,

            inputs,

            outputs

    ):

        self.activations = outputs.detach()

    # ======================================================
    # Backward Hook
    # ======================================================

    def _backward_hook(

            self,

            module,

            grad_input,

            grad_output

    ):

        self.gradients = grad_output[0].detach()

    # ======================================================
    # Register Hooks
    # ======================================================

    def _register_hooks(self):

        self.target_layer.register_forward_hook(

            self._forward_hook

        )

        self.target_layer.register_full_backward_hook(

            self._backward_hook

        )
    # ======================================================
    # Generate Heatmap
    # ======================================================

    def generate(

            self,

            image,

            class_idx=None

    ):
        """
        Generates Grad-CAM heatmap.

        Parameters
        ----------
        image : torch.Tensor
            Shape = (1, C, H, W)

        class_idx : int or None
            Target class.
            If None, predicted class is used.

        Returns
        -------
        heatmap : numpy.ndarray
        """

        self.model.eval()

        # --------------------------------------------
        # Forward Pass
        # --------------------------------------------

        image = image.requires_grad_(True)



        outputs = self.model(image)

        if class_idx is None:

            class_idx = torch.argmax(
                outputs,
                dim=1
            ).item()

        # --------------------------------------------
        # Backward Pass
        # --------------------------------------------

        self.model.zero_grad()

        outputs[:, class_idx].backward()

        # --------------------------------------------
        # Global Average Pooling
        # --------------------------------------------

        weights = torch.mean(

            self.gradients,

            dim=(2, 3),

            keepdim=True

        )

        # --------------------------------------------
        # Weighted Feature Maps
        # --------------------------------------------

        cam = torch.sum(

            weights * self.activations,

            dim=1

        )

        cam = torch.relu(cam)

        # --------------------------------------------
        # Normalize
        # --------------------------------------------

        cam -= cam.min()

        cam /= (cam.max() + 1e-8)

        heatmap = cam.squeeze().cpu().numpy()

        return heatmap


    # ======================================================
    # Overlay Heatmap
    # ======================================================

    def overlay(

            self,

            original_image,

            heatmap,

            alpha=0.4

    ):
        """
        Overlays Grad-CAM heatmap on original image.

        Parameters
        ----------
        original_image : numpy.ndarray

        heatmap : numpy.ndarray

        alpha : float

        Returns
        -------
        overlay_image
        """

        # --------------------------------------------
        # Resize Heatmap
        # --------------------------------------------

        heatmap = cv2.resize(

            heatmap,

            (

                original_image.shape[1],

                original_image.shape[0]

            )

        )

        # --------------------------------------------
        # Convert to 0-255
        # --------------------------------------------

        heatmap = np.uint8(

            255 * heatmap

        )

        # --------------------------------------------
        # Apply Color Map
        # --------------------------------------------

        heatmap = cv2.applyColorMap(

            heatmap,

            cv2.COLORMAP_JET

        )

        # --------------------------------------------
        # Overlay
        # --------------------------------------------

        overlay = cv2.addWeighted(

            original_image,

            1 - alpha,

            heatmap,

            alpha,

            0

        )

        return overlay

    # ======================================================
    # Save GradCAM
    # ======================================================

    def save(

            self,

            overlay,

            save_path

    ):
        """
        Saves Grad-CAM overlay.
        """

        save_path.parent.mkdir(

            parents=True,

            exist_ok=True

        )

        cv2.imwrite(

            str(save_path),

            overlay

        )

        print(

            f"Saved Grad-CAM -> {save_path}"

        )