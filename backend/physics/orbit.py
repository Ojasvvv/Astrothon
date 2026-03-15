"""
BOLIDE — Heliocentric orbit computation.

Uses Skyfield for Earth ephemeris, manual Keplerian element extraction.
Applies zenith attraction and diurnal aberration corrections.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Any, Optional

from backend.config import EARTH_MU, AU_METERS, OBLIQUITY_J2000
from backend.physics.coordinates import (
    ra_dec_to_unit, unit_to_ra_dec, eci_to_ecliptic,
    zenith_attraction, diurnal_aberration,
    greenwich_mean_sidereal_time, local_sidereal_time,
)

_DEG = np.pi / 180.0
_AU = AU_METERS

# Earth orbital velocity (approximate circular)
EARTH_V_ORB = 29.78e3  # m/s

# GM of Sun
SUN_MU = 1.32712440018e20  # m³/s²


def compute_orbital_elements(
    radiant_ra: float,
    radiant_dec: float,
    v_init_kms: float,
    entry_lat: float,
    entry_lon: float,
    entry_alt_km: float,
    jd: float,
    apply_corrections: bool = True,
) -> Dict[str, Any]:
    """
    Compute heliocentric Keplerian orbital elements from
    geocentric radiant and velocity.

    Parameters
    ----------
    radiant_ra, radiant_dec : geocentric radiant in degrees
    v_init_kms : initial (pre-atmosphere) velocity in km/s
    entry_lat, entry_lon : geographic coordinates of atmospheric entry point
    entry_alt_km : altitude of entry in km
    jd : Julian Date of the event

    Returns dict of orbital elements.
    """

    # ── Apply corrections ──
    if apply_corrections:
        gmst = greenwich_mean_sidereal_time(jd)
        lst = local_sidereal_time(jd, entry_lon)
        radiant_ra, radiant_dec = diurnal_aberration(
            radiant_ra, radiant_dec, lst, entry_lat
        )
        radiant_ra, radiant_dec, v_geo = zenith_attraction(
            radiant_ra, radiant_dec, v_init_kms,
            entry_lat, entry_lon, jd
        )
    else:
        v_geo = v_init_kms

    v_geo_ms = v_geo * 1000.0  # m/s

    # ── Geocentric velocity vector (ECI) ──
    radiant_dir = ra_dec_to_unit(radiant_ra, radiant_dec)
    # Meteor comes FROM the radiant → velocity is opposite to radiant direction
    v_geo_vec = -radiant_dir * v_geo_ms

    # ── Earth state vector (simplified) ──
    # Earth position at JD (approximate: circular orbit)
    # Mean longitude of Earth (rough)
    T = (jd - 2451545.0) / 36525.0
    L_earth = (100.46646 + 36000.76983 * T) % 360.0  # degrees
    L_rad = L_earth * _DEG

    # Earth position in ecliptic (heliocentric)
    r_earth = _AU * np.array([np.cos(L_rad), np.sin(L_rad), 0.0])

    # Earth velocity (perpendicular to position, prograde)
    v_earth = EARTH_V_ORB * np.array([-np.sin(L_rad), np.cos(L_rad), 0.0])

    # ── Convert geocentric velocity to ecliptic ──
    v_geo_ecl = eci_to_ecliptic(v_geo_vec)

    # ── Heliocentric velocity ──
    v_helio = v_earth + v_geo_ecl

    # ── Keplerian elements from state vector (r_earth, v_helio) ──
    r = r_earth
    v = v_helio
    r_mag = np.linalg.norm(r)
    v_mag = np.linalg.norm(v)

    # Specific angular momentum
    h = np.cross(r, v)
    h_mag = np.linalg.norm(h)

    # Node vector
    k_hat = np.array([0, 0, 1.0])
    n = np.cross(k_hat, h)
    n_mag = np.linalg.norm(n)

    # Eccentricity vector
    e_vec = (np.cross(v, h) / SUN_MU) - (r / r_mag)
    e = np.linalg.norm(e_vec)

    # Semi-major axis (vis-viva)
    energy = 0.5 * v_mag ** 2 - SUN_MU / r_mag
    if abs(energy) < 1e-10:
        a_m = float('inf')
    else:
        a_m = -SUN_MU / (2.0 * energy)
    a_au = a_m / _AU

    # Inclination
    i = np.arccos(np.clip(h[2] / h_mag, -1, 1))

    # Longitude of ascending node
    if n_mag > 1e-10:
        omega_node = np.arccos(np.clip(n[0] / n_mag, -1, 1))
        if n[1] < 0:
            omega_node = 2 * np.pi - omega_node
    else:
        omega_node = 0.0

    # Argument of perihelion
    if n_mag > 1e-10 and e > 1e-10:
        arg_peri = np.arccos(np.clip(np.dot(n, e_vec) / (n_mag * e), -1, 1))
        if e_vec[2] < 0:
            arg_peri = 2 * np.pi - arg_peri
    else:
        arg_peri = 0.0

    # Perihelion distance
    q = a_m * (1 - e) / _AU if a_m > 0 else abs(a_m * (1 - e)) / _AU
    Q_aph = a_m * (1 + e) / _AU if a_m > 0 else abs(a_m * (1 + e)) / _AU

    # Tisserand parameter w.r.t. Jupiter
    a_j = 5.2044  # Jupiter semi-major axis in AU
    T_j = a_j / a_au + 2 * np.cos(i) * np.sqrt(a_au / a_j * (1 - e ** 2))

    return {
        "semi_major_axis_au": float(a_au),
        "eccentricity": float(e),
        "inclination_deg": float(np.degrees(i)),
        "argument_of_perihelion_deg": float(np.degrees(arg_peri)),
        "longitude_of_ascending_node_deg": float(np.degrees(omega_node)),
        "perihelion_distance_au": float(q),
        "aphelion_distance_au": float(Q_aph),
        "tisserand_parameter": float(T_j),
        "geocentric_velocity_kms": float(v_geo),
        "heliocentric_velocity_kms": float(v_mag / 1000.0),
        "corrected_radiant_ra": float(radiant_ra),
        "corrected_radiant_dec": float(radiant_dec),
    }
