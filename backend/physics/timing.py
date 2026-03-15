"""
BOLIDE — Inter-station timing offset estimation.

Treats each station clock offset Δt_i as a free parameter.
Joint optimisation with velocity fitting via scipy.optimize.minimize.
"""

from __future__ import annotations
import numpy as np
from scipy.optimize import minimize
from typing import Dict, Any, List


def estimate_timing_offsets(
    trajectory_points: List[Dict[str, Any]],
    station_ids: List[str],
) -> Dict[str, float]:
    """
    Estimate per-station clock offsets by minimising the scatter in
    the distance-along-track vs. corrected-time relationship.

    Station 0 is anchored at Δt = 0.

    Returns dict {station_id: offset_ms}.
    """
    if len(station_ids) < 2 or len(trajectory_points) < 4:
        return {sid: 0.0 for sid in station_ids}

    anchor = station_ids[0]
    free_stations = station_ids[1:]

    # Extract data per point
    raw_times = []
    distances = []
    point_stations = []

    p0 = np.array(trajectory_points[0]["eci"])
    for tp in trajectory_points:
        raw_times.append(tp["timestamp"])
        d = np.linalg.norm(np.array(tp["eci"]) - p0) / 1000.0  # km
        distances.append(d)
        point_stations.append(tp["station_id"])

    raw_times = np.array(raw_times)
    distances = np.array(distances)

    # Station index mapping
    sid_to_idx = {sid: i for i, sid in enumerate(free_stations)}

    def cost(offsets_ms):
        """
        Apply offsets, sort by corrected time, then measure how well
        a linear model fits (velocity should decrease monotonically).
        """
        corrected = raw_times.copy()
        for i, t in enumerate(corrected):
            sid = point_stations[i]
            if sid in sid_to_idx:
                corrected[i] += offsets_ms[sid_to_idx[sid]] / 1000.0

        order = np.argsort(corrected)
        t_sorted = corrected[order]
        d_sorted = distances[order]

        dt = np.diff(t_sorted)
        if np.any(dt <= 0):
            return 1e8

        # Fit linear velocity model, return residual sum
        if len(t_sorted) < 2:
            return 1e8
        t_rel = t_sorted - t_sorted[0]
        try:
            coeffs = np.polyfit(t_rel, d_sorted, 2)
            d_fit = np.polyval(coeffs, t_rel)
            return np.sum((d_sorted - d_fit) ** 2)
        except Exception:
            return 1e8

    # Initial guess: all offsets = 0
    x0 = np.zeros(len(free_stations))
    bounds = [(-50.0, 50.0)] * len(free_stations)  # ±50 ms

    result = minimize(cost, x0, method='L-BFGS-B', bounds=bounds,
                      options={"maxiter": 500})

    offsets = {anchor: 0.0}
    for i, sid in enumerate(free_stations):
        offsets[sid] = float(result.x[i])

    return offsets


def apply_timing_offsets(
    trajectory_points: List[Dict[str, Any]],
    offsets_ms: Dict[str, float],
) -> List[Dict[str, Any]]:
    """Apply estimated clock offsets to trajectory point timestamps."""
    corrected = []
    for tp in trajectory_points:
        tp_copy = dict(tp)
        sid = tp["station_id"]
        if sid in offsets_ms:
            tp_copy["timestamp"] = tp["timestamp"] + offsets_ms[sid] / 1000.0
        corrected.append(tp_copy)
    corrected.sort(key=lambda x: x["timestamp"])
    return corrected
