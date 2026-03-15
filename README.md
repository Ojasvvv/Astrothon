<div align="center">
  <br/><br/>

  # ☄️ B O L I D E

  **Multi-Station Meteor Trajectory Reconstruction Platform**

  *Turning raw citizen-science sky data into explorable, three-dimensional atmospheric physics.*

  [![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js&logoColor=white)](https://nextjs.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
  [![NumPy](https://img.shields.io/badge/NumPy-Custom_Physics-013243?logo=numpy&logoColor=white)](https://numpy.org)
  [![SciPy](https://img.shields.io/badge/SciPy-Optimization-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

  <br/>

  **420+ Real Meteor Events** · **5 Data Networks** · **Custom Physics Engine** · **Zero Black-Box Solvers**

</div>

<hr/>

## 🌟 Why BOLIDE?

> **BOLIDE** — *Bright Objects Localized In Dynamic Exploration*

A **bolide** is the most spectacular kind of meteor — a fireball so bright it outshines Venus, sometimes fragmenting mid-flight, occasionally surviving to reach the ground as a meteorite. We named our platform after this phenomenon because BOLIDE does for meteor data what a bolide does for the night sky: **it makes the invisible visible.**

Every night, hundreds of cameras across the globe silently record streaks of light. The scientific data behind those streaks — precise angular coordinates, sub-millisecond timestamps, multi-station geometries — is **publicly available** but effectively invisible. It sits in CSV files, behind obscure APIs, formatted for a handful of planetary scientists who know the coordinate systems, the Julian date conventions, the atmospheric refraction corrections.

**BOLIDE changes that.** We built a platform that:

- 🔭 **Ingests real data** from 5 global meteor observation networks — no synthetic data, no simulations, no placeholders
- ⚛️ **Runs a custom physics engine** built from scratch in NumPy/SciPy — every matrix decomposition, every coordinate transform, every atmospheric drag integral is ours
- 🌍 **Reconstructs 3D trajectories** through the atmosphere using multi-station line-of-sight triangulation via SVD
- 🪐 **Traces orbits back to the Solar System** — computing the Keplerian elements that tell you whether a rock came from the asteroid belt or a cometary cloud
- 📊 **Makes it all explorable** — through interactive 3D viewers, velocity charts, orbital diagrams, and Monte Carlo uncertainty visualizations
- 🧑‍🔬 **Requires zero prior knowledge** — a non-scientist can understand every output

In short: **BOLIDE is a telescope pointed at data, not the sky.**

---

## 🏗️ Architecture

BOLIDE operates on a strict decoupling of **Data Ingestion → Physics Computation → Visual Rendering**. Every computation runs server-side. The browser renders results — it never runs the physics.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OPEN DATA SOURCES                                │
│  ┌───────────┐  ┌──────────────┐  ┌──────────┐  ┌─────┐  ┌──────────┐ │
│  │  GMN CSVs │  │ NASA JPL API │  │  FRIPON   │  │ AMS │  │ IAU MDC  │ │
│  └─────┬─────┘  └──────┬───────┘  └────┬─────┘  └──┬──┘  └────┬─────┘ │
└────────┼───────────────┼───────────────┼───────────┼───────────┼───────┘
         │               │               │           │           │
         ▼               ▼               ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     BOLIDE BACKEND (FastAPI + Python)                    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  DATA INGESTERS  (gmn_ingester · nasa_ingester · iau_ingester) │    │
│  └────────────────────────────┬────────────────────────────────────┘    │
│                               ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  UNIFIED JSON OBJECT STORE  (420+ events, normalized schema)   │    │
│  └────────────────────────────┬────────────────────────────────────┘    │
│                               ▼                                         │
│  ┌─────────────── PHYSICS ENGINE (Custom NumPy/SciPy) ───────────┐    │
│  │                                                                 │    │
│  │  Coordinate      LoS SVD         Whipple-Jacchia    Timing     │    │
│  │  Transforms  →  Triangulation →  Velocity Fit    →  Offsets    │    │
│  │  (WGS84/ECEF)   (RANSAC)         (Exponential)      (Free      │    │
│  │                                                       params)   │    │
│  │       ↓                                                         │    │
│  │  Orbital          Monte Carlo      Shower           Quality     │    │
│  │  Elements     →  Uncertainty   →  Association   →  Scoring     │    │
│  │  (Vis-Viva)       (100 iter)       (IAU MDC)        (0-100)    │    │
│  │                                                                 │    │
│  │  Fall Predictor · Mass Estimate · Atmospheric Refraction        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               ▼                                         │
│  ┌─────────────── REST API LAYER ─────────────────────────────────┐    │
│  │  /api/events · /api/events/{id}/trajectory · /api/compare      │    │
│  │  /api/events/{id}/montecarlo · /api/stats · /api/livefeed      │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     BOLIDE FRONTEND (Next.js 15)                        │
│                                                                         │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌─────────┐ ┌───────────┐ │
│  │Catalogue │ │Event Detail  │ │  Compare  │ │  Orbit  │ │ MC Sim    │ │
│  │& Search  │ │3D Trajectory │ │  Multi-   │ │Explorer │ │ Analysis  │ │
│  │Filters   │ │Velocity Chart│ │  Event    │ │Solar Sys│ │ σ Bounds  │ │
│  └──────────┘ └──────────────┘ └──────────┘ └─────────┘ └───────────┘ │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌─────────┐               │
│  │ Radiant  │ │  Live Feed   │ │  Fall     │ │ Physics │               │
│  │ Sky Map  │ │  AMS Ticker  │ │ Predictor │ │ Engine  │               │
│  └──────────┘ └──────────────┘ └──────────┘ └─────────┘               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Ingestion Pipeline

BOLIDE's trustworthiness begins at the data layer. **Zero synthetic data. Zero simulations. Every number traces back to a real photon hitting a real camera sensor.**

| Source | Ingester | Events | What We Extract |
|--------|----------|--------|-----------------|
| **Global Meteor Network** | `gmn_ingester.py` | 33 multi-station events | Per-station RA/Dec observation CSVs, station lat/lon/alt, timestamps, 3–6 cameras per event |
| **NASA JPL Fireball API** | `nasa_ingester.py` | 150+ bolides | Impact energy (kT), velocity, lat/lon, altitude, peak brightness |
| **NASA All-Sky Fireball Network** | `nasa_ingester.py` | 40+ events | Calibrated fireball astrometry, multi-station detections |
| **FRIPON (France)** | `nasa_ingester.py` | 30+ events | High-precision European network data, calibrated astrometry |
| **American Meteor Society** | `nasa_ingester.py` | 65+ events | Citizen-reported fireballs, magnitudes, witness locations |
| **IAU Meteor Data Centre** | `iau_ingester.py` | 1,100+ showers | Official shower radiant catalogue for association matching |

### Ingestion Flow

```
1. FETCH      Raw CSVs / JSON from public URLs & APIs
                    │
2. PARSE      Extract station metadata, observation angles, timestamps
                    │
3. NORMALIZE  Convert all events to unified schema:
              { event_id, metadata, stations[], observations[] }
                    │
4. VALIDATE   Check for ≥2 stations, valid coordinates, time coverage
                    │
5. STORE      Write to disk-backed JSON object store with indexed lookups
                    │
6. CACHE      Trajectory results cached per-event for instant retrieval
```

---

## 🖥️ Application Features

### 🗂️ 1. Event Catalogue & Search (`/`)

The mission control for the unified observation catalog.

- **420+ authentic events** from 5 global networks — no manual file upload required
- **Real-time filters**: network (GMN / NASA / FRIPON / AMS), meteor shower (Geminids, Perseids, Leonids, etc.), free-text search
- **Event cards** display: UTC timestamp, station count, peak magnitude, entry velocity, shower association, and a deterministic SVG sky-map thumbnail
- **Network distribution chart**: live bar graph showing event distribution across sources
- **Quality indicators**: High (multi-station) / Med (single w/ velocity) / Est (estimated)

### 🔬 2. Trajectory Reconstruction (`/event/[id]`)

The core investigative interface — every number computed server-side, rendered client-side.

- **3 interactive trajectory views**: SVG-rendered 3D Globe, Ground Track projection, Lines-of-Sight intersection
- **Velocity deceleration chart**: real data points plotted against Linear and Whipple-Jacchia exponential fits, togglable
- **5 stat cards**: initial velocity (± uncertainty), entry angle, peak magnitude, trajectory length, shower match
- **Station panel**: per-station angular residuals in arcseconds, frame counts, geographic coordinates
- **Heliocentric orbit diagram**: SVG rendering of the reconstructed Keplerian orbit relative to Earth
- **Orbital elements**: semi-major axis (AU), eccentricity, inclination, perihelion distance, Tisserand parameter
- **Quality score**: composite 0–100 score translating Q-angle, residuals, and station geometry into plain English
- **Event switcher**: quick-jump dropdown to navigate between events without returning to catalogue

### 🌐 3. Sky Radiant Analysis (`/radiant`)

- **All-sky radiant map**: every event's radiant direction plotted on a celestial coordinate projection
- **Shower clustering**: identified showers highlighted with distinct colors and counts
- **Radiant distribution stats**: total reconstructed events, valid LoS intersections, shower association rate

### ☀️ 4. Solar System Orbit Explorer (`/orbit`)

- **Heliocentric kinematics**: browse computed orbital elements for every event
- **Interactive cards**: click any event to jump to its full trajectory and orbital analysis
- **Orbit classification**: bound, parabolic, or hyperbolic orbits automatically flagged via `orbit_type`

### 🔄 5. Multi-Event Comparison (`/compare`)

- **Side-by-side analysis**: select 2–5 events for simultaneous comparison
- **Shared sky map**: overlaid radiant positions on a celestial coordinate projection
- **Orbital elements table**: tabular comparison of a, e, i, ω, Ω across events
- **Velocity overlay**: normalized deceleration curves on a single chart
- **Automatic shower association**: cross-reference against IAU meteor shower catalogue

### 🎲 6. Monte Carlo Simulation (`/montecarlo`)

- **100-iteration perturbation engine**: injects Gaussian noise (σ = 30 arcsec) into RA/Dec inputs
- **Re-runs the entire pipeline** for each iteration — triangulation, velocity, orbit
- **Output**: velocity σ, radiant area (deg²), RA/Dec uncertainty bounds
- **Available for any multi-station event** — select from catalogue and run

### 🌠 7. Live Feed (`/` sidebar)

- **Real-time AMS fireball ticker**: latest reported events from the American Meteor Society API
- **Prioritized display**: multi-station events with magnitude and shower data shown first
- **Continuous updates**: latest AMS-reported fireballs streamed into the sidebar panel

### 📐 8. Physics Engine Reference (`/physics`)

- **Transparent mathematics notebook**: every equation, every coordinate transform, every derivation
- **Interactive SVD demo**: animated visualization of how multi-station rays converge
- **Whipple-Jacchia profile**: animated deceleration curve showing exponential atmospheric drag
- **Orbital mechanics**: heliocentric state vector composition with live orbit animation

---

## 🔬 The Scientific Pipeline

We **did not** delegate the core math to black-box libraries. The entire physics engine is hand-built in NumPy and SciPy.

### Step 1 — Coordinate Transforms (`coordinates.py`)
- Geographic (φ, λ, h) → **ECEF** via WGS-84 ellipsoid (a = 6,378,137 m, f = 1/298.257)
- ECEF → **ECI J2000** via Greenwich Mean Sidereal Time rotation
- RA/Dec celestial angles → **unit direction vectors** in the terrestrial frame
- ECI → **Heliocentric Ecliptic** via obliquity rotation (ε = 23.4393°)

### Step 2 — 3D Triangulation (`triangulation.py`)
- **Line-of-Sight least-squares** via SVD: builds overdetermined system AX = B from multi-station rays
- **RANSAC outlier rejection**: discards > 3σ angular residuals (cosmic rays, aircraft, tracking glitches)
- Computes: trajectory direction, start point, entry angle, per-station residuals, convergence angle Q
- Entry/terminal altitudes extracted via Earth intersection geometry

### Step 3 — Velocity Fitting (`velocity.py`)
- Projects observations onto trajectory axis for **distance-along-track vs. time**
- **Linear deceleration model**: v(t) = v₀ + at (baseline)
- **Whipple-Jacchia exponential drag**: v(s) = v∞ exp(-K ∫ρ(h)ds') via Nelder-Mead optimization
- Velocity capped at 72 km/s (physical maximum for Earth-bound meteors)
- Sanity check: falls back to metadata velocity when fit χ² is extreme

### Step 4 — Timing Offset Estimation (`timing.py`)
- Inter-station clock drift treated as **free parameters**
- Estimates offsets by minimizing residuals between observed and predicted positions
- Critical for accuracy: 20 ms offset at 25 km/s = 500 m positional error

### Step 5 — Orbital Elements (`orbit.py`)
- **Diurnal aberration correction**: remove Earth's rotation effect on apparent radiant
- **Zenith attraction correction**: v\_geo = √(v∞² + v\_esc²), radiant shifted toward zenith
- Geocentric velocity vector → **heliocentric state vector** using Earth's orbital velocity
- **Vis-viva equation**: semi-major axis from specific orbital energy
- Full Keplerian elements: a, e, i, ω, Ω, q, Q, Tisserand parameter

### Step 6 — Shower Association (`shower.py`)
- Cross-references radiant RA/Dec against **1,100+ IAU Meteor Data Centre showers**
- Angular separation + velocity matching within solar longitude windows
- Confidence score based on proximity to shower reference radiant

### Step 7 — Monte Carlo Uncertainty (`montecarlo.py`)
- **100 iterations** with σ = 30 arcsec Gaussian perturbation on input RA/Dec
- Full pipeline re-execution per iteration
- Statistical output: 1σ confidence bounds on velocity, radiant, orbital elements

### Step 8 — Stretch: Fall Prediction (`fall_predictor.py`)
- For events where terminal velocity < 5 km/s (potential meteorite survival)
- Computes ground impact point and strewn-field ellipse
- Accounts for wind drift and atmospheric density profile

### Step 9 — Stretch: Mass Estimate (`mass_estimate.py`)
- Luminous efficiency relation applied to magnitude time series
- Estimates initial meteoroid mass from observed brightness curve

### Step 10 — Quality Scoring (`quality.py`)
- Composite 0–100 score from: convergence angle Q, median residuals, station count, timing quality
- Human-readable labels: Excellent / Good / Fair / Poor
- Transparent breakdown exposed to user in event detail panel

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ with `pip`
- Node.js 18+ with `npm`

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

---

## 📁 Project Structure

```
Astrothon/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── analysis.py            # Core trajectory analysis endpoint
│   │   ├── catalogue.py           # Event listing & search API
│   │   ├── comparison.py          # Multi-event comparison API
│   │   └── livefeed.py            # Live AMS feed + stats API
│   ├── data/
│   │   ├── gmn_ingester.py        # Global Meteor Network data parser
│   │   ├── nasa_ingester.py       # NASA JPL + AFSN + FRIPON + AMS ingester
│   │   ├── iau_ingester.py        # IAU shower catalogue ingester
│   │   └── store.py               # Unified JSON object store
│   └── physics/
│       ├── coordinates.py         # WGS84, ECEF, ECI, ecliptic transforms
│       ├── triangulation.py       # SVD Line-of-Sight triangulation + RANSAC
│       ├── velocity.py            # Linear + Whipple-Jacchia fitting
│       ├── timing.py              # Inter-station clock offset estimation
│       ├── orbit.py               # Heliocentric Keplerian elements
│       ├── montecarlo.py          # Monte Carlo uncertainty engine
│       ├── shower.py              # IAU shower association matching
│       ├── quality.py             # Composite quality scoring
│       ├── fall_predictor.py      # Meteorite strewn-field computation
│       └── mass_estimate.py       # Luminous efficiency mass estimate
├── frontend/
│   └── src/app/
│       ├── page.tsx               # Catalogue + Live Feed dashboard
│       ├── event/[id]/page.tsx    # Full event reconstruction viewer
│       ├── compare/page.tsx       # Multi-event comparison tool
│       ├── orbit/page.tsx         # Solar System orbit explorer
│       ├── radiant/page.tsx       # Sky radiant analysis map
│       ├── montecarlo/page.tsx    # Monte Carlo simulation interface
│       ├── fall/page.tsx          # Meteorite fall predictor
│       ├── physics/page.tsx       # Physics engine reference
│       └── diagnostics/page.tsx   # Developer diagnostics
└── data/events/                   # Ingested event data store
```

---

## 🏆 Hackathon Compliance

| Requirement | Status | Details |
|-------------|--------|---------|
| Real open data (≥2 sources) | ✅ | 5 sources: GMN, NASA JPL, NASA AFSN, FRIPON, AMS |
| 100+ events accessible | ✅ | **420+ events** across 5 networks |
| Custom 3D triangulation | ✅ | SVD LoS least-squares in `triangulation.py` |
| Custom velocity fitting | ✅ | Linear + Whipple-Jacchia in `velocity.py` |
| No black-box solvers | ✅ | All core geometry hand-built in NumPy/SciPy |
| Server-side computation | ✅ | All physics via FastAPI; browser only renders |
| Timing offset handling | ✅ | Free parameter estimation in `timing.py` |
| Angular residuals exposed | ✅ | Per-station arcsecond residuals in UI |
| Monte Carlo uncertainty | ✅ | 100 iterations, σ = 30″, 1σ bounds |
| Multi-event comparison | ✅ | `/compare` with shared sky map + velocity overlay |
| Shower association (IAU) | ✅ | 1,100+ showers from IAU MDC catalogue |
| **Stretch**: Meteorite fall | ✅ | Fall candidate identification + strewn-field computation |
| **Stretch**: Real-time feed | ✅ | AMS fireball API live integration |
| **Stretch**: Mass estimate | ✅ | Luminous efficiency computation |

---

## 🔭 Non-Negotiable Compliance

> ✅ **"The core geometry — 3D triangulation and velocity/deceleration fitting — must be implemented by your team using foundational libraries (NumPy, SciPy)."**

Every line of the triangulation matrix assembly, SVD decomposition, RANSAC rejection loop, Whipple-Jacchia exponential integral, and Keplerian state vector algebra is written by our team. No WesternMeteorPyLib. No black-box solvers. Complete source transparency.

> ✅ **"All computation runs server-side. The browser renders results — it does not run the physics."**

The Next.js frontend makes API calls to the FastAPI backend. All `numpy`, `scipy`, and coordinate math runs in Python. The browser receives JSON and renders SVGs.

---

<p align="center">
  <strong>B O L I D E</strong><br/>
  <i>Because every streak of light has a story — and it deserves to be told.</i>
</p>
