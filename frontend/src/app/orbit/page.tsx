"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function OrbitExplorerPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/events?page_size=30`)
      .then(r => r.json()).then(d => { setEvents(d.events || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div style={{display:"flex", flexDirection:"column", gap: 20}}>
      <div className="sec-head">
        <div className="sec-title">Solar System Orbit Explorer</div>
        <div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--accent)"}}>HELIOCENTRIC KINEMATICS</div>
      </div>

      <div className="panel" style={{marginBottom: 20}}>
        <div className="ph" style={{"--al":"var(--accent3)"} as any}>
          <div className="pt">Select an event to view full orbital elements</div>
        </div>
        <div style={{padding: "20px"}}>
          {loading ? <div className="loader"><div className="spinner" /></div> : (
            <div style={{display:"grid",gap:10,gridTemplateColumns:"repeat(auto-fill,minmax(250px,1fr))"}}>
              {events.map((ev: any) => (
                <Link key={ev.event_id} href={`/event/${ev.event_id}`}>
                  <div className="event-card" style={{padding: 15, height: "auto"}}>
                    <div className="card-id">{ev.event_id}</div>
                    <div className="card-name" style={{fontSize: 14, marginTop: 4}}>
                      <span style={{color:"var(--accent)"}}>{ev.shower || "Sporadic"}</span> · {ev.estimated_velocity_kms?.toFixed(1)} km/s
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
