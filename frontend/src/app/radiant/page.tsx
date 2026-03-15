"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SkyRadiantPage() {
  const [stats, setStats] = useState<any>({});
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${API}/api/stats`).then(r => r.json()).then(d => setStats(d)).catch(() => {});
    fetch(`${API}/api/events?page_size=120`).then(r => r.json()).then(d => setEvents(d.events || [])).catch(() => {});
  }, []);

  return (
    <div style={{display:"flex", flexDirection:"column", gap: 20}}>
      <div className="sec-head">
        <div className="sec-title">Sky Radiant Analysis</div>
        <div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--accent2)"}}>GLOBAL METEOR SHOWER DOMAINS</div>
      </div>

      {/* Main Map Panel */}
      <div className="panel" style={{marginBottom: 16}}>
        <div className="ph" style={{"--al":"var(--accent2)"} as any}>
          <div className="pt">Composite Radiant Map · Equatorial J2000</div>
        </div>
        <div style={{padding: 20, display: "flex", justifyContent: "center", background:"#030712"}}>
          <svg width="100%" height="auto" viewBox="0 0 800 400" style={{maxWidth: 800}}>
            <rect width="800" height="400" rx="4" fill="rgba(8,13,26,0.3)" />
            
            {/* Grid Lines */}
            <path d="M 400 20 L 400 380 M 100 200 L 700 200" stroke="rgba(255,255,255,0.15)" strokeWidth="1" strokeDasharray="4 4"/>
            <ellipse cx="400" cy="200" rx="300" ry="150" fill="none" stroke="rgba(255,255,255,.2)" strokeWidth="1" />
            <ellipse cx="400" cy="200" rx="150" ry="150" fill="none" stroke="rgba(255,255,255,.05)" strokeWidth="1" />
            
            {/* Events */}
            {(events || []).map((ev: any, i: number) => {
              if (ev.radiant_ra === null || ev.radiant_dec === null) return null;
              // Mollweide-ish projection
              const ra = ev.radiant_ra;
              const dec = ev.radiant_dec;
              
              // Map RA [0, 360] -> [700, 100] (0 is right, 360 is left)
              // Map Dec [-90, 90] -> [350, 50] (+90 is top, -90 is bottom)
              
              const dx = (180 - ra) / 180; // [-1, 1]
              const dy = dec / 90; // [-1, 1]
              
              // Scale dx by cos(dec) to create ellipse shape
              const rCurve = Math.sqrt(1 - dy*dy);
              const cx = 400 + (300 * dx * rCurve);
              const cy = 200 - (150 * dy);

              const isSporadic = !ev.shower || ev.shower === "Sporadic";
              const color = isSporadic ? "#facc15" : "var(--accent2)";
              
              return (
                <g key={ev.event_id}>
                  <circle cx={cx} cy={cy} r={isSporadic ? 2.5 : 4} fill={color} opacity={isSporadic ? 0.4 : 0.9} />
                  {!isSporadic && (
                    <circle cx={cx} cy={cy} r={8} fill="none" stroke={color} strokeWidth="1" opacity={0.3} />
                  )}
                </g>
              );
            })}
            
            {/* Axis Labels */}
            <text x="50" y="204" fill="rgba(255,255,255,.4)" fontSize="12" fontFamily="'Space Mono',monospace" textAnchor="middle">24h</text>
            <text x="750" y="204" fill="rgba(255,255,255,.4)" fontSize="12" fontFamily="'Space Mono',monospace" textAnchor="middle">0h</text>
            <text x="400" y="15" fill="rgba(255,255,255,.4)" fontSize="12" fontFamily="'Space Mono',monospace" textAnchor="middle">+90°</text>
            <text x="400" y="395" fill="rgba(255,255,255,.4)" fontSize="12" fontFamily="'Space Mono',monospace" textAnchor="middle">-90°</text>
            
            {/* Legend */}
            <rect x="20" y="350" width="140" height="40" rx="4" fill="rgba(0,0,0,0.5)" />
            <circle cx="35" cy="362" r="4" fill="var(--accent2)" />
            <text x="45" y="366" fill="#fff" fontSize="10" fontFamily="var(--mono)">Identified Shower</text>
            <circle cx="35" cy="378" r="2.5" fill="#facc15" opacity="0.6"/>
            <text x="45" y="382" fill="#fff" fontSize="10" fontFamily="var(--mono)">Sporadic (Background)</text>
          </svg>
        </div>
      </div>

      <div style={{display:"grid",gap:16,gridTemplateColumns:"1fr 1fr"}}>
        <div className="panel" style={{marginBottom: 0}}>
          <div className="ph" style={{"--al":"var(--accent)"} as any}>
            <div className="pt">Identified Showers ({Object.keys(stats.showers || {}).length})</div>
          </div>
          <div style={{padding: 20}}>
            {Object.entries(stats.showers || {})
              .sort((a: any, b: any) => b[1] - a[1]) // Sort by count desc
              .map(([name, count]: [string, any]) => (
              <div key={name} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"12px 0",borderBottom:"1px solid var(--cb)"}}>
                <div style={{display:"flex",alignItems:"center",gap:10}}>
                  <div style={{width:8,height:8,borderRadius:4,background:"var(--accent2)"}} />
                  <span style={{color:"var(--tx)", fontWeight:500}}>{name}</span>
                </div>
                <div style={{display:"flex", alignItems:"center", gap: 10}}>
                  <div style={{width: 100, height: 4, background:"var(--cb)", borderRadius:2, overflow:"hidden"}}>
                    <div style={{width: `${Math.min(100, (count / events.length) * 100 * 5)}%`, height:"100%", background:"var(--accent2)"}}/>
                  </div>
                  <span className="badge bp" style={{width:40,textAlign:"center"}}>{String(count)}</span>
                </div>
              </div>
            ))}
            {Object.keys(stats.showers || {}).length === 0 && <div style={{color:"var(--muted)", fontStyle:"italic"}}>No grouped showers detected yet.</div>}
          </div>
        </div>

        <div className="panel" style={{marginBottom: 0, height:"fit-content"}}>
          <div className="ph" style={{"--al":"#facc15"} as any}>
            <div className="pt">Radiant Distribution</div>
          </div>
          <div style={{padding: 20, display:"flex", flexDirection:"column", gap:15}}>
             <div className="stat-card" style={{background:"rgba(0,0,0,0.2)","--al":"#38bdf8"} as any}>
                <div className="sl">Total Reconstructed</div>
                <div className="sv" style={{fontSize:24,marginTop:5}}>{events.filter(e => e.radiant_ra !== null).length} <span style={{fontSize:12,color:"var(--muted)"}}>of {events.length}</span></div>
                <div className="ss">Events with valid LoS intersection</div>
             </div>
             
             <div className="stat-card" style={{background:"rgba(0,0,0,0.2)","--al":"var(--accent2)"} as any}>
                <div className="sl">Shower Association Rate</div>
                <div className="sv" style={{fontSize:24,marginTop:5}}>{stats.shower_percentage || "0.0"}%</div>
                <div className="ss">Matched via standard IAU radiants</div>
             </div>
             
             <div style={{fontSize:13, color:"var(--dim)", lineHeight:1.6}}>
               Showers are matched using a 3D velocity and angular separation threshold against the IAU working list of meteor showers. Velocity must match within 15%, and angular separation $&lt; 5^\circ$ during the peak date window.
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
