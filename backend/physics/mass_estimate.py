"""
BOLIDE — Light-curve mass estimation (stretch feature).

Uses the luminous efficiency relation to estimate initial meteoroid mass
from the magnitude time series.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Any, List


def estimate_mass(
    magnitudes: List[float],
    timestamps: List[float],
    velocity_kms: float,
) -> Dict[str, Any]:
    """
    Estimate initial meteoroid mass from brightness data.

    Method:
      1. Convert magnitudes to luminous power
      2. Integrate total radiated energy
      3. Apply luminous efficiency τ = 0.042 · v^0.2 (Ceplecha 1988)
      4. E_kinetic = E_luminous / τ → mass = 2·E_kinetic / v²

    Parameters
    ----------
    magnitudes : apparent visual magnitudes (more negative = brighter)
    timestamps : observation times in seconds
    velocity_kms : initial velocity in km/s

    Returns dict with mass estimate and uncertainty.
    """
    if len(magnitudes) < 2 or len(timestamps) < 2:
        return {"mass_kg": None, "error": "Insufficient data"}

    mags = np.array(magnitudes, dtype=np.float64)
    times = np.array(timestamps, dtype=np.float64)

    # Reference: magnitude 0 star luminous power ≈ 1500 W (at meteor distance)
    P_ref = 1500.0  # Watts for mag 0

    # Luminous power from magnitudes
    powers = P_ref * 10.0 ** (-0.4 * mags)  # Pogson

    # Integrate luminous energy (trapezoidal)
    dt = np.diff(times)
    E_luminous = np.sum(0.5 * (powers[:-1] + powers[1:]) * dt)  # Joules

    # Luminous efficiency (Ceplecha 1988)
    v = velocity_kms  # km/s
    tau = 0.042 * (v ** 0.2)  # fraction
    tau = np.clip(tau, 0.001, 0.5)  # physical bounds

    # Kinetic energy
    E_kinetic = E_luminous / tau

    # Mass from kinetic energy: E = 0.5 * m * v²
    v_ms = velocity_kms * 1000.0
    mass_kg = 2.0 * E_kinetic / (v_ms ** 2)

    # Uncertainty estimate (factor ~3 due to τ uncertainty)
    mass_lower = mass_kg / 3.0
    mass_upper = mass_kg * 3.0

    # Peak brightness
    peak_mag = float(np.min(mags))
    peak_power = float(P_ref * 10.0 ** (-0.4 * peak_mag))

    return {
        "mass_kg": float(mass_kg),
        "mass_grams": float(mass_kg * 1000),
        "mass_range_kg": [float(mass_lower), float(mass_upper)],
        "luminous_energy_J": float(E_luminous),
        "kinetic_energy_J": float(E_kinetic),
        "luminous_efficiency": float(tau),
        "peak_magnitude": peak_mag,
        "peak_power_W": peak_power,
        "duration_s": float(times[-1] - times[0]),
    }
