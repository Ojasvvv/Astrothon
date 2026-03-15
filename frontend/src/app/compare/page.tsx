"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ComparePage() {
  const [allEvents, setAllEvents] = useState<any[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/events?page_size=50`)
      .then(r => r.json()).then(d => setAllEvents(d.events || [])).catch(() => {});
  }, []);

  const handleCompare = () => {
    if (selected.length < 2) return;
    setLoading(true);
    fetch(`${API}/api/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_ids: selected }),
    }).then(r => r.json()).then(d => { setComparison(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  const toggle = (id: string) => {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id].slice(0, 5));
  };

  const events = comparison?.events || [];

  const COLORS = ["var(--accent)", "var(--accent2)", "var(--accent3)", "#facc15", "#38bdf8"];

  return (
    <>
      <div className="sec-head">
        <div className="sec-title">Multi-Event Comparison</div>
        <div className="heading-actions">
          <button className="btn btn-accent" onClick={handleCompare}
            disabled={selected.length < 2 || loading}>
            {loading ? "Comparing…" : `Compare ${selected.length} events`}
          </button>
          <Link href="/"><button className="btn btn-ghost">← Catalogue</button></Link>
        </div>
      </div>

      {/* Event Selector */}
      <div style={{display:"flex",gap:8,flexWrap:"wrap",marginBottom:20}}>
        {allEvents.slice(0, 20).map(ev => (
          <button key={ev.event_id}
            className={`filter-chip ${selected.includes(ev.event_id) ? "active" : ""}`}
            onClick={() => toggle(ev.event_id)}
            style={{fontSize:8}}>
            {ev.event_id.substring(0, 20)}
          </button>
        ))}
      </div>

      {comparison && events.length >= 2 && (
        <>
          {/* Sky Map Overlay */}
          <div className="panel" style={{marginBottom:16}}>
            <div className="ph" style={{"--al":"var(--accent2)"} as any}>
              <div className="pt">Radiant Sky Map · Overlay</div>
            </div>
            <div style={{padding:16,display:"flex",justifyContent:"center"}}>
              <svg width="400" height="240" viewBox="0 0 400 240">
                <rect width="400" height="240" rx="8" fill="rgba(8,13,26,.5)" />
                <ellipse cx="200" cy="120" rx="190" ry="110" fill="none" stroke="rgba(255,255,255,.05)" strokeWidth=".5" />
                <ellipse cx="200" cy="120" rx="127" ry="73" fill="none" stroke="rgba(255,255,255,.04)" strokeWidth=".5" />
                <line x1="10" y1="120" x2="390" y2="120" stroke="rgba(255,255,255,.04)" strokeWidth=".5" />
                <line x1="200" y1="10" x2="200" y2="230" stroke="rgba(255,255,255,.04)" strokeWidth=".5" />
                {events.map((ev: any, i: number) => {
                  const ra = ev.radiant?.ra_deg || ev.metadata?.radiant_ra || 0;
                  const dec = ev.radiant?.dec_deg || ev.metadata?.radiant_dec || 0;
                  const cx = 200 + (ra - 180) / 360 * 380;
                  const cy = 120 - dec / 90 * 110;
                  return (
                    <g key={i}>
                      <circle cx={cx} cy={cy} r="8" fill="none" stroke={COLORS[i]} strokeWidth=".8" opacity=".4" />
                      <circle cx={cx} cy={cy} r="5" fill={COLORS[i]} opacity=".85" />
                      <text x={cx + 8} y={cy - 4} fill={COLORS[i]} fontSize="8"
                        fontFamily="'Space Mono',monospace" opacity=".9">
                        {ev.shower_match?.shower_name || ev.metadata?.shower || "SPO"}
                      </text>
                    </g>
                  );
                })}
                <text x="10" y="235" fill="rgba(255,255,255,.18)" fontSize="8" fontFamily="'Space Mono',monospace">RA 360°</text>
                <text x="390" y="235" fill="rgba(255,255,255,.18)" fontSize="8" fontFamily="'Space Mono',monospace" textAnchor="end">RA 0°</text>
              </svg>
            </div>
          </div>

          {/* Orbital Elements Table */}
          <div className="compare-grid" style={{marginBottom:16}}>
            <div className="panel">
              <div className="ph" style={{"--al":"var(--accent3)"} as any}>
                <div className="pt">Orbital Elements</div>
              </div>
              <div style={{padding:8,overflowX:"auto"}}>
                <table className="compare-table">
                  <thead>
                    <tr>
                      <th>Element</th>
                      {events.map((ev: any, i: number) => (
                        <th key={i} style={{color: COLORS[i]}}>{ev.event_id.substring(0, 15)}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ["a (AU)", "semi_major_axis_au"],
                      ["e", "eccentricity"],
                      ["i (°)", "inclination_deg"],
                      ["ω (°)", "argument_of_perihelion_deg"],
                      ["Ω (°)", "longitude_of_ascending_node_deg"],
                      ["q (AU)", "perihelion_distance_au"],
                      ["Tj", "tisserand_parameter"],
                    ].map(([label, key]) => (
                      <tr key={String(key)}>
                        <td style={{color:"var(--muted)"}}>{String(label)}</td>
                        {events.map((ev: any, i: number) => {
                          const val = ev.orbital_elements?.[String(key)];
                          return (
                            <td key={i}>
                              {val !== undefined && val !== null && val !== 0 ? val.toFixed(3) : "N/A"}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Velocity Overlay */}
            <div className="panel">
              <div className="ph" style={{"--al":"var(--accent)"} as any}>
                <div className="pt">Velocity Profiles · Overlay</div>
              </div>
              <div style={{padding:16}}>
                {events.some((ev: any) => ev.velocity?.velocity_profile?.distances_km?.length > 1) ? (
                  <>
                    <svg width="100%" viewBox="0 0 280 120" style={{overflow:"visible"}}>
                  {[0,30,60,90,120].map(y => <line key={y} x1="0" y1={y} x2="280" y2={y} stroke="rgba(255,255,255,.04)" strokeWidth=".5" />)}
                  {events.map((ev: any, i: number) => {
                    const vp = ev.velocity?.velocity_profile;
                    if (!vp?.distances_km?.length) return null;
                    const dists = vp.distances_km;
                    const vels = vp.velocity_observed_kms;
                    const maxD = Math.max(...dists, 1);
                    const maxV = Math.max(...vels, 1);
                    const path = vels.map((v: number, j: number) =>
                      `${j === 0 ? "M" : "L"}${(dists[j]/maxD*276).toFixed(1)},${(120 - v/maxV*110).toFixed(1)}`
                    ).join(" ");
                    return <path key={i} d={path} fill="none" stroke={COLORS[i]} strokeWidth="1.5" opacity=".8" />;
                  })}
                  <text x="0" y="135" fill="rgba(255,255,255,.18)" fontSize="7" fontFamily="'Space Mono',monospace">0 km</text>
                  <text x="280" y="135" fill="rgba(255,255,255,.18)" fontSize="7" fontFamily="'Space Mono',monospace" textAnchor="end">max</text>
                    </svg>
                  </>
                ) : (
                  <div style={{padding:"40px 0",textAlign:"center",fontFamily:"var(--mono)",fontSize:10,color:"var(--dim)"}}>
                    VELOCITY PROFILES N/A FOR SELECTED EVENTS
                  </div>
                )}
                <div style={{display:"flex",gap:12,marginTop:8,flexWrap:"wrap"}}>
                  {events.map((ev: any, i: number) => (
                    <div key={i} style={{display:"flex",alignItems:"center",gap:4}}>
                      <span style={{width:8,height:3,borderRadius:2,background:COLORS[i]}} />
                      <span style={{fontFamily:"var(--mono)",fontSize:7,color:"var(--muted)"}}>
                        {ev.event_id.substring(0, 12)} ({ev.velocity?.initial_velocity_kms?.toFixed(1) || "—"} km/s)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Shower Association */}
          <div className="panel">
            <div className="ph" style={{"--al":"#facc15"} as any}>
              <div className="pt">Shower Association</div>
            </div>
            <div style={{padding:0}}>
              {events.map((ev: any, i: number) => (
                <div className="srow" key={i}>
                  <div className="sl2">
                    <span className="sdot" style={{background: COLORS[i]}} />
                    <div>
                      <div className="sname">{ev.event_id}</div>
                      <div className="sloc">
                        {ev.shower_match?.shower_name || ev.metadata?.shower || "Sporadic"} ·
                        {(ev.shower_match?.separation_deg || 0).toFixed(1)}° separation
                      </div>
                    </div>
                  </div>
                  <div style={{textAlign:"right"}}>
                    <div className="sresid" style={{color: (ev.shower_match?.confidence || 0) > 70 ? "var(--accent)" : "#facc15"}}>
                      {ev.shower_match?.confidence ? `${ev.shower_match.confidence.toFixed(0)}%` : "N/A"}
                    </div>
                    <div className="sframes">{ev.quality?.label || "—"}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  );
}
