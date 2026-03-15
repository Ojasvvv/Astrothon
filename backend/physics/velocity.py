"""
BOLIDE — Velocity and deceleration model fitting.

Hand-implemented using NumPy / SciPy.
- Linear deceleration: s = v₀t + ½at²
- Whipple-Jacchia exponential model: v = v∞·exp(−K·Σρ·Δs)
"""

from __future__ import annotations
import numpy as np
from scipy.optimize import curve_fit, minimize
from typing import Dict, Any, List

from backend.config import EARTH_RADIUS


# ── Atmospheric density profile (simplified NRLMSISE-00 approx.) ─────

def atmospheric_density(alt_km: float) -> float:
    """
    Approximate atmospheric density [kg/m³] as a function of altitude.
    Exponential scale-height model.
    """
    if alt_km < 0:
        return 1.225
    # Multi-layer exponential
    layers = [
        (0, 1.225, 8.5),
        (25, 3.899e-2, 6.5),
        (50, 1.027e-3, 7.0),
        (80, 1.846e-5, 5.5),
        (100, 5.604e-7, 6.0),
        (120, 2.222e-8, 10.0),
        (150, 2.076e-9, 22.0),
    ]
    for i in range(len(layers) - 1, -1, -1):
        h0, rho0, H = layers[i]
        if alt_km >= h0:
            return rho0 * np.exp(-(alt_km - h0) / H)
    return layers[0][1]


# ── Linear deceleration model ────────────────────────────────────────

def _linear_model(t, v0, a):
    """s = v₀t + ½at²"""
    return v0 * t + 0.5 * a * t ** 2


def _linear_velocity(t, v0, a):
    """v = v₀ + at (derivative of linear distance model)"""
    return v0 + a * t


# ── Whipple-Jacchia exponential ──────────────────────────────────────

def _wj_velocity(s_arr, v_inf, K, altitudes):
    """
    Whipple-Jacchia: v(s) = v_inf * exp(-K * integral(rho * ds))
    We compute the cumulative density integral along the track.
    """
    v = np.zeros_like(s_arr, dtype=np.float64)
    v[0] = v_inf
    for i in range(1, len(s_arr)):
        ds = s_arr[i] - s_arr[i - 1]
        rho = atmospheric_density(altitudes[i])
        v[i] = v[i - 1] * np.exp(-K * rho * abs(ds))
    return v


# ── Main velocity fitting ───────────────────────────────────────────

