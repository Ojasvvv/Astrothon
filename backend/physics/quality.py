"""
BOLIDE — Scientific quality scoring for reconstructed events.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Any


def compute_quality_score(
    rms_residual_arcsec: float,
    convergence_angle_Q: float,
    velocity_chi2: float,
    mc_convergence_ratio: float,
    outlier_ratio: float,
) -> Dict[str, Any]:
    """
    Compute composite quality score (0–100).

    Weights:
      - Astrometric RMS: 30%
      - Convergence angle Q: 20%
      - Velocity χ²: 20%
      - MC convergence: 15%
      - Outlier ratio: 15%
    """

    # Astrometric RMS score (30%)
    # Excellent < 3", Good < 10", Fair < 30"
    if rms_residual_arcsec < 1:
        rms_score = 100
    elif rms_residual_arcsec < 3:
        rms_score = 90 + 10 * (3 - rms_residual_arcsec) / 2
    elif rms_residual_arcsec < 10:
        rms_score = 70 + 20 * (10 - rms_residual_arcsec) / 7
    elif rms_residual_arcsec < 30:
        rms_score = 40 + 30 * (30 - rms_residual_arcsec) / 20
    else:
        rms_score = max(0, 40 - (rms_residual_arcsec - 30))

    # Convergence angle Q score (20%)
    # Q > 20° is good, > 60° is excellent
    if convergence_angle_Q > 90:
        q_score = 100
    elif convergence_angle_Q > 60:
        q_score = 85 + 15 * (convergence_angle_Q - 60) / 30
    elif convergence_angle_Q > 20:
        q_score = 50 + 35 * (convergence_angle_Q - 20) / 40
    elif convergence_angle_Q > 5:
        q_score = 20 + 30 * (convergence_angle_Q - 5) / 15
    else:
        q_score = convergence_angle_Q * 4

    # Velocity χ² score (20%)
    # χ² ~ 1 is ideal
    if velocity_chi2 < 0.5:
        chi_score = 85
    elif velocity_chi2 < 1.5:
        chi_score = 100 - 15 * abs(velocity_chi2 - 1.0)
    elif velocity_chi2 < 3.0:
        chi_score = 70 - 20 * (velocity_chi2 - 1.5) / 1.5
    elif velocity_chi2 < 10:
        chi_score = 50 - 30 * (velocity_chi2 - 3) / 7
    else:
        chi_score = max(0, 20 - velocity_chi2)

    # MC convergence score (15%)
    mc_score = mc_convergence_ratio * 100

    # Outlier ratio score (15%)
    # Lower is better: 0 outliers = 100, 50% = 0
    outlier_score = max(0, 100 * (1 - 2 * outlier_ratio))

    # Composite
    composite = (
        0.30 * rms_score
        + 0.20 * q_score
        + 0.20 * chi_score
        + 0.15 * mc_score
        + 0.15 * outlier_score
    )
    composite = np.clip(composite, 0, 100)

    if composite >= 85:
        label = "Excellent"
    elif composite >= 70:
        label = "Good"
    elif composite >= 50:
        label = "Fair"
    else:
        label = "Poor"

    return {
        "composite_score": round(float(composite)),
        "label": label,
        "breakdown": {
            "astrometric_rms": {"score": round(rms_score, 1), "weight": 0.30, "value": rms_residual_arcsec},
            "convergence_angle": {"score": round(q_score, 1), "weight": 0.20, "value": convergence_angle_Q},
            "velocity_chi2": {"score": round(chi_score, 1), "weight": 0.20, "value": velocity_chi2},
            "mc_convergence": {"score": round(mc_score, 1), "weight": 0.15, "value": mc_convergence_ratio},
            "outlier_ratio": {"score": round(outlier_score, 1), "weight": 0.15, "value": outlier_ratio},
        },
    }
