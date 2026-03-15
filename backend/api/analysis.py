"""
BOLIDE — Analysis API endpoints: reconstruction, trajectory, orbit, Monte Carlo.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import numpy as np
import logging

from backend.data.store import get_event, save_trajectory_cache, get_trajectory_cache
from backend.physics.triangulation import triangulate_trajectory
from backend.physics.velocity import fit_velocity
from backend.physics.timing import estimate_timing_offsets, apply_timing_offsets
from backend.physics.orbit import compute_orbital_elements
from backend.physics.montecarlo import run_monte_carlo
from backend.physics.shower import match_shower
from backend.physics.quality import compute_quality_score
from backend.physics.coordinates import (
    unit_to_ra_dec, greenwich_mean_sidereal_time, eci_to_ecef,
    ecef_to_geodetic, jd_from_timestamp,
)
from backend.physics.fall_predictor import predict_fall
from backend.physics.mass_estimate import estimate_mass

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analysis"])


def _run_reconstruction(event_data: dict) -> dict:
    """Run the full reconstruction pipeline on an event."""
    metadata = event_data["metadata"]
    stations = event_data["stations"]
    observations = event_data["observations"]

    event_time = metadata.get("unix_timestamp", 1700000000)
    jd = jd_from_timestamp(event_time)

    errors: list[str] = []

    # Initialize variables with safe defaults
    traj = {}
    offsets = {}
    corrected_points = []
    # Initialize variables with safe defaults
    vel_km_s = metadata.get("estimated_velocity_kms") or metadata.get("velocity")
    init_vel = float(vel_km_s) if vel_km_s is not None else None
    vel = {
        "initial_velocity_kms": init_vel,
        "deceleration_kms2": None,
        "entry_angle_deg": None,
        "linear_model": {"v0": init_vel, "a": None, "chi_squared": None},
        "whipple_jacchia_model": {"v_inf": init_vel, "K": None, "chi_squared": None},
        "velocity_profile": {"times": [], "distances_km": [], "altitudes_km": [],
                             "velocity_observed_kms": [], "velocity_linear_kms": [],
                             "velocity_wj_kms": [], "distance_fit_linear_km": []},
    }
    
    rad_ra = metadata.get("radiant_ra")
    radiant_ra = float(rad_ra) if rad_ra is not None else None
    rad_dec = metadata.get("radiant_dec")
    radiant_dec = float(rad_dec) if rad_dec is not None else None
    
    lat_val = metadata.get("entry_lat") or metadata.get("lat")
    entry_lat = float(lat_val) if lat_val is not None else None
    lon_val = metadata.get("entry_lon") or metadata.get("lon")
    entry_lon = float(lon_val) if lon_val is not None else None
    alt_val = metadata.get("terminal_altitude_km") or metadata.get("alt")
    entry_alt = float(alt_val) if alt_val is not None else None
    orbit = {"error": "Orbit computation not attempted"}
    shower = None
    quality = {"composite_score": 0, "label": "Error", "breakdown": {}}
    fall = None
    mass = None

    # 1. Triangulation
    if len(stations) < 2:
        log.warning("Not enough stations for triangulation (requires >= 2). Bypassing 3D reconstruction.")
        errors.append("Insufficient stations for 3D triangulation. Showing summary data only.")

        # --- NASA approximate orbit: synthesize radiant from lat/lon + velocity ---
        if init_vel is not None and entry_lat is not None and entry_lon is not None:
            try:
                # Approximate radiant: assume near-vertical entry
                # RA ≈ local sidereal time at impact point (converted to degrees), Dec ≈ latitude
                from backend.physics.coordinates import local_sidereal_time
                lst_rad = local_sidereal_time(jd, entry_lon)
                radiant_ra = float(np.degrees(lst_rad)) % 360.0   # LST returns radians → degrees, wrap [0,360]
                radiant_dec = max(-90.0, min(90.0, float(entry_lat)))  # clamp Dec to valid range

                orbit = compute_orbital_elements(
                    radiant_ra, radiant_dec, init_vel,
                    entry_lat, entry_lon, entry_alt or 80.0,
                    jd, apply_corrections=True,
                )
                orbit["estimated"] = True  # flag as approximate

                shower = match_shower(
                    float(orbit.get("corrected_radiant_ra", radiant_ra)),
                    float(orbit.get("corrected_radiant_dec", radiant_dec)),
                    float(orbit.get("geocentric_velocity_kms", init_vel)),
                    jd,
                )
            except Exception as e:
                log.warning("NASA approximate orbit failed: %s", e)
                errors.append(f"Approximate orbit: {e}")

        # --- Data-completeness quality score for summary events ---
        score = 0
        breakdown = {}
        if init_vel is not None:
            score += 25
            breakdown["velocity_data"] = {"score": 80, "weight": 0.25, "value": init_vel}
        else:
            breakdown["velocity_data"] = {"score": 0, "weight": 0.25, "value": None}
        if entry_lat is not None and entry_lon is not None:
            score += 20
            breakdown["geolocation"] = {"score": 80, "weight": 0.20, "value": f"{entry_lat:.1f}, {entry_lon:.1f}"}
        else:
            breakdown["geolocation"] = {"score": 0, "weight": 0.20, "value": None}
        if entry_alt is not None:
            score += 15
            breakdown["altitude"] = {"score": 80, "weight": 0.15, "value": entry_alt}
        else:
            breakdown["altitude"] = {"score": 0, "weight": 0.15, "value": None}
        energy = metadata.get("energy_kt")
        if energy is not None:
            score += 10
            breakdown["energy"] = {"score": 80, "weight": 0.10, "value": energy}
        else:
            breakdown["energy"] = {"score": 0, "weight": 0.10, "value": None}
        breakdown["multi_station"] = {"score": 0, "weight": 0.30, "value": "Single station"}

        label = "Estimated" if score >= 40 else "Summary"
        quality = {"composite_score": score, "label": label, "breakdown": breakdown}
    else:
        try:
            traj = triangulate_trajectory(stations, observations, jd)
            corrected_points = traj["trajectory_points"] # Default for timing step
        except Exception as e:
            log.exception("Triangulation failed")
            raise HTTPException(status_code=422, detail=f"Triangulation failed: {str(e)}")

        # 2. Timing offset estimation
        try:
            station_ids = list(set(o["station_id"] for o in observations))
            offsets = estimate_timing_offsets(traj["trajectory_points"], station_ids)
            corrected_points = apply_timing_offsets(traj["trajectory_points"], offsets)
        except Exception as e:
            log.warning("Timing estimation failed: %s", e)
            errors.append(f"Timing: {e}")
            offsets = {}

        # 3. Velocity fitting
        try:
            vel = fit_velocity(
                corrected_points,
                np.array(traj["trajectory_direction"]),
                np.array(traj["trajectory_start"]),
            )
            vel["entry_angle_deg"] = float(traj["entry_angle_deg"])

            # Sanity check: if fit was poor (high chi²) and velocity hit the cap,
            # fall back to metadata velocity or a conservative estimate
            chi2_lin = vel.get("linear_model", {}).get("chi_squared", 0)
            fitted_v0 = vel["initial_velocity_kms"]
            if chi2_lin > 1000 and fitted_v0 >= 71.5:
                # Fit failed badly — use metadata velocity if available
                meta_vel = metadata.get("estimated_velocity_kms")
                if meta_vel is not None:
                    vel["initial_velocity_kms"] = float(meta_vel)
                    vel["velocity_source"] = "metadata"
                    errors.append(f"Velocity fit unreliable (χ²={chi2_lin:.0f}), using metadata velocity {meta_vel} km/s")
                else:
                    # No metadata velocity — use a conservative 30 km/s (typical sporadic)
                    vel["initial_velocity_kms"] = 30.0
                    vel["velocity_source"] = "estimated"
                    errors.append(f"Velocity fit unreliable (χ²={chi2_lin:.0f}), using estimated 30 km/s")
            else:
                vel["velocity_source"] = "fitted"
        except Exception as e:
            log.warning("Velocity fit failed: %s", e)
            errors.append(f"Velocity: {e}")

        # 4. Radiant
        if "trajectory_direction" in traj:
            try:
                direction = np.array(traj["trajectory_direction"])
                norm = np.linalg.norm(direction)
                if norm < 1e-10:
                    raise ValueError("Zero-length trajectory direction")
                radiant_dir = -direction / norm
                radiant_ra, radiant_dec = unit_to_ra_dec(radiant_dir)
            except Exception as e:
                log.warning("Radiant computation failed: %s", e)
                errors.append(f"Radiant: {e}")

        # 5. Entry point geographic coords
        try:
            if "trajectory_start" in traj:
                gmst = greenwich_mean_sidereal_time(jd)
                entry_ecef = eci_to_ecef(np.array(traj["trajectory_start"]), gmst)
                geo = ecef_to_geodetic(entry_ecef)
                entry_lat, entry_lon = float(geo[0]), float(geo[1])
            else:
                gmst = greenwich_mean_sidereal_time(jd)
        except Exception as e:
            log.warning("ECEF→geodetic failed: %s", e)
            errors.append(f"Geodetic: {e}")
            gmst = greenwich_mean_sidereal_time(jd)

        # 6. Orbital elements
        try:
            if "trajectory_direction" in traj or (metadata.get("radiant_ra") is not None):
                orbit = compute_orbital_elements(
                    float(radiant_ra), float(radiant_dec),
                    float(vel["initial_velocity_kms"]),
                    float(entry_lat), float(entry_lon),
                    float(traj.get("entry_altitude_km", entry_alt)),
                    jd,
                    apply_corrections=True,
                )
            else:
                orbit = {"error": "Insufficient telemetry for Keplerian orbit generation."}
        except Exception as e:
            log.warning("Orbit computation failed: %s", e)
            errors.append(f"Orbit: {e}")
            orbit = {"error": str(e)}

        # 7. Shower matching
        try:
            if "trajectory_direction" in traj or (metadata.get("radiant_ra") is not None):
                shower = match_shower(
                    float(orbit.get("corrected_radiant_ra", radiant_ra)),
                    float(orbit.get("corrected_radiant_dec", radiant_dec)),
                    float(orbit.get("geocentric_velocity_kms", vel["initial_velocity_kms"])),
                    jd,
                )
            else:
                shower = None
        except Exception as e:
            log.warning("Shower match failed: %s", e)
            errors.append(f"Shower: {e}")
            shower = None

        # 8. Quality score
        try:
            if "trajectory_direction" in traj:
                n_total = traj.get("num_observations", 1)
                n_inliers = traj.get("num_inliers", n_total)
                outlier_ratio = (n_total - n_inliers) / max(n_total, 1)
                quality = compute_quality_score(
                    rms_residual_arcsec=float(traj.get("rms_residual_arcsec", 10.0)),
                    convergence_angle_Q=float(traj.get("convergence_angle_Q", 45.0)),
                    velocity_chi2=float(vel["linear_model"].get("chi_squared", 999.0)),
                    mc_convergence_ratio=1.0,
                    outlier_ratio=float(outlier_ratio),
                )
            else:
                quality = {"composite_score": 0, "label": "Summary", "breakdown": {"Triangulation": 0}}
        except Exception as e:
            log.warning("Quality score failed: %s", e)
            errors.append(f"Quality: {e}")
            quality = {"composite_score": 0, "label": "Error", "breakdown": {}}

    # 9. Fall prediction (stretch)
    try:
        terminal_v_list = vel["velocity_profile"].get("velocity_observed_kms", [])
        if terminal_v_list and float(terminal_v_list[-1]) < 5.0:
            fall = predict_fall(
                np.array(traj["trajectory_end"]),
                np.array(traj["trajectory_direction"]),
                float(terminal_v_list[-1]),
                float(traj["terminal_altitude_km"]),
                float(traj["entry_angle_deg"]),
            )
    except Exception as e:
        log.warning("Fall prediction failed: %s", e)
        errors.append(f"Fall: {e}")

    # 10. Mass estimation (stretch)
    try:
        mags = [o["brightness"] for o in observations if "brightness" in o]
        tss  = [o["timestamp"]  for o in observations if "timestamp"  in o and "brightness" in o]
        if len(mags) > 4: # Require at least 5 brightness measurements
            mass = estimate_mass(mags, tss, float(vel["initial_velocity_kms"]))
    except Exception as e:
        log.warning("Mass estimate failed: %s", e)
        errors.append(f"Mass: {e}")

    # Build result
    result = {
        "trajectory": {
            "start": traj.get("trajectory_start", []),
            "end": traj.get("trajectory_end", []),
            "direction": traj.get("trajectory_direction", []),
            "entry_altitude_km": float(traj.get("entry_altitude_km", 0.0)),
            "terminal_altitude_km": float(traj.get("terminal_altitude_km", 0.0)),
            "trajectory_length_km": float(traj.get("trajectory_length_km", 0.0)),
            "entry_angle_deg": float(traj.get("entry_angle_deg", 0.0)),
            "convergence_angle_Q": float(traj.get("convergence_angle_Q", 0.0)),
            "median_residual_arcsec": float(traj.get("median_residual_arcsec", 0.0)),
            "rms_residual_arcsec": float(traj.get("rms_residual_arcsec", 0.0)),
            "station_residuals": traj.get("station_residuals", {}),
            "num_observations": traj.get("num_observations", 0),
            "num_inliers": traj.get("num_inliers", 0),
            "entry_lat": float(entry_lat) if entry_lat is not None else None,
            "entry_lon": float(entry_lon) if entry_lon is not None else None,
            "terminal_altitude_km": float(traj["terminal_altitude_km"]) if "terminal_altitude_km" in traj else (float(entry_alt) if entry_alt is not None else None),
        },
        "velocity": vel,
        "radiant": {
            "ra_deg": float(radiant_ra) if radiant_ra is not None else None,
            "dec_deg": float(radiant_dec) if radiant_dec is not None else None,
            "corrected_ra": float(orbit.get("corrected_radiant_ra", radiant_ra)) if orbit.get("corrected_radiant_ra", radiant_ra) is not None else None,
            "corrected_dec": float(orbit.get("corrected_radiant_dec", radiant_dec)) if orbit.get("corrected_radiant_dec", radiant_dec) is not None else None,
        },
        "orbital_elements": orbit,
        "timing_offsets_ms": offsets,
        "shower_match": shower,
        "quality": quality,
        "fall_prediction": fall,
        "mass_estimate": mass,
        "pipeline_errors": errors,
    }

    return result


@router.post("/events/{event_id}/reconstruct")
async def reconstruct_event(event_id: str):
    """Run full reconstruction pipeline."""
    event_data = get_event(event_id)
    if event_data is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
    if "stations" not in event_data or "observations" not in event_data:
        raise HTTPException(status_code=422, detail="Missing station or observation data")

    result = _run_reconstruction(event_data)
    save_trajectory_cache(event_id, result)
    return result


@router.get("/events/{event_id}/trajectory")
async def get_trajectory(event_id: str):
    """Get cached trajectory data."""
    cache = get_trajectory_cache(event_id)
    if cache is None:
        # Auto-reconstruct
        event_data = get_event(event_id)
        if event_data is None:
            raise HTTPException(status_code=404, detail="Event not found")
        if "stations" not in event_data or "observations" not in event_data:
            raise HTTPException(status_code=422, detail="Missing data")
        cache = _run_reconstruction(event_data)
        save_trajectory_cache(event_id, cache)
    return cache


@router.get("/events/{event_id}/orbit")
async def get_orbit(event_id: str):
    """Get orbital elements."""
    cache = get_trajectory_cache(event_id)
    if cache is None:
        raise HTTPException(status_code=404, detail="Run reconstruction first")
    return cache.get("orbital_elements", {})


@router.post("/events/{event_id}/montecarlo")
async def run_mc(event_id: str, n_iterations: int = Query(100, ge=10, le=500)):
    """Run Monte Carlo uncertainty estimation."""
    event_data = get_event(event_id)
    if event_data is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if "stations" not in event_data or "observations" not in event_data:
        raise HTTPException(status_code=422, detail="Missing data")

    jd = jd_from_timestamp(event_data["metadata"].get("unix_timestamp", 1700000000))

    result = run_monte_carlo(
        event_data["stations"],
        event_data["observations"],
        jd,
        n_iterations=min(n_iterations, 200),
    )

    # Update cache with MC results
    cache = get_trajectory_cache(event_id)
    if cache:
        cache["uncertainty"] = result
        if "n_success" in result and "n_iterations" in result:
            # Recompute quality with MC convergence
            mc_ratio = result["n_success"] / result["n_iterations"]
            if "quality" in cache and "trajectory" in cache:
                from backend.physics.quality import compute_quality_score
                traj_data = cache["trajectory"]
                vel_data = cache.get("velocity", {})
                n_total = traj_data.get("num_observations", 1)
                n_inliers = traj_data.get("num_inliers", n_total)
                quality = compute_quality_score(
                    rms_residual_arcsec=traj_data.get("rms_residual_arcsec", 10),
                    convergence_angle_Q=traj_data.get("convergence_angle_Q", 45),
                    velocity_chi2=vel_data.get("linear_model", {}).get("chi_squared", 5),
                    mc_convergence_ratio=mc_ratio,
                    outlier_ratio=(n_total - n_inliers) / max(n_total, 1),
                )
                cache["quality"] = quality
        save_trajectory_cache(event_id, cache)

    return result


@router.get("/events/{event_id}/residuals")
async def get_residuals(event_id: str):
    """Get per-frame per-station angular residuals."""
    cache = get_trajectory_cache(event_id)
    if cache is None:
        raise HTTPException(status_code=404, detail="Run reconstruction first")
    return {
        "station_residuals": cache.get("trajectory", {}).get("station_residuals", {}),
        "median_arcsec": cache.get("trajectory", {}).get("median_residual_arcsec", 0),
        "rms_arcsec": cache.get("trajectory", {}).get("rms_residual_arcsec", 0),
    }
