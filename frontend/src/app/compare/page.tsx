"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ComparePage() {
  const [allEvents, setAllEvents] = useState<any[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [networkFilter, setNetworkFilter] = useState("All");

  useEffect(() => {
    fetch(`${API}/api/events?page_size=500`)
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

  const networks = Array.from(new Set(allEvents.map(e => e.network).filter(Boolean)));

  const filteredEvents = allEvents.filter(ev => {
    if (networkFilter !== "All" && ev.network !== networkFilter) return false;
    if (search) {
      const s = search.toLowerCase();
      const searchable = `${ev.event_id} ${ev.shower || ""} ${ev.network || ""}`.toLowerCase();
      if (!searchable.includes(s)) return false;
    }
    return true;
  });

  const events = comparison?.events || [];

  const COLORS = ["var(--accent)", "var(--accent2)", "var(--accent3)", "#facc15", "#38bdf8"];

  return (
    <>
      <div className="sec-head">
        <div className="sec-title">Multi-Event Comparison</div>
        <div className="heading-actions">
          <button className="btn btn-accent" onClick={handleCompare}
            disabled={selected.length < 2 || loading}>
            {loading ? "Reconstructing…" : `Compare ${selected.length} events`}
          </button>
          <Link href="/"><button className="btn btn-ghost">← Catalogue</button></Link>
        </div>
      </div>

      {/* Event Selector */}
      <div className="panel" style={{marginBottom:20}}>
        <div className="ph" style={{"--al":"var(--accent)"} as any}>
          <div className="pt">Select Events ({selected.length}/5 selected · {filteredEvents.length} available)</div>
        </div>
        <div style={{padding:"12px 16px",display:"flex",gap:8,alignItems:"center",borderBottom:"1px solid var(--cb)"}}>
          <input
            type="text" placeholder="Search events…" value={search}
            onChange={e => setSearch(e.target.value)}
            style={{flex:1,background:"rgba(0,0,0,.3)",border:"1px solid var(--cb)",borderRadius:6,padding:"6px 12px",
              color:"var(--fg)",fontFamily:"var(--mono)",fontSize:10,outline:"none"}}
          />
          <select value={networkFilter} onChange={e => setNetworkFilter(e.target.value)}
            style={{background:"rgba(0,0,0,.3)",border:"1px solid var(--cb)",borderRadius:6,padding:"6px 10px",
              color:"var(--fg)",fontFamily:"var(--mono)",fontSize:10,outline:"none"}}>
            <option value="All">All Networks</option>
            {networks.map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        <div style={{maxHeight:220,overflowY:"auto",padding:"4px 0",scrollbarWidth:"none",msOverflowStyle:"none"}} className="hide-scrollbar">
          {filteredEvents.map(ev => (
            <div key={ev.event_id}
              onClick={() => toggle(ev.event_id)}
              style={{display:"flex",alignItems:"center",gap:10,padding:"6px 16px",cursor:"pointer",
                borderBottom:"1px solid var(--cb)",
                background: selected.includes(ev.event_id) ? "rgba(56,189,248,0.08)" : "transparent",
                transition:"background .15s"}}>
              <span style={{width:14,height:14,borderRadius:3,border: selected.includes(ev.event_id) ? "2px solid var(--accent)" : "1px solid var(--dim)",
                display:"flex",alignItems:"center",justifyContent:"center",fontSize:9,color:"var(--accent)",fontWeight:700,flexShrink:0}}>
                {selected.includes(ev.event_id) ? "✓" : ""}
              </span>
              <span style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--fg)",flex:1,minWidth:0,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                {ev.event_id}
              </span>
              <span style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--accent2)",flexShrink:0}}>
                {ev.shower && ev.shower !== "Sporadic" ? ev.shower : ""}
              </span>
              <span style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--dim)",flexShrink:0}}>
                {ev.velocity ? `${ev.velocity.toFixed(1)} km/s` : ""}
              </span>
              <span style={{fontFamily:"var(--mono)",fontSize:8,padding:"1px 6px",borderRadius:4,flexShrink:0,
                background:"rgba(255,255,255,0.04)",color:"var(--muted)"}}>
                {ev.network}
              </span>
            </div>
          ))}
          {filteredEvents.length === 0 && (
            <div style={{padding:24,textAlign:"center",fontFamily:"var(--mono)",fontSize:10,color:"var(--dim)"}}>
              No events match your search
            </div>
          )}
        </div>
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
                {events.every((ev: any) => ev.orbital_elements?.error || (!ev.orbital_elements?.semi_major_axis_au && ev.orbital_elements?.semi_major_axis_au !== 0)) ? (
                  <div style={{padding:"20px 12px",fontFamily:"var(--mono)",fontSize:10,color:"var(--dim)",textAlign:"center",lineHeight:1.8}}>
                    Orbital elements unavailable for selected events.<br/>
                    Single-station events (e.g. NASA JPL) lack radiant direction data<br/>
                    required for orbit computation. Try comparing multi-station events (GMN, FRIPON, NASA AFSN).
                  </div>
                ) : (
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
                      ["i (\u00b0)", "inclination_deg"],
                      ["\u03c9 (\u00b0)", "argument_of_perihelion_deg"],
                      ["\u03a9 (\u00b0)", "longitude_of_ascending_node_deg"],
                      ["q (AU)", "perihelion_distance_au"],
                      ["Tj", "tisserand_parameter"],
                      ["Type", "orbit_type"],
                    ].map(([label, key]) => (
                      <tr key={String(key)}>
                        <td style={{color:"var(--muted)"}}>{String(label)}</td>
                        {events.map((ev: any, i: number) => {
                          const val = ev.orbital_elements?.[String(key)];
                          return (
                            <td key={i}>
                              {val !== undefined && val !== null ? (typeof val === 'number' ? val.toFixed(3) : val) : "N/A"}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
                )}
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
