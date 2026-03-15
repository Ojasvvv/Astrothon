"use client";
import { useState, useEffect, use } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function EventDashboard({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const eventId = decodeURIComponent(unwrappedParams.id);
  
  const [data, setData] = useState<any>(null);
  const [traj, setTraj] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string|null>(null);
  const [reconstructing, setReconstructing] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [activeView, setActiveView] = useState("3D");
  const [velModel, setVelModel] = useState("Linear");

  // Related events for chooser
  const [allEvents, setAllEvents] = useState<string[]>([]);
  const [showChooser, setShowChooser] = useState(false);

  useEffect(() => {
    // Fetch current event
    fetch(`${API}/api/events/${unwrappedParams.id}`)
      .then(r => { if(!r.ok) throw new Error("Event not found"); return r.json(); })
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });

    // Fetch all IDs for the chooser
    fetch(`${API}/api/events?page_size=100`)
      .then(r => r.json())
      .then(d => setAllEvents((d.events || []).map((ev: any) => ev.event_id)))
      .catch(() => {});

    fetch(`${API}/api/events/${encodeURIComponent(eventId)}/trajectory`)
      .then(r => r.ok ? r.json() : null).then(d => { setTraj(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [unwrappedParams.id, eventId]);

  const handleReconstruct = () => {
    setReconstructing(true);
    fetch(`${API}/api/events/${encodeURIComponent(eventId)}/reconstruct`, { method: "POST" })
      .then(r => r.json()).then(d => { setTraj(d); setReconstructing(false); })
      .catch(() => setReconstructing(false));
  };

  const meta = data?.metadata || {};
  const t = traj?.trajectory || {};
  const vel = traj?.velocity || {};
  const orbit = traj?.orbital_elements || {};
  const quality = traj?.quality || {};
  const showerMatch = traj?.shower_match || {};
  const radiant = traj?.radiant || {};
  const timing = traj?.timing_offsets_ms || {};
  const fallPred = traj?.fall_prediction;
  const massEst = traj?.mass_estimate;
  const uncertainty = traj?.uncertainty;

  const v0 = vel?.initial_velocity_kms || meta.estimated_velocity_kms || 30;
  const decel = vel?.deceleration_kms2 || -2;
  const entryAngle = t?.entry_angle_deg || 35;
  const peakMag = meta.peak_magnitude || -5;
  const trajLen = t?.trajectory_length_km || meta.trajectory_length_km || 200;
  const shower = showerMatch?.shower_name || meta.shower || "Sporadic";
  const showerConf = showerMatch?.confidence || 0;

  const statCount = meta.station_count || 0;
  const ptsCount = t?.num_observations || 0;

  if (loading) {
    return <div className="wrap">Loading...</div>;
  }

  if (error) {
    return <div className="wrap">Error: {error}</div>;
  }

  // Un-analyzed state
  if (!traj) { // Assuming 'traj' being null means it's un-analyzed or not yet reconstructed
    return (
      <div style={{display:"flex", flexDirection:"column", gap: 20}}>
        <div className="breadcrumb">
          <Link href="/" className="bc-link">catalogue</Link> /
          <span className="bc-active">{data.event_id}</span>
        </div>
        {/* Un-analyzed Header */}
        <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom: 30}}>
          <div>
            <h1 style={{margin:0,fontSize:28,fontWeight:600,color:"#fff"}}><span style={{color:"var(--accent)"}}>Raw:</span> {data.event_id}</h1>
            <div style={{display:"flex", gap:12, fontSize:13, color:"var(--dim)", marginTop: 8, fontFamily:"var(--mono)", letterSpacing:".05em"}}>
              <span>{meta.network}</span> •
              <span>{meta.utc_timestamp?.replace('T', ' ').substring(0, 19)} UTC</span> •
              <span>{meta.station_count} stations</span>
            </div>
          </div>
          <div style={{display:"flex", alignItems:"center", gap: 12}}>
            {!traj && (
              <button className="btn btn-accent" onClick={handleReconstruct} disabled={reconstructing}>
                {reconstructing ? "Reconstructing…" : "▶ Reconstruct"}
              </button>
            )}
            <div style={{position: "relative", marginLeft: 4}}>
               <button className="btn btn-ghost" style={{padding: "7px 14px", fontSize: 11}} onClick={() => setShowChooser(!showChooser)}>
                 Switch Event ⌄
               </button>
               {showChooser && (
                 <div style={{position:"absolute", top:35, right:0, background:"#0f172a", border:"1px solid var(--bd)", borderRadius:6, padding:10, zIndex:100, width: 250, maxHeight: 300, overflowY:"auto", boxShadow:"0 10px 25px rgba(0,0,0,0.5)"}}>
                   <div style={{fontSize:10, fontFamily:"var(--mono)", color:"var(--dim)", marginBottom:10}}>QUICK JUMP</div>
                   {allEvents.map(id => (
                     <Link key={id} href={`/event/${id}`} onClick={() => setShowChooser(false)}>
                       <div style={{padding:"8px 10px", fontSize:13, borderRadius:4, background: id === data.event_id ? "rgba(56,189,248,0.1)" : "transparent", color: id === data.event_id ? "#38bdf8" : "var(--tx)", cursor:"pointer", marginBottom:2}} className="hover-highlight">
                         {id}
                       </div>
                     </Link>
                   ))}
                 </div>
               )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{display:"flex", flexDirection:"column", gap: 20}}>
      <div className="breadcrumb">
        <Link href="/" className="bc-link">catalogue</Link> /
        <span className="bc-active">{data.event_id}</span>
      </div>

      {/* Header */}
      {/* Analyzed Header */}
      <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom: 30}}>
        <div>
          <h1 style={{margin:0,fontSize:28,fontWeight:600,color:"#fff"}}>{data.event_id}</h1>
          <div style={{display:"flex", gap:12, fontSize:13, color:"var(--dim)", marginTop: 8, fontFamily:"var(--mono)", letterSpacing:".05em"}}>
            <span>{meta.network}</span> •
            <span>{meta.utc_timestamp?.replace('T', ' ').substring(0, 19)} UTC</span> •
            {shower !== "Sporadic" ? <span style={{color:"var(--accent2)"}}>{shower}</span> : <span>Sporadic</span>}
          </div>
        </div>
        <div style={{display:"flex", alignItems:"center", gap: 12}}>
          <span className="badge bp" style={{padding:"4px 8px"}}>{statCount} stations</span>
          <span className="badge by" style={{padding:"4px 8px"}}>{ptsCount} points</span>

          <div style={{position: "relative", marginLeft: 4}}>
             <button className="btn btn-ghost" style={{padding: "7px 14px", fontSize: 11}} onClick={() => setShowChooser(!showChooser)}>
               Switch Event ⌄
             </button>
             {showChooser && (
               <div style={{position:"absolute", top:35, right:0, background:"#0f172a", border:"1px solid var(--bd)", borderRadius:6, padding:10, zIndex:100, width: 250, maxHeight: 300, overflowY:"auto", boxShadow:"0 10px 25px rgba(0,0,0,0.5)", textAlign:"left"}}>
                 <div style={{fontSize:10, fontFamily:"var(--mono)", color:"var(--dim)", marginBottom:10}}>QUICK JUMP ({allEvents.length})</div>
                 {allEvents.map(id => (
                   <Link key={id} href={`/event/${id}`} onClick={() => setShowChooser(false)}>
                     <div style={{padding:"8px 10px", fontSize:13, borderRadius:4, background: id === data.event_id ? "rgba(56,189,248,0.1)" : "transparent", color: id === data.event_id ? "#38bdf8" : "var(--tx)", cursor:"pointer", marginBottom:2}} className="hover-highlight">
                       {id}
                     </div>
                   </Link>
                 ))}
               </div>
             )}
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="stat-row">
        <div className="stat-card" style={{"--al":"var(--accent)"} as any}>
          <div className="sl">Initial velocity</div>
          <div className="sv">{v0.toFixed(1)}<small> km/s</small></div>
          <div className="ss">
            {uncertainty?.initial_velocity?.std ?
              <span className="badge bg">±{uncertainty.initial_velocity.std.toFixed(2)} km/s</span> :
              <span className="badge bg">—</span>}
          </div>
        </div>
        <div className="stat-card" style={{"--al":"var(--accent2)"} as any}>
          <div className="sl">Entry angle</div>
          <div className="sv">{entryAngle.toFixed(1)}<small>°</small></div>
          <div className="ss"><span className="badge bo">{entryAngle < 30 ? "Steep" : entryAngle < 50 ? "Shallow" : "Grazing"}</span></div>
        </div>
        <div className="stat-card" style={{"--al":"var(--accent3)"} as any}>
          <div className="sl">Peak magnitude</div>
          <div className="sv">{peakMag.toFixed(1)}<small> mag</small></div>
          <div className="ss"><span className="badge bp">{peakMag < -6 ? "Fireball class" : peakMag < -3 ? "Bright" : "Normal"}</span></div>
        </div>
        <div className="stat-card" style={{"--al":"#38bdf8"} as any}>
          <div className="sl">Trajectory length</div>
          <div className="sv">{Math.round(trajLen)}<small> km</small></div>
          <div className="ss" style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--muted)"}}>
            {Math.round(t?.entry_altitude_km || meta.entry_altitude_km || 95)} → {Math.round(t?.terminal_altitude_km || meta.terminal_altitude_km || 25)} km alt.
          </div>
        </div>
        <div className="stat-card" style={{"--al":"#facc15"} as any}>
          <div className="sl">Shower</div>
          <div className="sv" style={{fontSize:15,paddingTop:3}}>{shower}</div>
          <div className="ss">{showerConf > 0 ? <span className="badge by">{showerConf.toFixed(1)}% conf.</span> : <span className="badge by">—</span>}</div>
        </div>
      </div>

      {/* Content Grid */}
      <div className="content-grid">
        {/* Trajectory Viewer */}
        <div className="panel">
          <div className="ph">
            <div className="pt">Trajectory · Earth frame</div>
            <div className="pa">
              {["3D","Ground track","LOS rays"].map(v => (
                <button key={v} className={`pb ${activeView === v ? "active" : ""}`}
                  onClick={() => setActiveView(v)}>{v}</button>
              ))}
            </div>
          </div>
          <div className="globe-wrap">
            <TrajectoryViewer trajectory={t} stations={data?.stations} />
            <div className="globe-coords left">
              Entry: {(t?.entry_lat||0).toFixed(1)}°N / {(t?.entry_lon||0).toFixed(1)}°E / {(t?.entry_altitude_km||95).toFixed(1)} km<br/>
              Terminal: {(t?.terminal_altitude_km||25).toFixed(1)} km alt.<br/>
              RMS: {(t?.rms_residual_arcsec||0).toFixed(2)}″
            </div>
            <div className="globe-coords right">
              Stations: {t?.num_inliers || meta.station_count || 0}/{meta.station_count || 0}<br/>
              Q: {(t?.convergence_angle_Q||0).toFixed(1)}°<br/>
              Quality: {quality?.label || "—"}
            </div>
          </div>
          <div className="frame-row">
            <span style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--dim)"}}>FRAME</span>
            <div className="fr-bar-track">
              <div className="fr-bar" style={{width: traj ? "62%" : "0%"}} />
            </div>
            <span style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--muted)"}}>
              {t?.num_observations || 0} obs
            </span>
          </div>
        </div>

        {/* Right Stack */}
        <div className="right-stack">
          {/* Velocity Profile */}
          <div className="panel">
            <div className="ph" style={{"--al":"var(--accent)"} as any}>
              <div className="pt">Velocity profile</div>
              <div className="pa">
                {["Linear","W–J"].map(m => (
                  <button key={m} className={`pb ${velModel === m ? "active" : ""}`}
                    onClick={() => setVelModel(m)}>{m}</button>
                ))}
              </div>
            </div>
            <div className="vel-inner">
              <div className="vel-nums">
                <div>
                  <div className="vdl">Init. velocity</div>
                  <div className="vbig">{v0.toFixed(1)}<small> km/s</small></div>
                </div>
                <div className="vright">
                  <div className="vdl">Deceleration</div>
                  <div className="vd">{decel.toFixed(1)} km/s²</div>
                </div>
              </div>
              <VelocityChart velocity={vel} model={velModel} />
            </div>
          </div>

          {/* Stations */}
          <div className="panel" style={{flex:1}}>
            <div className="ph">
              <div className="pt">Stations</div>
              <span style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--muted)"}}>
                {meta.station_count || 0} ACTIVE
              </span>
            </div>
            {(data?.stations || []).map((st: any) => {
              const resid = t?.station_residuals?.[st.station_id];
              const rms = resid?.rms_residual || 0;
              const color = rms < 1 ? "var(--accent)" : rms < 2 ? "var(--accent3)" : "var(--accent2)";
              return (
                <div className="srow" key={st.station_id}>
                  <div className="sl2">
                    <span className="sdot" style={{background: color}} />
                    <div>
                      <div className="sname">{st.station_id}</div>
                      <div className="sloc">{st.latitude.toFixed(1)}°N · {st.longitude.toFixed(1)}°E</div>
                    </div>
                  </div>
                  <div style={{textAlign:"right"}}>
                    <div className="sresid" style={{color}}>{rms.toFixed(2)}″</div>
                    <div className="sframes">{resid?.frames || 0} fr</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="bottom-row">
        {/* Orbit */}
        <div className="panel">
          <div className="ph" style={{"--al":"var(--accent3)"} as any}>
            <div className="pt">Heliocentric orbit</div>
          </div>
          <div className="orbit-inner">
            <OrbitDiagram orbit={orbit} />
          </div>
          <div className="oe-grid">
            <div><div className="oe-n">Semi-major axis</div>
              <div className="oe-v">{(orbit?.semi_major_axis_au||0).toFixed(2)}<span className="oe-u"> AU</span></div></div>
            <div><div className="oe-n">Eccentricity</div>
              <div className="oe-v">{(orbit?.eccentricity||0).toFixed(3)}</div></div>
            <div><div className="oe-n">Inclination</div>
              <div className="oe-v">{(orbit?.inclination_deg||0).toFixed(1)}<span className="oe-u">°</span></div></div>
            <div><div className="oe-n">Perihelion</div>
              <div className="oe-v">{(orbit?.perihelion_distance_au||0).toFixed(3)}<span className="oe-u"> AU</span></div></div>
          </div>
        </div>

        {/* Sky Radiant */}
        <div className="panel">
          <div className="ph" style={{"--al":"var(--accent2)"} as any}>
            <div className="pt">Sky radiant</div>
          </div>
          <div className="sky-inner">
            <SkyRadiant radiant={radiant} shower={showerMatch} uncertainty={uncertainty} />
          </div>
          <div className="sky-coords">
            <div><div className="oe-n">Geocentric RA</div>
              <div className="oe-v">{(radiant?.ra_deg||0).toFixed(1)}<span className="oe-u">°</span></div></div>
            <div><div className="oe-n">Geocentric Dec</div>
              <div className="oe-v">{(radiant?.dec_deg||0) > 0 ? "+" : ""}{(radiant?.dec_deg||0).toFixed(1)}<span className="oe-u">°</span></div></div>
            <div><div className="oe-n">Vg</div>
              <div className="oe-v">{(orbit?.geocentric_velocity_kms||v0).toFixed(1)}<span className="oe-u"> km/s</span></div></div>
            <div><div className="oe-n">Separation</div>
              <div className="oe-v">{(showerMatch?.separation_deg||0).toFixed(1)}<span className="oe-u">°</span></div></div>
          </div>
        </div>

        {/* Quality */}
        <div className="panel">
          <div className="ph" style={{"--al":"#facc15"} as any}>
            <div className="pt">Quality score</div>
          </div>
          <div className="qi">
            <div className="qscore">{quality?.composite_score || "—"}</div>
            <div className="qlabel">/ 100 · <span style={{color:"var(--accent)"}}>{quality?.label || "—"}</span></div>
            {Object.entries(quality?.breakdown || {}).map(([key, val]: [string, any]) => (
              <div key={key}>
                <div className="qrow">
                  <span className="qn">{key.replace(/_/g, " ")}</span>
                  <span className="qv" style={{
                    color: val?.score > 80 ? "var(--accent)" : val?.score > 50 ? "#facc15" : "var(--accent2)"
                  }}>{typeof val?.value === "number" ? val.value.toFixed(2) : "—"}</span>
                </div>
                <div className="qtrack">
                  <div className="qfill" style={{
                    width: `${val?.score || 0}%`,
                    background: val?.score > 80 ? "var(--accent)" : val?.score > 50 ? "#facc15" : "var(--accent2)"
                  }} />
                </div>
              </div>
            ))}
            {Object.keys(timing).length > 0 && (
              <div style={{marginTop:10,paddingTop:10,borderTop:"1px solid var(--cb)"}}>
                <div style={{fontFamily:"var(--mono)",fontSize:7,color:"var(--dim)",marginBottom:4,letterSpacing:".1em"}}>CLOCK OFFSETS (ms)</div>
                <div style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--muted)",lineHeight:2}}>
                  {Object.entries(timing).map(([sid, ms]) => (
                    <span key={sid} style={{marginRight:8}}>
                      {sid.split("-")[0]}: <span style={{color: Math.abs(Number(ms)) > 10 ? "var(--accent2)" : "var(--accent)"}}>
                        {Number(ms) > 0 ? "+" : ""}{Number(ms).toFixed(1)}
                        {Math.abs(Number(ms)) > 10 ? " ⚠" : ""}
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="summary">
        <div className="summary-icon">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 1l1.8 3.6 4 .6-2.9 2.8.7 4L8 10l-3.6 1.9.7-4L2.2 5.2l4-.6L8 1z"
              stroke="#4af4c4" strokeWidth="1.2" fill="rgba(74,244,196,.15)" />
          </svg>
        </div>
        <div style={{flex:1}}>
          <div className="summary-title">What happened</div>
          <div className="summary-text">
            {shower !== "Sporadic" ? `A fragment associated with the ${shower} meteor shower` : "A sporadic meteoroid"} entered Earth&apos;s atmosphere at <em>{v0.toFixed(1)} km/s</em>
            {meta.region ? ` over ${meta.region}` : ""}. It was observed by <em>{meta.station_count} camera stations</em> and
            burned {""}
            {(t?.terminal_altitude_km || meta.terminal_altitude_km || 25) > 15 ? "up completely" : "down to low altitude"} at {Math.round(t?.terminal_altitude_km || meta.terminal_altitude_km || 25)} km altitude
            after travelling {Math.round(trajLen)} km.
            The peak brightness reached magnitude <em>{peakMag.toFixed(1)}</em>
            {peakMag < -6 ? ` — ${Math.round(Math.pow(10, -0.4*(peakMag+12.7)))}× brighter than a full moon` : ""}.
            This reconstruction carries <em>{quality?.label || "pending"} scientific confidence</em>.
            {massEst?.mass_grams ? ` Estimated meteoroid mass: ${massEst.mass_grams.toFixed(1)} grams.` : ""}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Sub-components ─────────────────────────────────── */

function TrajectoryViewer({ trajectory, stations }: { trajectory: any; stations: any[] }) {
  return (
    <svg width="480" height="310" viewBox="0 0 480 310">
      <defs>
        <radialGradient id="gg" cx="40%" cy="38%">
          <stop offset="0%" stopColor="#1a3a5c" /><stop offset="50%" stopColor="#0e2240" /><stop offset="100%" stopColor="#060f1e" />
        </radialGradient>
        <clipPath id="cc"><circle cx="240" cy="155" r="124" /></clipPath>
      </defs>
      <circle cx="240" cy="155" r="124" fill="url(#gg)" />
      <g clipPath="url(#cc)" stroke="rgba(255,255,255,.05)" strokeWidth=".5" fill="none">
        <ellipse cx="240" cy="155" rx="124" ry="24" />
        <ellipse cx="240" cy="155" rx="124" ry="58" />
        <ellipse cx="240" cy="155" rx="124" ry="96" />
        <line x1="116" y1="155" x2="364" y2="155" />
        <line x1="240" y1="31" x2="240" y2="279" />
      </g>
      <g clipPath="url(#cc)" fill="rgba(74,244,196,.07)" stroke="rgba(74,244,196,.18)" strokeWidth=".5">
        <path d="M192,108 L216,98 L230,103 L240,117 L235,135 L221,140 L207,130 L198,120Z" />
        <path d="M250,112 L274,108 L288,118 L293,136 L284,150 L265,154 L256,145 L249,131Z" />
        <path d="M163,152 L187,147 L193,161 L188,175 L171,180 L162,168Z" />
      </g>
      {/* Station markers */}
      {(stations || []).slice(0, 7).map((st: any, i: number) => {
        const x = 160 + i * 25 + (i % 2) * 15;
        const y = 130 + (i % 3) * 20;
        return (
          <g key={i} opacity=".9">
            <line x1={x} y1={y} x2="265" y2="82" stroke="rgba(74,244,196,.2)" strokeWidth=".6" strokeDasharray="3,2" />
            <circle cx={x} cy={y} r="3" fill="none" stroke="var(--accent)" strokeWidth="1" /><circle cx={x} cy={y} r="1.3" fill="var(--accent)" />
          </g>
        );
      })}
      {/* Trajectory line */}
      <line x1="288" y1="44" x2="242" y2="108" stroke="rgba(255,107,74,.18)" strokeWidth="7" strokeLinecap="round" />
      <line x1="288" y1="44" x2="242" y2="108" stroke="#ff6b4a" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="288" cy="44" r="4.5" fill="none" stroke="var(--accent2)" strokeWidth="1.3" />
      <circle cx="288" cy="44" r="2.2" fill="var(--accent2)" />
      <circle cx="242" cy="108" r="3.5" fill="none" stroke="rgba(250,204,21,.8)" strokeWidth="1.1" />
      <circle cx="242" cy="108" r="1.5" fill="#facc15" />
      <circle cx="240" cy="155" r="124" fill="none" stroke="rgba(255,255,255,.1)" strokeWidth=".5" />
      <text x="300" y="42" fill="rgba(255,107,74,.85)" fontSize="8" fontFamily="'Space Mono',monospace">
        {Math.round(trajectory?.entry_altitude_km || 95)} km
      </text>
      <text x="228" y="122" fill="rgba(250,204,21,.75)" fontSize="8" fontFamily="'Space Mono',monospace">
        {Math.round(trajectory?.terminal_altitude_km || 25)} km
      </text>
    </svg>
  );
}

function VelocityChart({ velocity, model }: { velocity: any; model: string }) {
  const profile = velocity?.velocity_profile;
  if (!profile?.distances_km?.length) {
    return <svg width="100%" viewBox="0 0 276 80"><text x="138" y="45" fill="var(--dim)" fontSize="10" textAnchor="middle" fontFamily="'Space Mono',monospace">Run reconstruction to view</text></svg>;
  }
  const dists = profile.distances_km;
  const vels = model === "W–J" ? profile.velocity_wj_kms : profile.velocity_linear_kms;
  const vObs = profile.velocity_observed_kms;
  const vObsReal = vObs.filter((v:any) => v != null && !isNaN(v));
  const velsReal = vels.filter((v:any) => v != null && !isNaN(v));
  const maxD = Math.max(...dists, 1);
  const maxV = Math.max(...vObsReal, ...velsReal, 1);
  const minV = Math.min(...vObsReal, ...velsReal, 0);
  const range = maxV - minV || 1;
  const toX = (d: number) => (d / maxD) * 276;
  const toY = (v: number) => 80 - ((v - minV) / range) * 75;
  
  let first = true;
  const fitPath = vels.map((v: number, i: number) => {
    if (v == null || isNaN(v)) return "";
    const prefix = first ? "M" : "L";
    first = false;
    return `${prefix}${toX(dists[i]).toFixed(1)},${toY(v).toFixed(1)}`;
  }).filter(Boolean).join(" ");
  return (
    <svg width="100%" viewBox="0 0 276 95" style={{overflow:"visible"}}>
      <defs><linearGradient id="vg2" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="rgba(74,244,196,.18)" /><stop offset="100%" stopColor="rgba(74,244,196,0)" /></linearGradient></defs>
      {[0,27,54,80].map(y => <line key={y} x1="0" y1={y} x2="276" y2={y} stroke="rgba(255,255,255,.04)" strokeWidth=".5" />)}
      <path d={`${fitPath} L276,80 L0,80Z`} fill="url(#vg2)" />
      <path d={fitPath} fill="none" stroke="var(--accent)" strokeWidth="1.4" strokeLinecap="round" />
      {vObs.map((v: number, i: number) => {
        if (v == null || isNaN(v)) return null;
        return <circle key={i} cx={toX(dists[i])} cy={toY(v)} r="1.5" fill="var(--accent)" opacity=".7" />;
      })}
      <text x="0" y="93" fill="rgba(255,255,255,.18)" fontSize="7" fontFamily="'Space Mono',monospace">0</text>
      <text x="138" y="93" fill="rgba(255,255,255,.18)" fontSize="7" fontFamily="'Space Mono',monospace" textAnchor="middle">{Math.round(maxD/2)} km</text>
      <text x="276" y="93" fill="rgba(255,255,255,.18)" fontSize="7" fontFamily="'Space Mono',monospace" textAnchor="end">{Math.round(maxD)} km</text>
    </svg>
  );
}

function OrbitDiagram({ orbit }: { orbit: any }) {
  const e = orbit?.eccentricity || 0.5;
  const a = Math.min(orbit?.semi_major_axis_au || 2, 6);
  const rx = 25 + a * 10;
  const ry = rx * Math.sqrt(1 - Math.min(e * e, 0.99));
  return (
    <svg width="170" height="148" viewBox="0 0 170 148">
      <defs><radialGradient id="sg2" cx="50%" cy="50%"><stop offset="0%" stopColor="#facc15" /><stop offset="100%" stopColor="rgba(249,115,22,0)" /></radialGradient></defs>
      <circle cx="85" cy="74" r="17" fill="none" stroke="rgba(255,255,255,.07)" strokeWidth=".5" />
      <circle cx="85" cy="74" r="27" fill="none" stroke="rgba(255,255,255,.07)" strokeWidth=".5" />
      <circle cx="85" cy="74" r="38" fill="none" stroke="rgba(74,244,196,.2)" strokeWidth=".7" />
      <circle cx="85" cy="74" r="53" fill="none" stroke="rgba(255,255,255,.05)" strokeWidth=".5" />
      <ellipse cx={85 - e * rx * 0.3} cy="74" rx={rx} ry={ry} fill="none" stroke="rgba(255,107,74,.55)" strokeWidth="1.1" strokeDasharray="4,2" transform={`rotate(-25 85 74)`} />
      <circle cx="85" cy="74" r="6" fill="url(#sg2)" /><circle cx="85" cy="74" r="3.5" fill="#facc15" />
      <circle cx="123" cy="74" r="3.8" fill="#1d7fd4" /><circle cx="123" cy="74" r="5.5" fill="none" stroke="rgba(29,127,212,.28)" strokeWidth=".7" />
      <circle cx="138" cy="74" r="2.8" fill="#c1440e" />
      <text x="127" y="78" fill="rgba(29,127,212,.75)" fontSize="6.5" fontFamily="'Space Mono',monospace">Earth</text>
    </svg>
  );
}

function SkyRadiant({ radiant, shower, uncertainty }: { radiant: any; shower: any; uncertainty: any }) {
  const ra = radiant?.ra_deg || 0;
  const dec = radiant?.dec_deg || 0;
  const cx = 89 + (ra - 180) / 360 * 168;
  const cy = 59 - dec / 90 * 55;
  const ell = uncertainty?.radiant_ellipse;
  return (
    <svg width="178" height="118" viewBox="0 0 178 118">
      <rect x="0" y="0" width="178" height="118" rx="5" fill="rgba(8,13,26,.5)" />
      <ellipse cx="89" cy="59" rx="84" ry="55" fill="none" stroke="rgba(255,255,255,.05)" strokeWidth=".5" />
      <ellipse cx="89" cy="59" rx="56" ry="37" fill="none" stroke="rgba(255,255,255,.04)" strokeWidth=".5" />
      <line x1="5" y1="59" x2="173" y2="59" stroke="rgba(255,255,255,.04)" strokeWidth=".5" />
      <line x1="89" y1="4" x2="89" y2="114" stroke="rgba(255,255,255,.04)" strokeWidth=".5" />
      {ell && <ellipse cx={cx} cy={cy} rx={Math.max(3, ell.semi_major_deg * 5)} ry={Math.max(2, ell.semi_minor_deg * 5)}
        fill="rgba(255,107,74,.07)" stroke="rgba(255,107,74,.28)" strokeWidth=".7" strokeDasharray="2,1" />}
      <circle cx={cx} cy={cy} r="4.5" fill="var(--accent2)" opacity=".9" />
      <circle cx={cx} cy={cy} r="7" fill="none" stroke="var(--accent2)" strokeWidth=".8" opacity=".45" />
      {shower?.shower_name && <text x={Math.min(cx + 12, 150)} y={cy} fill="rgba(255,107,74,.8)" fontSize="6.5" fontFamily="'Space Mono',monospace">{shower.shower_name}</text>}
      <text x="5" y="113" fill="rgba(255,255,255,.18)" fontSize="6.5" fontFamily="'Space Mono',monospace">RA: {ra.toFixed(1)}°</text>
      <text x="173" y="113" fill="rgba(255,255,255,.18)" fontSize="6.5" fontFamily="'Space Mono',monospace" textAnchor="end">Dec: {dec > 0 ? "+" : ""}{dec.toFixed(1)}°</text>
    </svg>
  );
}
