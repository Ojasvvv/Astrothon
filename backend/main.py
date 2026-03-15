"""
BOLIDE — FastAPI application entry point.
"""
from __future__ import annotations
import sys, os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import CORS_ORIGINS
from backend.api.catalogue import router as catalogue_router
from backend.api.analysis import router as analysis_router
from backend.api.comparison import router as comparison_router
from backend.api.livefeed import router as livefeed_router

app = FastAPI(
    title="BOLIDE — Meteor Trajectory Reconstruction",
    description="Scientific platform for multi-station meteor trajectory reconstruction",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(catalogue_router)
app.include_router(analysis_router)
app.include_router(comparison_router)
app.include_router(livefeed_router)


@app.get("/")
async def root():
    return {
        "name": "BOLIDE",
        "description": "Meteor Trajectory Reconstruction Platform",
        "version": "1.0.0",
        "endpoints": {
            "catalogue": "/api/events",
            "event_detail": "/api/events/{event_id}",
            "reconstruct": "/api/events/{event_id}/reconstruct (POST)",
            "trajectory": "/api/events/{event_id}/trajectory",
            "orbit": "/api/events/{event_id}/orbit",
            "montecarlo": "/api/events/{event_id}/montecarlo (POST)",
            "residuals": "/api/events/{event_id}/residuals",
            "compare": "/api/compare (POST)",
            "livefeed": "/api/livefeed",
            "stats": "/api/stats",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    """Fetch real data if no events exist."""
    from backend.data.store import get_event_ids
    if len(get_event_ids()) == 0:
        print("No events found. Fetching real NASA Fireball datasets...")
        from backend.data.nasa_ingester import fetch_nasa_fireballs
        count = fetch_nasa_fireballs(150)
        print(f"Ingested {count} real events from NASA.")
