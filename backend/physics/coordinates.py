"""
BOLIDE — Coordinate system transforms.

Hand-implemented using NumPy.  No black-box solvers.
Covers:
  geodetic → ECEF (WGS-84)
  RA/Dec  → unit direction vector
  ECEF    → ECI  (J2000 via sidereal rotation)
  Atmospheric refraction, diurnal aberration, zenith attraction
  Julian-date / sidereal-time helpers
"""

from __future__ import annotations
import numpy as np
from backend.config import (
    WGS84_A, WGS84_B, WGS84_E2, WGS84_F,
    EARTH_OMEGA, OBLIQUITY_J2000,
)

_DEG = np.pi / 180.0
_ARCSEC = _DEG / 3600.0

# ── Geodetic ↔ ECEF ───────────────────────────────────────────────────

def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_m: float) -> np.ndarray:
    """Convert geodetic (lat, lon, alt) to ECEF Cartesian [m]."""
    lat = lat_deg * _DEG
    lon = lon_deg * _DEG
    sin_lat, cos_lat = np.sin(lat), np.cos(lat)
    sin_lon, cos_lon = np.sin(lon), np.cos(lon)

    N = WGS84_A / np.sqrt(1.0 - WGS84_E2 * sin_lat ** 2)
    x = (N + alt_m) * cos_lat * cos_lon
    y = (N + alt_m) * cos_lat * sin_lon
    z = (N * (1.0 - WGS84_E2) + alt_m) * sin_lat
    return np.array([x, y, z], dtype=np.float64)


def ecef_to_geodetic(ecef: np.ndarray):
    """Convert ECEF [m] back to (lat_deg, lon_deg, alt_m).  Bowring iterative."""
    x, y, z = ecef
    lon = np.arctan2(y, x)
    p = np.hypot(x, y)
    lat = np.arctan2(z, p * (1 - WGS84_E2))
    for _ in range(10):
        sin_lat = np.sin(lat)
        N = WGS84_A / np.sqrt(1.0 - WGS84_E2 * sin_lat ** 2)
        lat = np.arctan2(z + WGS84_E2 * N * sin_lat, p)
    alt = p / np.cos(lat) - N
    return np.degrees(lat), np.degrees(lon), alt


# ── RA / Dec → direction vector ───────────────────────────────────────

def ra_dec_to_unit(ra_deg: float, dec_deg: float) -> np.ndarray:
    """Equatorial RA/Dec (degrees) → Cartesian unit vector (ECI aligned)."""
    ra = ra_deg * _DEG
    dec = dec_deg * _DEG
    cos_dec = np.cos(dec)
    return np.array([
        cos_dec * np.cos(ra),
        cos_dec * np.sin(ra),
        np.sin(dec),
    ], dtype=np.float64)


def unit_to_ra_dec(v: np.ndarray):
    """Cartesian unit vector → (RA_deg, Dec_deg)."""
    v = v / np.linalg.norm(v)
    dec = np.arcsin(np.clip(v[2], -1, 1))
    ra = np.arctan2(v[1], v[0]) % (2 * np.pi)
    return np.degrees(ra), np.degrees(dec)


# ── Time helpers ──────────────────────────────────────────────────────

def julian_date(year: int, month: int, day: int,
                hour: float = 0, minute: float = 0, second: float = 0) -> float:
    """UTC calendar → Julian Date (JD)."""
    if month <= 2:
        year -= 1
        month += 12
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    day_frac = day + (hour + minute / 60 + second / 3600) / 24.0
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day_frac + B - 1524.5


def jd_from_timestamp(ts: float) -> float:
    """Unix timestamp → JD."""
    return ts / 86400.0 + 2440587.5


def greenwich_mean_sidereal_time(jd: float) -> float:
    """GMST in radians for a given JD (IAU 1982 formula)."""
    T = (jd - 2451545.0) / 36525.0
    gmst_sec = (
        67310.54841
        + (876600 * 3600 + 8640184.812866) * T
        + 0.093104 * T ** 2
        - 6.2e-6 * T ** 3
    )
    return (gmst_sec % 86400) / 86400.0 * 2.0 * np.pi


def local_sidereal_time(jd: float, lon_deg: float) -> float:
    """Local sidereal time in radians."""
    return greenwich_mean_sidereal_time(jd) + lon_deg * _DEG


# ── ECEF ↔ ECI ────────────────────────────────────────────────────────

def ecef_to_eci(ecef: np.ndarray, gmst_rad: float) -> np.ndarray:
    """Rotate ECEF → ECI (J2000) by Greenwich sidereal angle."""
    c, s = np.cos(gmst_rad), np.sin(gmst_rad)
    R = np.array([[c, -s, 0],
                  [s,  c, 0],
                  [0,  0, 1]], dtype=np.float64)
    return R @ ecef


def eci_to_ecef(eci: np.ndarray, gmst_rad: float) -> np.ndarray:
    """Rotate ECI → ECEF."""
    c, s = np.cos(gmst_rad), np.sin(gmst_rad)
    R = np.array([[ c, s, 0],
                  [-s, c, 0],
                  [ 0, 0, 1]], dtype=np.float64)
    return R @ eci


# ── Direction vector in ECI frame for a station ───────────────────────

def observation_direction_eci(ra_deg: float, dec_deg: float,
                              station_lat: float, station_lon: float,
                              jd: float) -> np.ndarray:
    """
    Convert topocentric RA/Dec observation to a direction vector in ECI.
    Already in ECI because RA/Dec is referenced to the celestial sphere.
    """
    return ra_dec_to_unit(ra_deg, dec_deg)


