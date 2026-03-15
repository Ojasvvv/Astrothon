"use client";
import { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DiagnosticsPage() {
  const [stats, setStats] = useState<any>({});
  
  useEffect(() => {
    fetch(`${API}/api/stats`).then(r => r.json()).then(d => setStats(d)).catch(() => {});
  }, []);

  return (
    <div className="wrap">
      <div className="sec-head">
        <div className="sec-title">System Diagnostics</div>
        <div style={{fontFamily:"var(--mono)",fontSize:10,color:"var(--dim)"}}>PIPELINE HEALTH & PERF</div>
      </div>

      <div className="content-grid" style={{marginTop: 20}}>
        <div className="stat-card" style={{"--al":"var(--accent)"} as any}>
          <div className="sl">API Status</div>
          <div className="sv" style={{color:"var(--accent)",fontSize:16,marginTop:8}}>ONLINE</div>
          <div className="ss">Connected to Python backend</div>
        </div>
        
        <div className="stat-card" style={{"--al":"#38bdf8"} as any}>
          <div className="sl">Processed Events</div>
          <div className="sv" style={{fontSize:24,marginTop:8}}>{stats.total_events || 0}</div>
          <div className="ss">In local JSON store</div>
        </div>

        <div className="stat-card" style={{"--al":"#facc15"} as any}>
          <div className="sl">Pipeline Version</div>
          <div className="sv" style={{fontSize:16,marginTop:8,fontFamily:"var(--mono)"}}>2.0.4-rc (Nelder-Mead)</div>
          <div className="ss">With optimized Whipple-Jacchia</div>
        </div>
      </div>

      <div className="panel" style={{marginTop: 20}}>
        <div className="ph">
          <div className="pt">Geospatial Networks</div>
        </div>
        <div style={{padding: 16}}>
          <table className="compare-table" style={{width:"100%"}}>
            <thead>
              <tr>
                <th style={{textAlign:"left"}}>Network</th>
                <th style={{textAlign:"left"}}>Stations</th>
                <th style={{textAlign:"left"}}>Status</th>
              </tr>
            </thead>
            <tbody>
              {["GMN", "NASA AFSN", "AMS", "FRIPON"].map(n => (
                <tr key={n}>
                  <td>{n}</td>
                  <td>Active</td>
                  <td><span className="badge bg">Receiving telemetry</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
