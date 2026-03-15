"use client";
import { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function MonteCarloPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, any>>({});

  useEffect(() => {
    fetch(`${API}/api/events?page_size=20`)
      .then(r => r.json()).then(d => { setEvents(d.events || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const runSimulation = async (id: string) => {
    setRunningId(id);
    try {
      const res = await fetch(`${API}/api/events/${encodeURIComponent(id)}/montecarlo?n_iterations=100`, {
        method: "POST"
      });
      const data = await res.json();
      setResults(prev => ({ ...prev, [id]: data }));
    } catch (e) {
      console.error(e);
      alert("Simulation failed");
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div style={{display:"flex", flexDirection:"column", gap: 20}}>
      <div className="sec-head">
        <div className="sec-title">Monte Carlo Uncertainty Analysis</div>
        <div style={{fontFamily:"var(--mono)",fontSize:10,color:"#38bdf8"}}>STOCHASTIC ERROR ESTIMATION</div>
      </div>

      <div className="summary" style={{marginBottom: 15, borderLeftColor: "#38bdf8"}}>
        <div className="summary-icon" style={{color: "#38bdf8"}}>⤴</div>
        <div>
          <div className="summary-title" style={{color: "#38bdf8"}}>Run Monte Carlo Simulation</div>
          <div className="summary-text" style={{lineHeight: 1.6}}>
            Perturb astrometric observations with Gaussian noise ($3\sigma$ bounds) to estimate robust standard deviations ($\sigma$) and confidence intervals for velocity, radiant coordinates, and Keplerian orbital parameters. Select an event to run the $N=100$ iteration simulation directly on the Python backend.
          </div>
        </div>
      </div>

      <div style={{display:"grid",gap:16,gridTemplateColumns:"repeat(auto-fill,minmax(350px,1fr))"}}>
        {events.map((ev: any) => {
          const res = results[ev.event_id];
          const isRunning = runningId === ev.event_id;
          
          return (
            <div key={ev.event_id} className="panel" style={{marginBottom: 0, padding:"12px", ...(res ? {borderColor: "#38bdf8"} : {})}}>
              <div>
                <div style={{display:"flex",justifyContent:"space-between"}}>
                  <div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--muted)",marginBottom:4}}>
                    {ev.network} · {ev.utc_timestamp?.split("T")[0]}
                  </div>
                  {res && <div style={{fontFamily:"var(--mono)",fontSize:10,color:"#38bdf8"}}>COMPLETED</div>}
                </div>
                <div style={{fontSize:15,fontWeight:600}}>{ev.event_id}</div>
                <div style={{marginTop: 12, display:"flex", justifyContent:"space-between", alignItems:"center"}}>
                  <div>
                    <span className="badge bp">{res ? "100 iterations" : `${ev.station_count} stations`}</span>
                    {res && <span className="badge by" style={{marginLeft:6}}>{res.n_success} converged</span>}
                  </div>
                  {!res && (
                    <button className={`btn ${isRunning ? "btn-ghost" : "btn-ghost"}`} 
                      style={isRunning ? {opacity: 0.5, cursor: "not-allowed"} : {color: "#38bdf8", borderColor:"rgba(56,189,248,0.3)"}}
                      onClick={() => runSimulation(ev.event_id)}
                      disabled={isRunning || runningId !== null}>
                      {isRunning ? "Computing..." : "Run MC Simulation"}
                    </button>
                  )}
                </div>
                
                {/* Results Visualization */}
                {res && (
                  <div style={{marginTop: 16, paddingTop: 16, borderTop: "1px solid rgba(255,255,255,0.05)"}}>
                    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
                      <div>
                        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--dim)",marginBottom:4}}>VELOCITY $\sigma$</div>
                        <div style={{fontSize:16,color:"#38bdf8"}}>
                          ±{res.initial_velocity?.std?.toFixed(2) || "0.00"} <span style={{fontSize:10}}>km/s</span>
                        </div>
                      </div>
                      <div>
                        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--dim)",marginBottom:4}}>RADIANT AREA</div>
                        <div style={{fontSize:16,color:"#38bdf8"}}>
                          {res.radiant_ellipse?.area_deg2?.toFixed(2) || "0.00"} <span style={{fontSize:10}}>deg²</span>
                        </div>
                      </div>
                      <div>
                        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--dim)",marginBottom:4}}>RA UNCERTAINTY</div>
                        <div style={{fontSize:14}}>±{res.radiant_ra?.std?.toFixed(2) || "0.00"}°</div>
                      </div>
                      <div>
                        <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--dim)",marginBottom:4}}>DEC UNCERTAINTY</div>
                        <div style={{fontSize:14}}>±{res.radiant_dec?.std?.toFixed(2) || "0.00"}°</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
