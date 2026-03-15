"""
BOLIDE — Multi-event comparison API.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import logging

from backend.data.store import get_trajectory_cache, get_event, save_trajectory_cache

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["comparison"])


class CompareRequest(BaseModel):
    event_ids: List[str]


@router.post("/compare")
async def compare_events(req: CompareRequest):
    """Compare multiple meteor events side by side."""
    if len(req.event_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 events to compare")
    if len(req.event_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 events")

    results = []
    for eid in req.event_ids:
        event = get_event(eid)
        if event is None:
            continue

        # Try cache first, otherwise run reconstruction on-the-fly
        cache = get_trajectory_cache(eid)
        if cache is None:
            try:
                from backend.api.analysis import _run_reconstruction
                log.info(f"Compare: running reconstruction for {eid}")
                cache = _run_reconstruction(event)
                save_trajectory_cache(eid, cache)
            except Exception as e:
                log.error(f"Compare: reconstruction failed for {eid}: {e}")
                cache = {}

        results.append({
            "event_id": eid,
            "metadata": event.get("metadata", {}),
            "trajectory": cache.get("trajectory", {}),
            "velocity": cache.get("velocity", {}),
            "orbital_elements": cache.get("orbital_elements", {}),
            "radiant": cache.get("radiant", {}),
            "shower_match": cache.get("shower_match"),
            "quality": cache.get("quality", {}),
        })

    return {"events": results, "count": len(results)}

