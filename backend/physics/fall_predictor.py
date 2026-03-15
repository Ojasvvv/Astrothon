"""
BOLIDE — Meteorite fall predictor (stretch feature).

If terminal velocity < ~5 km/s → potential meteorite survival.
Estimates ground impact point and strewn-field ellipse.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Any, Optional

from backend.config import EARTH_RADIUS
from backend.physics.coordinates import ecef_to_geodetic
from backend.physics.velocity import atmospheric_density


def predict_fall(
    trajectory_end_eci: np.ndarray,
    trajectory_direction: np.ndarray,
    terminal_velocity_kms: float,
    terminal_altitude_km: float,
    entry_angle_deg: float,
) -> Optional[Dict[str, Any]]:
    """
    Predict meteorite fall location and strewn field.

    Returns None if terminal velocity is too high for survival.
    """
    if terminal_velocity_kms > 5.0:
        return None

    # Below ~5 km/s, atmospheric drag dominates; meteoroid enters dark flight
    # Approximate dark-flight trajectory using ballistic descent

    v_term = terminal_velocity_kms * 1000.0  # m/s
    alt = terminal_altitude_km * 1000.0  # m
    angle = entry_angle_deg * np.pi / 180.0

    # Normalise trajectory direction
    d = trajectory_direction / np.linalg.norm(trajectory_direction)

    # Dark flight: simple ballistic model
    # dt steps until altitude reaches 0
    pos = trajectory_end_eci.copy()
    vel = d * v_term

    dt = 0.5  # seconds
    points = [pos.copy()]

    for _ in range(10000):
        alt_m = np.linalg.norm(pos) - EARTH_RADIUS
        if alt_m <= 0:
            break

        # Gravity (radial inward)
        g_dir = -pos / np.linalg.norm(pos)
        g = 9.81 * g_dir

        # Drag
        rho = atmospheric_density(alt_m / 1000.0)
        v_mag = np.linalg.norm(vel)
        if v_mag < 0.1:
            break
        Cd = 1.2  # drag coefficient for tumbling body
        A = 0.01  # effective cross-section m² (assumed)
        m = 0.5   # mass kg (assumed)
        drag_acc = -0.5 * rho * Cd * A * v_mag * vel / m

        vel = vel + (g + drag_acc) * dt
        pos = pos + vel * dt
        points.append(pos.copy())

    # Final impact point
    impact_ecef = pos
    lat, lon, _ = ecef_to_geodetic(impact_ecef)

    # Strewn field ellipse estimation
    # Length along trajectory direction, width perpendicular
    # Larger mass fragments land further (closer to end of bright path)
    # Lighter fragments decelerate more → land earlier

    # Simplified: ellipse semi-axes based on altitude and wind uncertainty
    wind_spread_km = terminal_altitude_km * 0.3  # rough estimate
    flight_spread_km = terminal_altitude_km * 0.5

    return {
        "impact_latitude": float(lat),
        "impact_longitude": float(lon),
        "strewn_field": {
            "center_lat": float(lat),
            "center_lon": float(lon),
            "semi_major_km": float(flight_spread_km),
            "semi_minor_km": float(wind_spread_km),
            "orientation_deg": float(np.degrees(np.arctan2(d[1], d[0]))),
        },
        "terminal_velocity_kms": terminal_velocity_kms,
        "dark_flight_duration_s": len(points) * dt,
        "survival_probability": "High" if terminal_velocity_kms < 3 else "Moderate",
    }
