"""
BOLIDE — Multi-event comparison API.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from backend.data.store import get_trajectory_cache, get_event

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
        cache = get_trajectory_cache(eid)
        results.append({
            "event_id": eid,
            "metadata": event.get("metadata", {}),
            "trajectory": cache.get("trajectory", {}) if cache else {},
            "velocity": cache.get("velocity", {}) if cache else {},
            "orbital_elements": cache.get("orbital_elements", {}) if cache else {},
            "radiant": cache.get("radiant", {}) if cache else {},
            "shower_match": cache.get("shower_match") if cache else None,
            "quality": cache.get("quality", {}) if cache else {},
        })

    return {"events": results, "count": len(results)}
