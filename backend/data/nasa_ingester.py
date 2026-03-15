import urllib.request
import json
import uuid
import datetime
from backend.data.store import save_event

def fetch_nasa_fireballs(limit=150):
    url = f"https://ssd-api.jpl.nasa.gov/fireball.api?limit={limit}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla'})
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed to fetch NASA Fireballs: {e}")
        return 0
        
    fields = data.get("fields", [])
    events = data.get("data", [])
    
    count = 0
    for row in events:
        evt = dict(zip(fields, row))
        
        event_id = f"NASA_JPL_{evt.get('date', '').replace(' ', '_').replace(':', '')}"
        utc_stamp = evt.get('date', '').replace(' ', 'T')
        lat = evt.get('lat', '')
        lon = evt.get('lon', '')
        alt = evt.get('alt', '')
        if lat and evt.get('lat-dir') == 'S': lat = f"-{lat}"
        if lon and evt.get('lon-dir') == 'W': lon = f"-{lon}"
        
        # We don't have multi-station RA/Dec for NASA events, so we store them as single-station "summary" events
        metadata = {
            "event_id": event_id,
            "utc_timestamp": utc_stamp,
            "network": "NASA_JPL_Fireball",
            "station_count": 1,
            "shower": "Sporadic",
            "lat": float(lat) if lat else None,
            "lon": float(lon) if lon else None,
            "alt": float(alt) if alt else None,
            "velocity": float(evt.get('vel', 0)) if evt.get('vel') else None,
            "energy_kt": float(evt.get('impact-e', 0)) if evt.get('impact-e') else None,
            "status": "summary_only"
        }
        
        stations = [
            {
                "station_id": "JPL_SATELLITE",
                "lat": float(lat) if lat else 0,
                "lon": float(lon) if lon else 0,
                "elevation": 100000,
                "camera_fov": "sky"
            }
        ]
        
        observations = [] # NASA doesn't dump per-frame RA/Dec via this API
        
        save_event(event_id, metadata, stations, observations)
        count += 1
        
    print(f"Ingested {count} real NASA fireballs.")
    return count

if __name__ == "__main__":
    fetch_nasa_fireballs()