# ── Atmospheric refraction correction ─────────────────────────────────

def refraction_correction(apparent_alt_deg: float) -> float:
    """
    Approximate atmospheric refraction correction (Meeus formula).
    Returns correction in degrees to ADD to apparent altitude.
    """
    if apparent_alt_deg < -0.5:
        return 0.0
    if apparent_alt_deg < 0.0:
        apparent_alt_deg = 0.0
    # Refraction in arcminutes
    R = 1.02 / np.tan((apparent_alt_deg + 10.3 / (apparent_alt_deg + 5.11)) * _DEG) + 0.0019279
    return R / 60.0  # convert arcmin → degrees


# ── Diurnal aberration ────────────────────────────────────────────────

def diurnal_aberration(ra_deg: float, dec_deg: float,
                       lst_rad: float, lat_deg: float):
    """
    Correct RA/Dec for diurnal aberration due to Earth's rotation.
    Returns corrected (ra_deg, dec_deg).
    """
    lat = lat_deg * _DEG
    ra = ra_deg * _DEG
    dec = dec_deg * _DEG
    H = lst_rad - ra  # hour angle

    # Diurnal aberration constant ≈ 0.3200″ at the equator
    k = 0.3200 * _ARCSEC  # radians

    cos_lat = np.cos(lat)
    cos_dec = np.cos(dec)
    sin_dec = np.sin(dec)
    cos_H = np.cos(H)
    sin_H = np.sin(H)

    if abs(cos_dec) < 1e-12:
        return ra_deg, dec_deg

    d_ra = -k * cos_lat * cos_H / cos_dec
    d_dec = -k * cos_lat * sin_H * sin_dec

    return ra_deg + np.degrees(d_ra), dec_deg + np.degrees(d_dec)


# ── Zenith attraction ────────────────────────────────────────────────

def zenith_attraction(ra_deg: float, dec_deg: float,
                      v_inf_km_s: float,
                      lat_deg: float, lon_deg: float,
                      jd: float):
    """
    Correct geocentric radiant for zenith attraction (gravity focus effect).
    Converts apparent radiant to true radiant.

    v_inf_km_s: geocentric velocity at infinity
    Returns corrected (ra_deg, dec_deg, v_geo_corrected_km_s).
    """
    v_inf = v_inf_km_s * 1000.0  # m/s
    v_esc = 11186.0  # Earth escape velocity at surface, m/s

    # True geocentric velocity
    v_geo = np.sqrt(v_inf ** 2 + v_esc ** 2)

    # Zenith attraction angle
    # sin(z_true) / sin(z_app) = v_inf / v_geo
    # where z is the zenith distance of the radiant

    # Compute zenith distance of apparent radiant
    lst = local_sidereal_time(jd, lon_deg)
    lat = lat_deg * _DEG
    ra = ra_deg * _DEG
    dec = dec_deg * _DEG
    H = lst - ra

    # Altitude of radiant
    sin_alt = np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(H)
    alt = np.arcsin(np.clip(sin_alt, -1, 1))
    z_app = np.pi / 2 - alt  # zenith distance

    if abs(np.sin(z_app)) < 1e-10:
        return ra_deg, dec_deg, v_geo / 1000.0

    # Corrected zenith distance
    sin_z_true = np.sin(z_app) * v_inf / v_geo
    sin_z_true = np.clip(sin_z_true, -1, 1)
    z_true = np.arcsin(sin_z_true)

    # Shift the radiant toward the zenith by (z_app - z_true)
    dz = z_app - z_true

    # Azimuth of radiant
    sin_az = -np.cos(dec) * np.sin(H) / np.cos(alt)
    cos_az = (np.sin(dec) - np.sin(lat) * np.sin(alt)) / (np.cos(lat) * np.cos(alt))
    az = np.arctan2(sin_az, cos_az)

    # New altitude
    alt_true = np.pi / 2 - z_true

    # Convert back to RA/Dec
    sin_dec_new = np.sin(lat) * np.sin(alt_true) + np.cos(lat) * np.cos(alt_true) * np.cos(az)
    dec_new = np.arcsin(np.clip(sin_dec_new, -1, 1))
    cos_H_new = (np.sin(alt_true) - np.sin(lat) * np.sin(dec_new)) / (np.cos(lat) * np.cos(dec_new))
    cos_H_new = np.clip(cos_H_new, -1, 1)
    sin_H_new = -np.cos(alt_true) * np.sin(az) / np.cos(dec_new)
    H_new = np.arctan2(sin_H_new, cos_H_new)

    ra_new = lst - H_new
    return np.degrees(ra_new) % 360.0, np.degrees(dec_new), v_geo / 1000.0


# ── ECI → Heliocentric ecliptic ──────────────────────────────────────

def eci_to_ecliptic(vec: np.ndarray) -> np.ndarray:
    """Rotate from equatorial (ECI / J2000) to ecliptic frame."""
    eps = OBLIQUITY_J2000 * _DEG
    c, s = np.cos(eps), np.sin(eps)
    R = np.array([[1, 0,  0],
                  [0, c,  s],
                  [0, -s, c]], dtype=np.float64)
    return R @ vec


def angular_separation(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Angular separation between two sky positions in degrees."""
    v1 = ra_dec_to_unit(ra1, dec1)
    v2 = ra_dec_to_unit(ra2, dec2)
    dot = np.clip(np.dot(v1, v2), -1, 1)
    return np.degrees(np.arccos(dot))
