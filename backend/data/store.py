"""
BOLIDE — JSON file store for event data.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.config import EVENTS_DIR


def list_events(
    page: int = 1,
    page_size: int = 20,
    network: Optional[str] = None,
    shower: Optional[str] = None,
    min_velocity: Optional[float] = None,
    max_velocity: Optional[float] = None,
    search: Optional[str] = None,
    region: Optional[str] = None,
) -> Dict[str, Any]:
    """List events with pagination and filters."""
    events = []
    if not EVENTS_DIR.exists():
        return {"events": [], "total": 0, "page": page, "page_size": page_size}

    all_metas = []
    for event_dir in EVENTS_DIR.iterdir():
        if not event_dir.is_dir():
            continue
        meta_file = event_dir / "metadata.json"
        if not meta_file.exists():
            continue
        try:
            with open(meta_file) as f:
                meta = json.load(f)
        except Exception:
            continue
        all_metas.append(meta)

    # Sort by timestamp (newest first)
    all_metas.sort(key=lambda m: m.get("utc_timestamp", ""), reverse=True)

    for meta in all_metas:
        # Apply filters
        if network and meta.get("network", "").upper() != network.upper():
            continue
        if shower and shower.lower() != "all":
            if meta.get("shower", "").lower() != shower.lower() and \
               meta.get("shower_code", "").lower() != shower.lower():
                continue
        if min_velocity and meta.get("estimated_velocity_kms", 0) < min_velocity:
            continue
        if max_velocity and meta.get("estimated_velocity_kms", 999) > max_velocity:
            continue
        if region and region.lower() not in meta.get("region", "").lower():
            continue
        if search:
            s = search.lower()
            searchable = f"{meta.get('event_id', '')} {meta.get('shower', '')} {meta.get('region', '')} {meta.get('network', '')}".lower()
            if s not in searchable:
                continue

        events.append(meta)

    total = len(events)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "events": events[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def get_event(event_id: str) -> Optional[Dict[str, Any]]:
    """Load full event data."""
    event_dir = EVENTS_DIR / event_id
    if not event_dir.exists():
        return None

    data = {}
    for fname in ["metadata.json", "stations.json", "observations.json", "trajectory_cache.json"]:
        fpath = event_dir / fname
        if fpath.exists():
            with open(fpath) as f:
                data[fname.replace(".json", "")] = json.load(f)

    return data


def save_trajectory_cache(event_id: str, cache: Dict[str, Any]):
    """Save computed trajectory results."""
    event_dir = EVENTS_DIR / event_id
    event_dir.mkdir(parents=True, exist_ok=True)
    with open(event_dir / "trajectory_cache.json", "w") as f:
        json.dump(cache, f, indent=2)


def get_trajectory_cache(event_id: str) -> Optional[Dict[str, Any]]:
    """Load cached trajectory results."""
    cache_file = EVENTS_DIR / event_id / "trajectory_cache.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return None


def get_event_ids() -> List[str]:
    """List all event IDs."""
    if not EVENTS_DIR.exists():
        return []
    return sorted([d.name for d in EVENTS_DIR.iterdir() if d.is_dir()])

def save_event(event_id: str, metadata: dict, stations: list, observations: list):
    """Save an event struct to disk."""
    event_dir = EVENTS_DIR / event_id
    event_dir.mkdir(parents=True, exist_ok=True)
    with open(event_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    with open(event_dir / "stations.json", "w") as f:
        json.dump(stations, f, indent=2)
    with open(event_dir / "observations.json", "w") as f:
        json.dump(observations, f, indent=2)


def get_network_stats() -> Dict[str, int]:
    """Count events per network."""
    stats = {}
    for eid in get_event_ids():
        meta_file = EVENTS_DIR / eid / "metadata.json"
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
            net = meta.get("network", "Unknown")
            stats[net] = stats.get(net, 0) + 1
    return stats


def get_shower_stats() -> Dict[str, int]:
    """Count events per shower."""
    stats = {}
    for eid in get_event_ids():
        meta_file = EVENTS_DIR / eid / "metadata.json"
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
            shower_name = meta.get("shower", "Unknown")
            stats[shower_name] = stats.get(shower_name, 0) + 1
    return stats
