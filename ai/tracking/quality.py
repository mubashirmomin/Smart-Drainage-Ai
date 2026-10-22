"""
ai/tracking/quality.py - CCTV Video Frame Quality Assessment Engine

Project: AI-Powered Underground Drainage Intelligence and Predictive Maintenance Platform
Purpose: Evaluates CCTV footage clarity in underground drainage pipes. Automatically detects
and flags poor-quality footage caused by:
1. Lens fogging / condensation / mud splatters (Laplacian variance blur metric)
2. Insufficient illumination / crawler headlight failure (underexposure)
3. Water surface glare / light saturation (overexposure)
4. Murky atmosphere / low contrast
"""

from typing import Dict, List, Tuple
import cv2
import numpy as np


class VideoQualityAssessor:
    """Evaluates optical quality of sewer inspection frames."""

    def __init__(
        self,
        blur_threshold: float = 60.0,
        low_light_threshold: float = 30.0,
        high_light_threshold: float = 225.0,
        low_contrast_threshold: float = 20.0,
    ):
        self.blur_threshold = blur_threshold
        self.low_light_threshold = low_light_threshold
        self.high_light_threshold = high_light_threshold
        self.low_contrast_threshold = low_contrast_threshold

    def evaluate_frame(self, frame: np.ndarray) -> Dict:
        """
        Analyze a single video frame and return diagnostic quality metrics.

        Returns:
            dict containing:
                is_poor_quality (bool): True if any critical quality degradation is detected.
                quality_score (float): Normalized score from 0.0 (unusable) to 1.0 (crystal clear).
                issues (List[str]): Explanations of why the frame is degraded.
                blur_metric (float): Variance of the Laplacian.
                brightness (float): Mean grayscale luminance.
                contrast (float): Standard deviation of grayscale pixel intensities.
        """
        if frame is None or frame.size == 0:
            return {
                "is_poor_quality": True,
                "quality_score": 0.0,
                "issues": ["EMPTY_FRAME"],
                "blur_metric": 0.0,
                "brightness": 0.0,
                "contrast": 0.0,
            }

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

        # 1. Blur Detection using Laplacian Variance: var(Laplacian(I))
        # Clear edges produce high variance; blurred/fogged scenes produce low variance.
        blur_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # 2. Lighting / Luminance
        mean_brightness = float(np.mean(gray))

        # 3. Dynamic Range & Contrast
        contrast_std = float(np.std(gray))

        issues: List[str] = []

        # Check conditions
        if blur_var < self.blur_threshold:
            issues.append(f"BLURRY_LENS_FOG (var={blur_var:.1f} < {self.blur_threshold})")

        if mean_brightness < self.low_light_threshold:
            issues.append(f"UNDEREXPOSED_DARK (lum={mean_brightness:.1f} < {self.low_light_threshold})")
        elif mean_brightness > self.high_light_threshold:
            issues.append(f"OVEREXPOSED_GLARE (lum={mean_brightness:.1f} > {self.high_light_threshold})")

        if contrast_std < self.low_contrast_threshold:
            issues.append(f"LOW_CONTRAST (std={contrast_std:.1f} < {self.low_contrast_threshold})")

        # Compute normalized quality score [0.0, 1.0]
        # Blur subscore: saturated sigmoid-like scaling
        blur_sub = min(1.0, blur_var / (self.blur_threshold * 2.5))
        # Brightness subscore: ideal center around 100-140
        bright_sub = 1.0 - abs(mean_brightness - 120.0) / 120.0
        bright_sub = max(0.0, min(1.0, bright_sub))
        # Contrast subscore
        contrast_sub = min(1.0, contrast_std / (self.low_contrast_threshold * 2.5))

        quality_score = round(0.45 * blur_sub + 0.35 * bright_sub + 0.20 * contrast_sub, 2)
        is_poor_quality = len(issues) > 0 or quality_score < 0.40

        return {
            "is_poor_quality": is_poor_quality,
            "quality_score": quality_score,
            "issues": issues,
            "blur_metric": round(blur_var, 2),
            "brightness": round(mean_brightness, 2),
            "contrast": round(contrast_std, 2),
        }
