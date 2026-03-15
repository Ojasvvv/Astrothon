"""
BOLIDE — Event catalogue API endpoints.
"""
from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from backend.data.store import list_events, get_event

router = APIRouter(prefix="/api", tags=["catalogue"])


@router.get("/events")
async def get_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    network: Optional[str] = None,
    shower: Optional[str] = None,
    min_velocity: Optional[float] = None,
    max_velocity: Optional[float] = None,
    search: Optional[str] = None,
    region: Optional[str] = None,
):
    """Paginated event catalogue with filters."""
    return list_events(
        page=page,
        page_size=page_size,
        network=network,
        shower=shower,
        min_velocity=min_velocity,
        max_velocity=max_velocity,
        search=search,
        region=region,
    )


@router.get("/events/{event_id}")
async def get_event_detail(event_id: str):
    """Full event data including cached trajectory."""
    data = get_event(event_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
    return data
