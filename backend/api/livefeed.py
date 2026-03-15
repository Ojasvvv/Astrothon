"""
BOLIDE — Live feed & stats API (stretch feature).
"""
from __future__ import annotations
from fastapi import APIRouter
from backend.data.store import list_events, get_network_stats, get_shower_stats

router = APIRouter(prefix="/api", tags=["livefeed"])


@router.get("/livefeed")
async def get_livefeed():
    """Get recent fireball events (simulated live feed)."""
    recent = list_events(page=1, page_size=10)
    feed_items = []
    for event in recent.get("events", []):
        feed_items.append({
            "event_id": event["event_id"],
            "utc_timestamp": event.get("utc_timestamp", ""),
            "region": event.get("region", "Unknown"),
            "network": event.get("network", ""),
            "peak_magnitude": event.get("peak_magnitude", 0),
            "estimated_velocity_kms": event.get("estimated_velocity_kms", 0),
            "station_count": event.get("station_count", 0),
        })
    return {"feed": feed_items, "total": recent.get("total", 0)}


@router.get("/stats")
async def get_stats():
    """Get aggregate statistics."""
    all_events = list_events(page=1, page_size=9999)
    total = all_events["total"]
    events = all_events["events"]

    fireballs = sum(1 for e in events if e.get("peak_magnitude", 0) < -4)

    return {
        "total_events": total,
        "fireballs": fireballs,
        "networks": get_network_stats(),
        "showers": get_shower_stats(),
        "hourly_rate": max(1, total // 24),
    }
