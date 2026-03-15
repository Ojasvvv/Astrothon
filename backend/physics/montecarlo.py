"""
BOLIDE — Monte Carlo uncertainty estimation.

Perturb RA/Dec by Gaussian noise, re-run full pipeline, collect statistics.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Any, List
import copy

from backend.config import MC_ITERATIONS, MC_SIGMA_ARCSEC
from backend.physics.triangulation import triangulate_trajectory
from backend.physics.velocity import fit_velocity
from backend.physics.orbit import compute_orbital_elements
from backend.physics.coordinates import unit_to_ra_dec, ecef_to_geodetic


def run_monte_carlo(
    stations: List[Dict[str, Any]],
    observations: List[Dict[str, Any]],
    jd: float,
    n_iterations: int = MC_ITERATIONS,
    sigma_arcsec: float = MC_SIGMA_ARCSEC,
) -> Dict[str, Any]:
    """
    Monte Carlo uncertainty estimation.

    1. Perturb each RA/Dec observation by Gaussian noise (σ = sigma_arcsec)
    2. Re-run triangulation → velocity → orbit
    3. Collect distributions for radiant, velocity, orbital elements

    Returns statistics: means, σ, confidence intervals.
    """
    sigma_deg = sigma_arcsec / 3600.0

    results = {
        "radiant_ra": [],
        "radiant_dec": [],
        "initial_velocity": [],
        "entry_altitude": [],
        "terminal_altitude": [],
        "semi_major_axis": [],
        "eccentricity": [],
        "inclination": [],
        "perihelion_distance": [],
        "entry_angle": [],
    }

    n_success = 0

    for i in range(n_iterations):
        # Perturb observations
        perturbed_obs = []
        for obs in observations:
            pobs = dict(obs)
            pobs["ra"] = obs["ra"] + np.random.normal(0, sigma_deg)
            pobs["dec"] = obs["dec"] + np.random.normal(0, sigma_deg)
            perturbed_obs.append(pobs)

        try:
            # Triangulate
            traj = triangulate_trajectory(stations, perturbed_obs, jd)

            # Velocity fit
            vel = fit_velocity(
                traj["trajectory_points"],
                np.array(traj["trajectory_direction"]),
                np.array(traj["trajectory_start"]),
            )

            # Radiant direction
            direction = np.array(traj["trajectory_direction"])
            radiant = -direction  # meteor comes FROM radiant
            ra_rad, dec_rad = unit_to_ra_dec(radiant)

            results["radiant_ra"].append(ra_rad)
            results["radiant_dec"].append(dec_rad)
            results["initial_velocity"].append(vel["initial_velocity_kms"])
            results["entry_altitude"].append(traj["entry_altitude_km"])
            results["terminal_altitude"].append(traj["terminal_altitude_km"])
            results["entry_angle"].append(traj["entry_angle_deg"])

            # Orbital elements
            entry_eci = np.array(traj["trajectory_start"])
            from backend.physics.coordinates import eci_to_ecef, greenwich_mean_sidereal_time
            gmst = greenwich_mean_sidereal_time(jd)
            entry_ecef = eci_to_ecef(entry_eci, gmst)
            entry_lat, entry_lon, entry_alt = ecef_to_geodetic(entry_ecef)

            orb = compute_orbital_elements(
                ra_rad, dec_rad, vel["initial_velocity_kms"],
                entry_lat, entry_lon, traj["entry_altitude_km"],
                jd, apply_corrections=True,
            )

            results["semi_major_axis"].append(orb["semi_major_axis_au"])
            results["eccentricity"].append(orb["eccentricity"])
            results["inclination"].append(orb["inclination_deg"])
            results["perihelion_distance"].append(orb["perihelion_distance_au"])

            n_success += 1

        except Exception:
            continue

    if n_success < 3:
        return {"error": "Insufficient successful MC iterations", "n_success": n_success}

    # Compute statistics
    stats = {}
    for key, values in results.items():
        if len(values) == 0:
            continue
        arr = np.array(values)
        stats[key] = {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "median": float(np.median(arr)),
            "ci_lower": float(np.percentile(arr, 15.87)),  # -1σ
            "ci_upper": float(np.percentile(arr, 84.13)),  # +1σ
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
        }

    # Radiant uncertainty ellipse
    if len(results["radiant_ra"]) > 2 and len(results["radiant_dec"]) > 2:
        ra_arr = np.array(results["radiant_ra"])
        dec_arr = np.array(results["radiant_dec"])
        cov = np.cov(ra_arr, dec_arr)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        # Semi-axes of 1σ ellipse
        stats["radiant_ellipse"] = {
            "semi_major_deg": float(np.sqrt(max(eigenvalues))),
            "semi_minor_deg": float(np.sqrt(max(min(eigenvalues), 0))),
            "angle_deg": float(np.degrees(np.arctan2(eigenvectors[1, 1], eigenvectors[0, 1]))),
            "center_ra": float(np.mean(ra_arr)),
            "center_dec": float(np.mean(dec_arr)),
        }

    stats["n_iterations"] = n_iterations
    stats["n_success"] = n_success
    stats["convergence_ratio"] = n_success / n_iterations

    return stats
