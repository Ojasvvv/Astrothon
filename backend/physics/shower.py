"""
BOLIDE — Meteor shower matching against the IAU catalogue.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Any, List, Optional

from backend.config import SHOWER_MAX_SEPARATION_DEG, SHOWER_VELOCITY_TOLERANCE
from backend.physics.coordinates import angular_separation

from backend.config import REFERENCE_DIR
import json

def load_iau_showers() -> List[Dict[str, Any]]:
    path = REFERENCE_DIR / "iau_showers.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# ── IAU Shower Catalogue ──────────
IAU_SHOWERS = load_iau_showers()


def solar_longitude(jd: float) -> float:
    """Approximate solar longitude in degrees for a given JD."""
    T = (jd - 2451545.0) / 36525.0
    L = (280.46646 + 36000.76983 * T) % 360.0
    return L


def match_shower(
    radiant_ra: float,
    radiant_dec: float,
    v_geo_kms: float,
    jd: float,
    max_sep_deg: float = SHOWER_MAX_SEPARATION_DEG,
) -> Optional[Dict[str, Any]]:
    """
    Match a reconstructed radiant against the IAU shower catalogue.

    Returns best match or None.
    """
    sol_lon = solar_longitude(jd)

    best_match = None
    best_score = float("inf")

    for shower in IAU_SHOWERS:
        # Angular separation
        sep = angular_separation(radiant_ra, radiant_dec, shower["ra"], shower["dec"])

        # Velocity check
        v_ratio = abs(v_geo_kms - shower["v_g"]) / shower["v_g"]

        # Date check (solar longitude)
        in_window = shower["start_sol"] <= sol_lon <= shower["end_sol"]
        if shower["start_sol"] > shower["end_sol"]:
            in_window = sol_lon >= shower["start_sol"] or sol_lon <= shower["end_sol"]

        # Score: combine angular sep and velocity ratio
        if sep > max_sep_deg * 2:
            continue

        score = sep + v_ratio * 10.0
        if not in_window:
            score += 20.0  # penalty for out of activity window

        if score < best_score:
            best_score = score
            confidence = max(0.0, 1.0 - sep / max_sep_deg) * max(0.0, 1.0 - v_ratio / SHOWER_VELOCITY_TOLERANCE)
            if not in_window:
                confidence *= 0.3

            best_match = {
                "shower_code": shower["code"],
                "shower_name": shower["name"],
                "separation_deg": float(sep),
                "velocity_reference_kms": shower["v_g"],
                "radiant_ra_reference": shower["ra"],
                "radiant_dec_reference": shower["dec"],
                "in_activity_window": in_window,
                "confidence": float(np.clip(confidence * 100, 0, 100)),
            }

    return best_match
