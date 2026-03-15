<div align="center">

# B O L I D E — Project Report

**Multi-Station Meteor Trajectory Reconstruction Platform**

*Orion Astrothon 2026 · 48-Hour Advanced Challenge*

---

**420+ Real Events** · **5 Networks** · **10 Custom Physics Modules** · **Zero Black-Box Solvers**

</div>

---

## 1. What Is BOLIDE?

Every night, hundreds of cameras across the globe record meteors passing through Earth's atmosphere. Networks like the **Global Meteor Network (GMN)**, **NASA's All-Sky Fireball Network**, **FRIPON**, and the **American Meteor Society** capture precise angular coordinates, sub-millisecond timestamps, and multi-station geometries.

The raw data is publicly available — but effectively invisible. It exists as CSV files and obscure JSON APIs, formatted for the handful of planetary scientists who understand celestial coordinate systems, Julian date conventions, and atmospheric refraction corrections.

**BOLIDE changes that.** We built a complete platform that:

1. **Fetches** real observation data from 5 global citizen-science networks
2. **Reconstructs** full 3D atmospheric trajectories using custom SVD-based triangulation
3. **Computes** entry velocities via Whipple-Jacchia exponential drag modelling
4. **Determines** heliocentric Solar System orbits using vis-viva Keplerian mechanics
5. **Quantifies** uncertainty through 100-iteration Monte Carlo perturbation analysis
6. **Presents** everything through an interactive, visually rich web interface

No black-box solvers. No simulated data. Every photon is real, every matrix is ours.

---

## 2. How It Works — End-to-End Pipeline

### 2.1 Data Ingestion

BOLIDE ingests from **5 real-world data sources** with zero synthetic data:

| Source | What We Fetch | Events |
|--------|--------------|--------|
| **Global Meteor Network** | Per-station RA/Dec CSVs with 3–6 cameras per event, station GPS coordinates, sub-second timestamps | 33 multi-station |
| **NASA JPL Fireball API** | Live JSON from `ssd-api.jpl.nasa.gov` — impact energy (kilotons), velocity, lat/lon, altitude | 150+ bolides |
| **NASA All-Sky Fireball Network** | Calibrated fireball astrometry from dedicated all-sky cameras | 40+ events |
| **FRIPON (France)** | High-precision European network data with excellent astrometric quality | 30+ events |
| **American Meteor Society** | Citizen-reported fireballs via public JSON API — magnitudes, witness locations, timing | 65+ events |

Additionally, **1,100+ meteor showers** from the IAU Meteor Data Centre are loaded for shower association matching.

Each data source has a dedicated Python ingester that fetches, parses, normalizes into a unified schema (`event_id`, `metadata`, `stations[]`, `observations[]`), validates (≥2 stations, valid coordinates), and stores into a disk-backed JSON object store.

### 2.2 Coordinate Transform Chain

Camera observations arrive in geographic coordinates (latitude, longitude, altitude). The physics engine needs them in a common inertial frame. We perform a four-stage transform:

```
Geographic (φ, λ, h)
    │  WGS-84 ellipsoid: N(φ) = a / √(1 - e²sin²φ)
    ▼
ECEF (X, Y, Z)
    │  GMST rotation matrix
    ▼
ECI J2000 (inertial frame)
    │  Obliquity rotation: ε = 23.4393°
    ▼
Heliocentric Ecliptic (for orbit determination)
```

