import json
import pathlib
import sys
import os

# Put this repo in path to import backend configs
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from backend.config import REFERENCE_DIR

def parse_iau_showers():
    txt_path = pathlib.Path(r"c:\Users\ojasv\Desktop\Astrothon\iau showers list.txt")
    if not txt_path.exists():
        print(f"Error: Could not find '{txt_path}'")
        return
        
    showers = []
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(':'):
                continue
                
            parts = [p.strip().replace('"', '') for p in line.split('|')]
            if len(parts) < 16:
                continue
                
            code = parts[3]
            name = parts[6]
            
            try:
                # Some fields might be empty or invalid floats
                ra = float(parts[11]) if parts[11].strip() else None
                dec = float(parts[12]) if parts[12].strip() else None
                vg = float(parts[15]) if parts[15].strip() else None
                
                start_sol = float(parts[8]) if parts[8].strip() else None
                end_sol = float(parts[9]) if parts[9].strip() else None
                peak_sol = float(parts[10]) if parts[10].strip() else None
                
                # We need all these for matching
                if None in (ra, dec, vg, start_sol, end_sol, peak_sol):
                    continue
                    
                showers.append({
                    "code": code,
                    "name": name,
                    "ra": ra,
                    "dec": dec,
                    "v_g": vg,
                    "start_sol": start_sol,
                    "end_sol": end_sol,
                    "peak_sol": peak_sol
                })
            except ValueError:
                continue

    output_path = REFERENCE_DIR / "iau_showers.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(showers, f, indent=2)
        
    print(f"Successfully parsed {len(showers)} meteor showers into {output_path}")

if __name__ == "__main__":
    parse_iau_showers()