def fit_velocity(
    trajectory_points: List[Dict[str, Any]],
    trajectory_direction: np.ndarray,
    trajectory_start: np.ndarray,
) -> Dict[str, Any]:
    """
    Fit velocity models to the reconstructed trajectory.

    trajectory_points: sorted list of {eci, t_param, timestamp, frame_index, ...}
    Returns velocity profile, model parameters, and fit quality.
    """
    if len(trajectory_points) < 3:
        return _minimal_result(trajectory_points)

    # Extract timestamps and positions
    start_eci = np.array(trajectory_start)
    times = []
    distances = []
    altitudes = []

    t0 = trajectory_points[0]["timestamp"]
    for tp in trajectory_points:
        eci = np.array(tp["eci"])
        dist = np.linalg.norm(eci - start_eci) / 1000.0  # km
        alt = (np.linalg.norm(eci) - EARTH_RADIUS) / 1000.0  # km
        t = tp["timestamp"] - t0  # seconds
        times.append(t)
        distances.append(dist)
        altitudes.append(alt)

    times = np.array(times)
    distances = np.array(distances)
    altitudes = np.array(altitudes)

    # Remove duplicate/negative times
    mask = np.diff(times, prepend=-1) > 1e-6
    times = times[mask]
    distances = distances[mask]
    altitudes = altitudes[mask]

    if len(times) < 3:
        return _minimal_result(trajectory_points)

    # ── SUBSAMPLE to at most 40 representative points ──────────────────
    # This makes all fitting O(40) instead of O(800), 20× faster
    MAX_PTS = 40
    if len(times) > MAX_PTS:
        idx = np.round(np.linspace(0, len(times) - 1, MAX_PTS)).astype(int)
        idx = np.unique(idx)
        times = times[idx]
        distances = distances[idx]
        altitudes = altitudes[idx]

    # Maximum physical velocity for an Earth-bound meteor (km/s)
    MAX_V = 72.0

    # ── Fit linear deceleration model ──────────────────────────────────
    try:
        v0_guess = min(distances[-1] / max(times[-1], 1e-6), MAX_V)
        popt_lin, _ = curve_fit(
            _linear_model, times, distances,
            p0=[v0_guess, -2.0],
            bounds=([0, -200], [MAX_V, 0]),
            maxfev=2000,
        )
        v0_lin, a_lin = popt_lin
        dist_fit_lin = _linear_model(times, *popt_lin)
        residuals_lin = distances - dist_fit_lin
        chi2_lin = float(np.sum(residuals_lin ** 2) / max(len(times) - 2, 1))
    except Exception:
        v0_lin = min(float(distances[-1] / max(times[-1], 1e-6)), MAX_V)
        a_lin = -2.0
        chi2_lin = 999.0
        dist_fit_lin = _linear_model(times, v0_lin, a_lin)

    # ── Fit Whipple-Jacchia model ───────────────────────────────────────
    try:
        vel_obs = np.gradient(distances, times)
        vel_obs = np.clip(np.abs(vel_obs), 1.0, 200.0)

        distances_m = distances * 1000.0

        def wj_cost(params):
            v_inf, K = params
            if v_inf <= 0 or K <= 0:
                return 1e12
            v_pred = _wj_velocity(distances_m, v_inf * 1000.0, K, altitudes)
            return float(np.sum((v_pred / 1000.0 - vel_obs) ** 2))

        result_wj = minimize(
            wj_cost,
            [abs(v0_lin), 5e-5],
            method='Nelder-Mead',
            options={"maxiter": 200, "xatol": 0.05, "fatol": 0.01},
        )
        v_inf_wj, K_wj = result_wj.x
        v_inf_wj = min(abs(v_inf_wj), MAX_V)
        K_wj = abs(K_wj)
        v_pred_wj = _wj_velocity(distances_m, v_inf_wj * 1000.0, K_wj, altitudes) / 1000.0
        chi2_wj = float(np.sum((v_pred_wj - vel_obs) ** 2) / max(len(times) - 2, 1))
    except Exception:
        v_inf_wj = abs(v0_lin)
        K_wj = 0.0
        vel_obs = np.gradient(distances, times)
        vel_obs = np.clip(np.abs(vel_obs), 0.0, 200.0)
        v_pred_wj = vel_obs.copy()
        chi2_wj = 999.0

    # ── Compute velocity profile arrays for plotting ──
    velocity_linear = _linear_velocity(times, v0_lin, a_lin)
    velocity_observed = np.clip(np.abs(np.gradient(distances, times)), 0.0, 200.0)

    return {
        "initial_velocity_kms": abs(float(v0_lin)),
        "deceleration_kms2": float(a_lin),
        "entry_angle_deg": None,  # set by triangulation
        "linear_model": {
            "v0": abs(float(v0_lin)),
            "a": float(a_lin),
            "chi_squared": chi2_lin,
        },
        "whipple_jacchia_model": {
            "v_inf": float(v_inf_wj),
            "K": float(K_wj),
            "chi_squared": chi2_wj,
        },
        "velocity_profile": {
            "times": times.tolist(),
            "distances_km": distances.tolist(),
            "altitudes_km": altitudes.tolist(),
            "velocity_observed_kms": velocity_observed.tolist(),
            "velocity_linear_kms": velocity_linear.tolist(),
            "velocity_wj_kms": v_pred_wj.tolist(),
            "distance_fit_linear_km": dist_fit_lin.tolist(),
        },
    }



def _minimal_result(points):
    """Fallback for insufficient data."""
    return {
        "initial_velocity_kms": 30.0,
        "deceleration_kms2": -1.0,
        "entry_angle_deg": None,
        "linear_model": {"v0": 30.0, "a": -1.0, "chi_squared": 999.0},
        "whipple_jacchia_model": {"v_inf": 30.0, "K": 0.0, "chi_squared": 999.0},
        "velocity_profile": {
            "times": [], "distances_km": [], "altitudes_km": [],
            "velocity_observed_kms": [], "velocity_linear_kms": [],
            "velocity_wj_kms": [], "distance_fit_linear_km": [],
        },
    }