Every conversion is hand-coded in NumPy. RA/Dec celestial angles are converted to 3D unit direction vectors, with corrections for diurnal aberration (Earth's rotation effect on apparent radiant) and zenith attraction (gravitational focusing).

### 2.3 3D Triangulation via SVD

The core geometric problem: multiple cameras observe the same meteor from different locations. Their lines of sight (LoS) should intersect at the meteor's position — but due to measurement noise, they never perfectly do.

**Our approach:**
1. For each station, construct a LoS ray: origin point **P** + direction **d** (from RA/Dec)
2. Build an overdetermined linear system where we minimize the perpendicular distance from each ray to the trajectory line
3. Solve via **Singular Value Decomposition** (A = UΣV^T) — the optimal trajectory direction is the right-singular vector corresponding to the smallest singular value
4. Apply **RANSAC outlier rejection** — iteratively discard observations with angular residuals > 3σ (cosmic rays, aircraft, tracking glitches)
5. Extract: trajectory start/end points, direction vector, entry angle, convergence angle Q, and per-station residuals in arcseconds

The convergence angle Q measures the geometric strength of the multi-station observation — higher Q means the stations are spread out and the trajectory is well-constrained.

### 2.4 Velocity & Deceleration Fitting

Meteoroids decelerate as they penetrate the atmosphere. The raw position-vs-time data must be fitted to extract the true pre-atmospheric entry velocity.

We project all observations onto the trajectory axis to get **distance-along-track vs. time**, then fit two models:

- **Linear deceleration**: `v(t) = v₀ + at` — a simple baseline giving initial velocity and constant drag
- **Whipple-Jacchia exponential drag**:
  ```
  v(s) = v∞ · exp(-K ∫₀ˢ ρ(h) ds')
  ```
  where ρ(h) is atmospheric density from a multi-layer scale-height model, v∞ is the pre-atmospheric velocity, and K is the shape-density parameter — optimized via SciPy's Nelder-Mead minimizer

The velocity is physically capped at 72 km/s (maximum speed for an Earth-intercepting meteoroid). A multi-tier selection system picks the most reliable velocity estimate and tags it with its source (`fitted`, `metadata`, or `estimated`).

### 2.5 Timing Offset Correction

Different camera stations have slightly different clock times (typically 5–50ms of drift). At 25 km/s, even a 20ms offset produces 500 meters of positional error.

We treat inter-station timing offsets as **free parameters** and estimate them by minimizing the global residual between observed and predicted observation times given the fitted trajectory. These corrections are applied before the final velocity determination.

### 2.6 Heliocentric Orbit Determination

Once we know the meteor's radiant direction (where it came from in the sky) and its velocity, we can trace its orbit back through the Solar System.

The process:
1. **Correct diurnal aberration** — remove Earth's rotational velocity from the apparent radiant
2. **Correct zenith attraction** — account for Earth's gravity bending the incoming trajectory: `v_geo = √(v∞² + v_esc²)`
3. **Transform to heliocentric** — add Earth's orbital velocity (29.78 km/s) to the corrected geocentric velocity, rotated into ecliptic coordinates
4. **Compute Keplerian elements** via the vis-viva equation:
   ```
   E = ½v² - GM☉/r  →  a = -GM☉/(2E)
   ```
5. Extract the full orbital element set: semi-major axis (a), eccentricity (e), inclination (i), argument of perihelion (ω), longitude of ascending node (Ω), perihelion distance (q), aphelion distance (Q), and the Tisserand parameter T_J

The orbit is automatically classified as **bound** (e < 1, Solar System origin), **parabolic** (e ≈ 1), or **hyperbolic** (e > 1, indicating noisy input data — a known challenge in meteor astronomy that we flag transparently).

### 2.7 Shower Association

We cross-reference each meteor's corrected radiant RA/Dec against the IAU Meteor Data Centre catalogue of **1,100+ established showers**. Matching criteria: angular separation below threshold, velocity within range, and solar longitude within the seasonal activity window. Each match reports a confidence score.

### 2.8 Monte Carlo Uncertainty Estimation

A single deterministic reconstruction gives no indication of uncertainty. We address this by:

1. Running **100 iterations**, each injecting Gaussian noise (σ = 30 arcseconds) into the input RA/Dec observations
2. **Re-executing the entire pipeline** per iteration — triangulation, velocity fit, orbit determination
3. Computing 1σ confidence bounds on: velocity, radiant position, and all orbital elements
4. Reporting: velocity σ (km/s), radiant area (deg²), RA/Dec uncertainty (degrees)

### 2.9 Quality Scoring

Not all reconstructions are equally reliable. We compute a composite 0–100 quality score from five weighted components:

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Astrometric RMS | 30% | Angular residual quality (arcseconds) |
| Convergence Angle Q | 20% | Geometric strength of station baseline |
| Velocity χ² | 20% | Goodness of the velocity fit |
| MC Convergence | 15% | Stability across Monte Carlo iterations |
| Outlier Ratio | 15% | Fraction of observations rejected by RANSAC |

The score maps to human-readable labels: **Excellent** (80–100), **Good** (60–80), **Fair** (40–60), **Poor** (0–40), each with a plain-English explanation visible in the UI.

### 2.10 Stretch Features

- **Meteorite Fall Predictor**: For deep-penetrating events (terminal altitude < 35 km, velocity < 5 km/s), computes the dark-flight trajectory from terminal point to ground, accounting for gravitational arc, atmospheric density, and wind drift
- **Mass Estimate**: Applies the luminous efficiency relation to observed brightness curves, estimating initial meteoroid mass from peak magnitude and velocity
- **Live Feed**: Real-time integration with the American Meteor Society API, streaming the latest reported fireballs into the application sidebar

---

## 3. What We Built — Application Features

### 3.1 Event Catalogue & Dashboard (`/`)

The mission control for the unified observation catalog:
- **420+ authentic events** from 5 networks — no upload needed, data loads on startup
- **Real-time filters**: by network (GMN / NASA / FRIPON / AMS), meteor shower, and free-text search
- **Event cards** with: UTC timestamp, station count, velocity, shower association, SVG sky-map thumbnail
- **Network distribution chart**: live bar graph showing event counts across sources
- **Live feed sidebar**: latest AMS-reported fireballs streaming in real-time

### 3.2 Trajectory Reconstruction Viewer (`/event/[id]`)

The core investigative interface — every number computed server-side, rendered client-side:
- **3 interactive trajectory views**: SVG-rendered 3D Globe, Ground Track projection, Lines-of-Sight intersection — togglable
- **Velocity deceleration chart**: observed data points plotted against Linear and Whipple-Jacchia model curves with model toggle
- **5 stat cards**: initial velocity (± uncertainty), entry angle, peak magnitude, trajectory length, shower match
- **Station panel**: per-station angular residuals in arcseconds, frame counts, geographic coordinates
- **Heliocentric orbit diagram**: SVG rendering of the Keplerian orbit relative to Earth's orbit
- **Full orbital elements table**: a, e, i, ω, Ω, q, Q, Tisserand parameter, orbit type
- **Quality score**: composite 0–100 with per-component breakdown in plain English
- **Event navigation**: quick-jump dropdown between events without returning to catalogue

### 3.3 Multi-Event Comparison (`/compare`)

Select 2–5 events for simultaneous side-by-side analysis:
- **Shared sky map**: overlaid radiant positions on a celestial coordinate projection
- **Orbital elements table**: tabular comparison of a, e, i, ω, Ω across selected events
- **Velocity overlay**: normalized deceleration curves from multiple events on a single chart
- **Shower association panel**: confidence scores and angular separations for each event

### 3.4 Sky Radiant Analysis (`/radiant`)

All-sky map plotting every event's radiant direction on a celestial coordinate projection, with shower clustering highlighted in distinct colors. Displays total reconstructed events, valid LoS intersections, and shower association rate.

### 3.5 Solar System Orbit Explorer (`/orbit`)

Browse computed orbital elements for every event. Cards display shower association, velocity, and link directly to the full trajectory viewer. Orbit type (bound/hyperbolic/parabolic) is automatically classified.

### 3.6 Monte Carlo Simulation Interface (`/montecarlo`)

Select any multi-station event, run 100-iteration perturbation analysis, and view: velocity σ, radiant area (deg²), RA/Dec uncertainty bounds — all computed server-side.

### 3.7 Meteorite Fall Predictor (`/fall`)

Identifies deep-penetrating fireballs and computes prospective ground-truth impact ellipses for events where meteorite survival is plausible.

### 3.8 Physics Engine Reference (`/physics`)

A fully transparent, interactive mathematics notebook documenting every equation in the pipeline:
- Animated SVD triangulation demo showing how multi-station rays converge
- Animated Whipple-Jacchia deceleration profile showing exponential drag
- Live heliocentric orbit animation showing state vector composition
- Detailed data ingestion pipeline flowchart with all 5 sources and animated data pulse

---

## 4. Engineering Challenges

### Building a 4-Stage Coordinate Transform Chain from Scratch

The pipeline traverses four coordinate systems: Geographic → ECEF → ECI J2000 → Heliocentric Ecliptic. Each transform involves non-trivial mathematics (ellipsoidal Earth model, sidereal time rotation, obliquity correction). A single unit error (degrees vs radians) at any boundary cascades through the entire pipeline. We solved this with strict boundary conventions: all public API values in degrees, all internal computation in radians, with explicit conversion functions at every interface.

### Implementing Overdetermined SVD Triangulation

Textbook triangulation assumes two perfectly intersecting rays. Real meteor data has 3–6 noisy stations with rays that miss each other by kilometers. We implemented an overdetermined least-squares SVD approach that finds the best-fit trajectory through all stations simultaneously, with RANSAC-based robust fitting to automatically reject outlier observations. This is significantly more sophisticated than simple two-station intersection.

### Whipple-Jacchia Atmospheric Drag Modelling

The standard linear deceleration model fails for bright fireballs that experience significant atmospheric drag. We implemented the full Whipple-Jacchia exponential drag model, which requires numerical integration of atmospheric density along the trajectory path using a multi-layer scale-height approximation. The model parameters are optimized via bounded Nelder-Mead to prevent non-physical solutions.

### Multi-Network Data Normalization

Five data sources, five different schemas, five different coordinate conventions. GMN provides per-station CSV files with RA/Dec per frame. NASA provides JSON with impact energy in kilotons. AMS provides citizen reports with magnitude estimates. We built dedicated ingesters that normalize everything into a single unified schema, making cross-network comparison seamless.

### End-to-End Monte Carlo Re-execution

Most Monte Carlo implementations perturb a single computation step. Ours re-runs the **entire** pipeline — triangulation, velocity fitting, orbit determination — for each of the 100 iterations. This captures the full propagation of observational uncertainty through every computational stage, producing genuinely representative confidence intervals.

---

## 5. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.11 + FastAPI | REST API server, physics computation |
| **Physics Engine** | NumPy + SciPy (custom) | All geometry, dynamics, orbit math — no external astronomy libraries |
| **Ephemeris** | Skyfield | Earth orbital velocity for heliocentric orbit determination |
| **Frontend** | Next.js 15 + React 19 | Interactive visualization, responsive UI |
| **Visualization** | Custom SVG | Trajectory, orbit, and radiant diagrams — hand-drawn, no charting libraries |
| **Data Store** | JSON (disk-backed) | Event persistence with indexed lookups and trajectory caching |
| **Data Sources** | GMN CSVs, NASA JPL API, FRIPON, AMS API, IAU MDC | 5 real-world meteor observation networks + shower catalogue |

---

## 6. Data Integrity

Every piece of data in BOLIDE traces back to a real photon hitting a real camera sensor:

- **420+ events** fetched from 5 authentic astronomical observation networks
- **Zero synthetic data** — no `Math.random()`, no placeholder values, no simulated observations
- **All station coordinates** are real geographic positions (no origins at 0,0)
- **All velocities** fall within the physically valid range of 0–72 km/s
- **Events span multiple months** with natural temporal distribution
- **Known meteor showers** (Geminids, Perseids, Leonids, Orionids, Eta Aquariids) are correctly identified

---

## 7. Hackathon Compliance

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Real open data (≥2 sources) | Completed | 5 sources: GMN, NASA JPL, NASA AFSN, FRIPON, AMS |
| 100+ events | Completed | **420+** events across 5 networks |
| Custom 3D triangulation | Completed | SVD LoS least-squares in `triangulation.py` |
| Custom velocity fitting | Completed | Linear + Whipple-Jacchia in `velocity.py` |
| No black-box solvers | Completed | All geometry hand-built in NumPy/SciPy |
| Server-side computation | Completed | All physics via FastAPI; browser only renders |
| Timing offset handling | Completed | Free parameter estimation in `timing.py` |
| Angular residuals exposed | Completed | Per-station arcsecond residuals in event detail UI |
| Monte Carlo uncertainty | Completed | 100 iterations, σ = 30″, 1σ confidence bounds |
| Multi-event comparison | Completed | `/compare` with shared sky map + velocity overlay |
| Shower association (IAU) | Completed | 1,100+ showers from IAU MDC catalogue |
| **Stretch**: Meteorite fall prediction | Completed | Fall candidate identification + strewn-field computation |
| **Stretch**: Real-time feed | Completed | AMS fireball API live integration |
| **Stretch**: Mass estimate | Completed | Luminous efficiency computation |

> **"The core geometry — 3D triangulation and velocity/deceleration fitting — must be implemented by your team using foundational libraries (NumPy, SciPy)."**
>
> Every line of the triangulation matrix assembly, SVD decomposition, RANSAC rejection, Whipple-Jacchia integral, and Keplerian orbit algebra is written by our team. No WesternMeteorPyLib. No black-box solvers. Complete source transparency.

---

<p align="center">
  <strong>B O L I D E</strong><br/>
  <em>Bright Objects Localized In Dynamic Exploration</em><br/><br/>
  Because every streak of light has a story — and it deserves to be told.
</p>
