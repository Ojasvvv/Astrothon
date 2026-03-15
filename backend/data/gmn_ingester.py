import os
import sys
import pathlib
import datetime
from backend.data.store import save_event

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from backend.physics.shower import match_shower

def parse_gmn_summary(limit=150):
    txt_path = pathlib.Path(r"c:\Users\ojasv\Desktop\Astrothon\summary.txt")
    if not txt_path.exists():
        print(f"Error: Could not find '{txt_path}'")
        return 0
        
    count = 0
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            if count >= limit:
                break
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = [p.strip() for p in line.split(';')]
            if len(parts) < 85:
                continue
                
            event_id = f"GMN_{parts[0]}"
            utc_stamp = parts[2].replace(' ', 'T')
            
            shower_code = parts[4]
            shower_name = "Sporadic" if shower_code in ('...', '-1', '') else shower_code
            
            try:
                # Basic parsing
                vgeo = float(parts[15]) if parts[15] else None
                vinit = float(parts[57]) if parts[57] else None
                lat_beg = float(parts[61]) if parts[61] else None
                lon_beg = float(parts[63]) if parts[63] else None
                ht_beg = float(parts[65]) if parts[65] else None
                duration = float(parts[73]) if parts[73] else None
                peak_mag = float(parts[74]) if parts[74] else None
                
                # RA/Dec and Sol
                ra = float(parts[7]) if parts[7] else None
                dec = float(parts[9]) if parts[9].strip() != 'nan' else None
                sol_lon = float(parts[5]) if parts[5] else None
                
                # Attempt to get shower name from physics match_shower if available
                if ra is not None and dec is not None and vgeo is not None and sol_lon is not None:
                    jd = float(parts[1]) if parts[1] else 2451545.0
                    match = match_shower(ra, dec, vgeo, jd)
                    if match:
                        shower_name = match["shower_name"]
                        shower_code = match["shower_code"]
                
                stations_str = parts[85] if len(parts) > 85 else ""
                station_names = [s.strip() for s in stations_str.split(',') if s.strip()]
                
                metadata = {
                    "event_id": event_id,
                    "utc_timestamp": utc_stamp,
                    "network": "Global Meteor Network",
                    "station_count": len(station_names) or int(parts[84] or 1),
                    "shower": shower_name,
                    "shower_code": shower_code,
                    "lat": lat_beg,
                    "lon": lon_beg,
                    "alt": ht_beg * 1000 if ht_beg else None, # km to m
                    "velocity": vinit * 1000 if vinit else None, # km/s to m/s
                    "estimated_velocity_kms": vinit,
                    "duration": duration,
                    "peak_mag": peak_mag,
                    "status": "summary_only"
                }
                
                stations = []
                for sname in station_names:
                    stations.append({
                        "station_id": sname,
                        "lat": lat_beg, # Approximate since we don't have station exact coords
                        "lon": lon_beg,
                        "elevation": 100,
                        "camera_fov": "sky"
                    })
                    
                observations = []
                
                # Try to synthesize some basic observation frames if we want it to run in the engine
                # For now just save summary structure
                save_event(event_id, metadata, stations, observations)
                count += 1
                
            except Exception as e:
                print(f"Skipping line due to error: {e}")
                continue

    print(f"Ingested {count} real GMN trajectories.")
    return count

if __name__ == "__main__":
    parse_gmn_summary()
