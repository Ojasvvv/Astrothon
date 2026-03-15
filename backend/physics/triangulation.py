"""
BOLIDE — 3-D trajectory triangulation.

Line-of-Sight (LoS) least-squares method with SVD.
Hand-implemented using NumPy — NO black-box trajectory solvers.
"""

from __future__ import annotations
import numpy as np
from typing import List, Tuple, Dict, Any

from backend.physics.coordinates import (
    geodetic_to_ecef, ra_dec_to_unit, greenwich_mean_sidereal_time,
    ecef_to_eci, observation_direction_eci, angular_separation,
    unit_to_ra_dec, jd_from_timestamp,
)
from backend.config import OUTLIER_SIGMA, EARTH_RADIUS


# ── Core line-of-sight solver ─────────────────────────────────────────

def _closest_point_on_line(P: np.ndarray, d: np.ndarray,
                            Q: np.ndarray) -> Tuple[np.ndarray, float]:
    """Project point Q onto ray P + t*d, return (closest_point, t)."""
    t = np.dot(Q - P, d) / np.dot(d, d)
    return P + t * d, t


def los_triangulate(
    station_positions: List[np.ndarray],
    direction_vectors: List[np.ndarray],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Line-of-Sight least-squares: find the 3-D line that minimises total
    squared perpendicular distance to all observation rays.

    Each ray: r_i = station_i + t_i * dir_i

    Returns (point_on_line, line_direction) both in ECI.

    Method: form normal equations using the cross-product approach.
    For every ray pair we find the mutual perpendicular.  Then we
    formulate an overdetermined least-squares system and solve via SVD.
    """
    n = len(station_positions)
    if n < 2:
        raise ValueError("Need at least 2 observation rays for triangulation")

    S = np.array(station_positions)  # (n, 3)
    D = np.array(direction_vectors)  # (n, 3)
    # Normalise directions
    D = D / np.linalg.norm(D, axis=1, keepdims=True)

    # Build the linear system  A x = b
    # For each ray i: the point X on the trajectory satisfies
    #   (I - d_i d_i^T) X = (I - d_i d_i^T) s_i
    # Stack all equations
    A_blocks = []
    b_blocks = []
    for i in range(n):
        d = D[i]
        M = np.eye(3) - np.outer(d, d)   # projection matrix
        A_blocks.append(M)
        b_blocks.append(M @ S[i])

    A = np.vstack(A_blocks)  # (3n, 3)
    b = np.concatenate(b_blocks)  # (3n,)

    # Solve via SVD (least squares)
    point, residual_norm, rank, sv = np.linalg.lstsq(A, b, rcond=None)

    # Now find the trajectory *direction*:
    # Project all station rays onto the neighbourhood of `point` and
    # find the principal direction of closest-approach points.
    closest_pts = []
    for i in range(n):
        cp, _ = _closest_point_on_line(S[i], D[i], point)
        closest_pts.append(cp)
    closest_pts = np.array(closest_pts)

    if n >= 2:
        centroid = closest_pts.mean(axis=0)
        _, _, Vt = np.linalg.svd(closest_pts - centroid)
        direction = Vt[0]  # first principal component
    else:
        direction = D[0]

    return point, direction


# ── Multi-point trajectory fit ────────────────────────────────────────

def triangulate_trajectory(
    stations: List[Dict[str, Any]],
    observations: List[Dict[str, Any]],
    jd: float,
) -> Dict[str, Any]:
    """
    Full multi-station triangulation pipeline.

    stations: list of {station_id, latitude, longitude, elevation}
    observations: list of {station_id, timestamp, ra, dec, frame_index, brightness}
    jd: Julian date of the event

    Returns dict with trajectory parameters, residuals, quality metrics.
    """
    gmst = greenwich_mean_sidereal_time(jd)

    # Build station lookup
    station_map = {}
    for st in stations:
        ecef = geodetic_to_ecef(st["latitude"], st["longitude"], st["elevation"])
        eci = ecef_to_eci(ecef, gmst)
        station_map[st["station_id"]] = {
            "ecef": ecef,
            "eci": eci,
            "lat": st["latitude"],
            "lon": st["longitude"],
            "alt": st["elevation"],
        }

    # Group observations by station
    obs_by_station = {}
    for obs in observations:
        sid = obs["station_id"]
        if sid not in obs_by_station:
            obs_by_station[sid] = []
        obs_by_station[sid].append(obs)

    # Sort each station's observations by frame_index
    for sid in obs_by_station:
        obs_by_station[sid].sort(key=lambda o: o["frame_index"])

    # Collect ALL observation rays
    all_positions = []
    all_directions = []
    all_obs_meta = []

    for sid, obs_list in obs_by_station.items():
        if sid not in station_map:
            continue
        st = station_map[sid]
        for obs in obs_list:
            d = ra_dec_to_unit(obs["ra"], obs["dec"])
            all_positions.append(st["eci"])
            all_directions.append(d)
            all_obs_meta.append({"station_id": sid, **obs})

    if len(all_positions) < 2:
        raise ValueError(f"Insufficient observations for triangulation: {len(all_positions)}")

    # ── Initial triangulation ──
    point, direction = los_triangulate(all_positions, all_directions)

    # ── Compute per-observation residuals ──
    residuals = _compute_residuals(point, direction, all_positions, all_directions)

    # ── RANSAC outlier rejection ──
    inlier_mask = _reject_outliers(residuals, sigma=OUTLIER_SIGMA)

    if np.sum(inlier_mask) >= 2:
        inlier_pos = [p for p, m in zip(all_positions, inlier_mask) if m]
        inlier_dir = [d for d, m in zip(all_directions, inlier_mask) if m]
        point, direction = los_triangulate(inlier_pos, inlier_dir)
        residuals = _compute_residuals(point, direction, all_positions, all_directions)

    # ── Project observations onto trajectory line → 3-D points ──
    trajectory_points = []
    for pos, d_vec, meta in zip(all_positions, all_directions, all_obs_meta):
        cp, t = _closest_point_on_line(point, direction, pos + 1e6 * d_vec)
        trajectory_points.append({
            "eci": cp.tolist(),
            "t_param": t,
            "station_id": meta["station_id"],
            "frame_index": meta["frame_index"],
            "timestamp": meta["timestamp"],
        })

    # Sort by t_param (distance along track)
    trajectory_points.sort(key=lambda x: x["t_param"])

    # ── Entry & terminal points ──
    entry_eci = np.array(trajectory_points[0]["eci"])
    terminal_eci = np.array(trajectory_points[-1]["eci"])

    entry_alt = np.linalg.norm(entry_eci) - EARTH_RADIUS
    terminal_alt = np.linalg.norm(terminal_eci) - EARTH_RADIUS
    trajectory_length = np.linalg.norm(entry_eci - terminal_eci)

    # Ensure entry is higher altitude
    if entry_alt < terminal_alt:
        direction = -direction
        entry_eci, terminal_eci = terminal_eci, entry_eci
        entry_alt, terminal_alt = terminal_alt, entry_alt
        trajectory_points.reverse()

    # ── Station convergence angle Q ──
    Q_angle = _convergence_angle(obs_by_station, station_map)

    # ── Per-station residual statistics ──
    station_residuals = {}
    for res, meta, mask in zip(residuals, all_obs_meta, inlier_mask):
        sid = meta["station_id"]
        if sid not in station_residuals:
            station_residuals[sid] = {"residuals": [], "frames": 0, "is_outlier": False}
        station_residuals[sid]["residuals"].append(res)
        station_residuals[sid]["frames"] += 1
    for sid in station_residuals:
        r = station_residuals[sid]["residuals"]
        station_residuals[sid]["mean_residual"] = float(np.mean(r))
        station_residuals[sid]["rms_residual"] = float(np.sqrt(np.mean(np.array(r)**2)))

    # Compute entry angle (angle between trajectory direction and local vertical)
    local_vertical = entry_eci / np.linalg.norm(entry_eci)
    cos_entry = abs(np.dot(direction / np.linalg.norm(direction), local_vertical))
    entry_angle = np.degrees(np.arccos(np.clip(cos_entry, 0, 1)))

    return {
        "trajectory_start": entry_eci.tolist(),
        "trajectory_end": terminal_eci.tolist(),
        "trajectory_direction": (direction / np.linalg.norm(direction)).tolist(),
        "trajectory_points": trajectory_points,
        "entry_altitude_km": entry_alt / 1000.0,
        "terminal_altitude_km": terminal_alt / 1000.0,
        "trajectory_length_km": trajectory_length / 1000.0,
        "entry_angle_deg": entry_angle,
        "convergence_angle_Q": Q_angle,
        "median_residual_arcsec": float(np.median(residuals)),
        "rms_residual_arcsec": float(np.sqrt(np.mean(np.array(residuals)**2))),
        "station_residuals": station_residuals,
        "outlier_mask": inlier_mask.tolist(),
        "num_observations": len(all_positions),
        "num_inliers": int(np.sum(inlier_mask)),
    }


# ── Residuals ─────────────────────────────────────────────────────────

def _compute_residuals(
    point: np.ndarray, direction: np.ndarray,
    positions: List[np.ndarray], directions: List[np.ndarray],
) -> List[float]:
    """Compute angular residuals in arcseconds for each observation."""
    direction_norm = direction / np.linalg.norm(direction)
    residuals = []
    for pos, obs_dir in zip(positions, directions):
        obs_dir_norm = obs_dir / np.linalg.norm(obs_dir)
        # Closest point on trajectory line to this ray
        # Line: point + s * direction_norm
        # Ray: pos + t * obs_dir_norm
        # Find s that gives the closest point on the line to the ray
        w = pos - point
        a = np.dot(direction_norm, direction_norm)
        b = np.dot(direction_norm, obs_dir_norm)
        c_val = np.dot(obs_dir_norm, obs_dir_norm)
        d_val = np.dot(direction_norm, w)
        e = np.dot(obs_dir_norm, w)
        denom = a * c_val - b * b
        if abs(denom) < 1e-15:
            residuals.append(0.0)
            continue
        s = (b * e - c_val * d_val) / denom
        traj_point = point + s * direction_norm

        # Direction from station to traj_point
        expected_dir = traj_point - pos
        expected_dir = expected_dir / np.linalg.norm(expected_dir)

        # Angular separation
        cos_angle = np.clip(np.dot(obs_dir_norm, expected_dir), -1, 1)
        angle_rad = np.arccos(cos_angle)
        residuals.append(np.degrees(angle_rad) * 3600)  # arcseconds

    return residuals


def _reject_outliers(residuals: List[float], sigma: float = 3.0) -> np.ndarray:
    """Sigma-clipping outlier rejection. Returns boolean mask (True = inlier)."""
    r = np.array(residuals)
    median = np.median(r)
    mad = np.median(np.abs(r - median))
    if mad < 1e-10:
        mad = np.std(r)
    threshold = median + sigma * mad * 1.4826
    return r <= threshold


def _convergence_angle(obs_by_station, station_map) -> float:
    """
    Convergence quality angle Q: angle between the two best-separated
    station sight-line planes.
    """
    station_ids = [sid for sid in obs_by_station if sid in station_map]
    if len(station_ids) < 2:
        return 0.0

    # Compute mean sight direction per station
    mean_dirs = {}
    for sid in station_ids:
        directions = []
        for obs in obs_by_station[sid]:
            d = ra_dec_to_unit(obs["ra"], obs["dec"])
            directions.append(d)
        mean_dirs[sid] = np.mean(directions, axis=0)
        mean_dirs[sid] /= np.linalg.norm(mean_dirs[sid])

    # Find maximum angular separation between station mean directions
    max_angle = 0.0
    sids_list = list(mean_dirs.keys())
    for i in range(len(sids_list)):
        for j in range(i + 1, len(sids_list)):
            s1 = station_map[sids_list[i]]["eci"]
            s2 = station_map[sids_list[j]]["eci"]
            baseline = s2 - s1
            baseline_norm = baseline / np.linalg.norm(baseline)

            # Q ≈ angle subtended by baseline as seen from mean trajectory point
            d1 = mean_dirs[sids_list[i]]
            d2 = mean_dirs[sids_list[j]]
            cos_a = np.clip(np.dot(d1, d2), -1, 1)
            angle = np.degrees(np.arccos(cos_a))
            if angle > max_angle:
                max_angle = angle

    return max_angle
