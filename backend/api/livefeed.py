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
    recent = list_events(page=1, page_size=50)
    all_events = recent.get("events", [])
    # Sort: prioritize events with real data (magnitude, region, multi-station)
    all_events.sort(key=lambda e: (
        -(e.get("station_count", 0)),  # more stations first
        0 if e.get("peak_magnitude") is not None else 1,  # has magnitude first
        0 if e.get("region") and e.get("region") != "Unknown" else 1,  # has region first
    ))
    feed_items = []
    for event in all_events[:10]:
        feed_items.append({
            "event_id": event["event_id"],
            "utc_timestamp": event.get("utc_timestamp", ""),
            "region": event.get("region") or "Unknown",
            "network": event.get("network", ""),
            "peak_magnitude": event.get("peak_magnitude"),
            "estimated_velocity_kms": event.get("estimated_velocity_kms"),
            "station_count": event.get("station_count", 0),
            "shower": event.get("shower", "Sporadic"),
        })
    return {"feed": feed_items, "total": recent.get("total", 0)}


@router.get("/stats")
async def get_stats():
    """Get aggregate statistics."""
    all_events = list_events(page=1, page_size=9999)
    total = all_events["total"]
    events = all_events["events"]

    fireballs = sum(1 for e in events if e.get("peak_magnitude", 0) < -4)

    showers = get_shower_stats()
    non_sporadic = sum(v for k, v in showers.items() if k.lower() != "sporadic" and k.lower() != "unknown")
    shower_pct = round(100 * non_sporadic / max(total, 1), 1)
    with_radiant = sum(1 for e in events if e.get("radiant_ra") is not None)

    return {
        "total_events": total,
        "fireballs": fireballs,
        "networks": get_network_stats(),
        "showers": showers,
        "hourly_rate": max(1, total // 24),
        "shower_percentage": shower_pct,
        "total_with_radiant": with_radiant,
    }
