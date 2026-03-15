"""
BOLIDE — Configuration constants for the meteor trajectory reconstruction platform.
"""
import os, pathlib

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EVENTS_DIR = DATA_DIR / "events"
REFERENCE_DIR = DATA_DIR / "reference"

# Ensure dirs exist
EVENTS_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

# ── WGS-84 Ellipsoid ──────────────────────────────────────────────────
WGS84_A = 6_378_137.0            # semi-major axis  [m]
WGS84_F = 1.0 / 298.257223563    # flattening
WGS84_B = WGS84_A * (1 - WGS84_F)
WGS84_E2 = 2 * WGS84_F - WGS84_F ** 2  # first eccentricity squared

# ── Physical constants ─────────────────────────────────────────────────
EARTH_MU = 3.986004418e14        # GM  [m³/s²]
EARTH_RADIUS = 6_371_000.0       # mean radius [m]
EARTH_OMEGA = 7.2921159e-5       # rotation rate [rad/s]
AU_METERS = 1.495978707e11       # 1 AU in metres
OBLIQUITY_J2000 = 23.4392911     # obliquity of ecliptic [deg]

# ── Monte-Carlo defaults ──────────────────────────────────────────────
MC_ITERATIONS = 100
MC_SIGMA_ARCSEC = 30.0           # Gaussian noise σ on RA/Dec [arcsec]

# ── Quality thresholds ─────────────────────────────────────────────────
OUTLIER_SIGMA = 3.0              # RANSAC outlier rejection threshold
SHOWER_MAX_SEPARATION_DEG = 5.0  # max angular sep for shower match
SHOWER_VELOCITY_TOLERANCE = 0.15 # 15 % relative velocity tolerance

# ── API ────────────────────────────────────────────────────────────────
CORS_ORIGINS = ["*"]
PAGE_SIZE = 20
