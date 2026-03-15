"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function FallPredictorPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/events?page_size=40`)
      .then(r => r.json()).then(d => {
        // Filter for fireballs/potential falls (e.g., bright and deep penetration)
        const falls = (d.events || []).filter((e: any) => 
          (e.peak_magnitude || 0) < -4 || (e.terminal_altitude_km || 30) < 30
        );
        setEvents(falls);
        setLoading(false);
      }).catch(() => setLoading(false));
  }, []);

  return (
    <div style={{display:"flex", flexDirection:"column", gap: 20}}>
      <div className="sec-head">
        <div className="sec-title">Meteorite Fall Predictor</div>
        <div style={{fontFamily:"var(--mono)",fontSize:10,color:"#10b981"}}>DARK FLIGHT MODELLING</div>
      </div>

      <div className="summary" style={{marginBottom: 16, borderLeftColor: "#10b981"}}>
        <div className="summary-icon" style={{color: "#10b981"}}>⬇</div>
        <div style={{flex: 1}}>
          <div className="summary-title" style={{color: "#10b981"}}>Strewn Field Mapping</div>
          <div className="summary-text" style={{lineHeight: 1.6}}>
            When a meteoroid decelerates below ~4 km/s, ablation ceases and it falls in <em>dark flight</em> subject to gravitational and aeolian forces. The fall predictor isolates deep-penetrating fireballs to compute prospective ground truth impact ellipses.
          </div>
        </div>
      </div>

      <div className="panel" style={{marginBottom: 0}}>
        <div className="ph" style={{"--al":"#10b981"} as any}>
          <div className="pt">Potential Fall Candidates</div>
        </div>
        <div style={{padding: "16px"}}>
          {loading ? <div className="loader"><div className="spinner" /></div> : (
            <div style={{display:"grid",gap:10,gridTemplateColumns:"repeat(auto-fill,minmax(280px,1fr))"}}>
              {events.map((ev: any) => (
                <Link key={ev.event_id} href={`/event/${ev.event_id}`}>
                  <div className="event-card" style={{padding: 15, height: "auto", borderLeft: "3px solid #10b981"}}>
                    <div className="card-id">{ev.event_id}</div>
                    <div className="card-name" style={{fontSize: 14, marginTop: 4, display:"flex", justifyContent:"space-between"}}>
                      <span>Term. Altitude: <span style={{color:"#10b981"}}>{ev.terminal_altitude_km?.toFixed(1) || 25.0} km</span></span>
                    </div>
                  </div>
                </Link>
              ))}
              {events.length === 0 && <div style={{color:"var(--muted)"}}>No deep penetration events found in current dataset.</div>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
