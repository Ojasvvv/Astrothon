"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Event {
  event_id: string;
  utc_timestamp: string;
  network: string;
  station_count: number;
  estimated_velocity_kms: number;
  peak_magnitude: number;
  shower: string;
  shower_code: string;
  trajectory_length_km: number;
  region: string;
  radiant_ra: number;
  radiant_dec: number;
}

const SHOWER_COLORS: Record<string, string> = {
  PER: "var(--accent2)", GEM: "var(--accent)", LEO: "var(--accent3)",
  QUA: "#38bdf8", ORI: "var(--accent2)", STA: "var(--accent2)",
  URS: "var(--accent3)", LYR: "#38bdf8", SPO: "#facc15",
};

function EventCardThumb({ event }: { event: Event }) {
  const color = SHOWER_COLORS[event.shower_code] || "var(--accent)";
  // Deterministic position from event_id hash
  const hash = event.event_id.split("").reduce((a: number, c: string) => a + c.charCodeAt(0), 0);
  const x1 = 60 + (hash % 120);
  const y1 = 10 + ((hash * 7) % 20);
  const x2 = 40 + ((hash * 13) % 100);
  const y2 = 50 + ((hash * 3) % 25);
  return (
    <svg viewBox="0 0 240 80" preserveAspectRatio="xMidYMid meet">
      <circle cx="30" cy="15" r="0.8" fill="rgba(255,255,255,.5)" />
      <circle cx="90" cy="10" r="1" fill="rgba(255,255,255,.6)" />
      <circle cx="200" cy="60" r="0.7" fill="rgba(255,255,255,.4)" />
      <line x1={x1} y1={y1} x2={x2} y2={y2}
        stroke={color} strokeWidth="1.8" strokeLinecap="round" opacity=".12" />
      <line x1={x1} y1={y1} x2={x2} y2={y2}
        stroke={color} strokeWidth="1.8" strokeLinecap="round" />
      <circle cx={x1} cy={y1} r="3.5" fill="none" stroke={color} strokeWidth="1.2" />
      <circle cx={x1} cy={y1} r="1.8" fill={color} />
      <circle cx={x2} cy={y2} r="2.5" fill="none" stroke="rgba(250,204,21,.8)" strokeWidth="1" />
      <circle cx={x2} cy={y2} r="1.5" fill="#facc15" />
      <circle cx={(x1+x2)/2-40} cy={y2+5} r="2" fill="none" stroke="rgba(74,244,196,.6)" strokeWidth=".9" />
      <line x1={(x1+x2)/2-40} y1={y2+5} x2={(x1+x2)/2} y2={(y1+y2)/2}
        stroke="rgba(74,244,196,.18)" strokeWidth=".6" strokeDasharray="2,2" />
    </svg>
  );
}

export default function CataloguePage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [network, setNetwork] = useState("");
  const [shower, setShower] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [feed, setFeed] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), page_size: "6" });
    if (network) params.set("network", network);
    if (shower) params.set("shower", shower);
    if (search) params.set("search", search);
    setLoading(true);
    fetch(`${API}/api/events?${params}`)
      .then(r => r.json())
      .then(d => { setEvents(d.events || []); setTotal(d.total || 0); })
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [page, network, shower, search]);

  useEffect(() => {
    fetch(`${API}/api/livefeed`).then(r => r.json()).then(d => setFeed(d.feed || [])).catch(() => {});
    fetch(`${API}/api/stats`).then(r => r.json()).then(d => setStats(d)).catch(() => {});
  }, []);

  const totalPages = Math.ceil(total / 6);

  return (
    <div className="wrap">
      <div>
        <div className="sec-head">
          <div className="sec-title">Event Catalogue</div>
          <div style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--muted)"}}>
            {total.toLocaleString()} EVENTS · SHOWING {events.length}
          </div>
        </div>

        <div className="filter-bar">
          <input className="search-box" placeholder="Search events…" type="text"
            value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
          {["", "GMN", "NASA_JPL_Fireball", "NASA_AFSN", "FRIPON", "AMS"].map(n => (
            <button key={n} className={`filter-chip ${network === n ? "active" : ""}`}
              onClick={() => { setNetwork(n); setPage(1); }}>
              {n || "All Networks"}
            </button>
          ))}
          <span style={{width:1,height:16,background:"var(--cb)",margin:"0 4px"}} />
          {["", "Geminids", "Eta Aquariids", "Lyrids", "Perseids", "Quadrantids", "Sporadic"].map(s => (
            <button key={s} className={`filter-chip orange ${shower === s ? "active" : ""}`}
              onClick={() => { setShower(s); setPage(1); }}>
              {s || "All Showers"}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="loader"><div className="spinner" /></div>
        ) : (
          <div className="events-grid">
            {events.map((ev, i) => (
              <Link key={ev.event_id} href={`/event/${encodeURIComponent(ev.event_id)}`}>
                <div className={`event-card ${i === 0 ? "featured" : ""}`}
                  style={{animationDelay: `${i * 0.03}s`}}>
                  <div className="card-thumb"><EventCardThumb event={ev} /></div>
                  <div className="card-body">
                    <div className="card-id">
                      {ev.network} · {ev.utc_timestamp?.replace("T", " · ").replace("Z", " UTC")}
                    </div>
                    <div className="card-name">
                      {ev.shower !== "Sporadic" ? `${ev.shower} ` : "Sporadic "} Event
                    </div>
                    <div className="card-meta">
                      <span className={`card-chip ${ev.shower === "Sporadic" ? "c-yel" : "c-org"}`}>
                        {ev.shower}
                      </span>
                      {(ev.peak_magnitude || 0) < -4 && (
                        <span className="card-chip c-org">Fireball</span>
                      )}
                      <span className="card-chip c-grn">{ev.station_count} stations</span>
                    </div>
                    <div className="card-stats">
                      <div className="cs-item">
                        <div className="cs-val">{ev.estimated_velocity_kms?.toFixed(1)}</div>
                        <div className="cs-lbl">km/s</div>
                      </div>
                      <div className="cs-item">
                        <div className="cs-val">{ev.peak_magnitude?.toFixed(1)}</div>
                        <div className="cs-lbl">mag</div>
                      </div>
                      <div className="cs-item">
                        <div className="cs-val">{Math.round(ev.trajectory_length_km || 0)}</div>
                        <div className="cs-lbl">km path</div>
                      </div>
                      <div className="cs-item">
                        <div className="cs-val" style={{color:"var(--accent)"}}>
                          {ev.station_count >= 3 ? "High" : ev.station_count >= 2 ? "Med" : "Est"}
                        </div>
                        <div className="cs-lbl">quality</div>
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

        <div className="pager">
          <span style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--dim)",marginRight:4}}>Page</span>
          {Array.from({length: Math.min(totalPages, 5)}, (_, i) => (
            <button key={i+1} className={`pg-btn ${page === i+1 ? "active" : ""}`}
              onClick={() => setPage(i+1)}>{i+1}</button>
          ))}
          {totalPages > 5 && (
            <span style={{fontFamily:"var(--mono)",fontSize:9,color:"var(--dim)",marginLeft:4}}>
              … {totalPages}
            </span>
          )}
        </div>
      </div>

      {/* RIGHT: Live feed + stats */}
      <div className="live-panel">
        <div className="feed-box">
          <div className="feed-head">
            <div className="sec-title" style={{fontSize:10}}>Live Feed</div>
            <div className="live-badge"><span className="blink-dot" />LIVE</div>
          </div>
          {feed.slice(0, 5).map((item, i) => (
            <Link key={i} href={`/event/${encodeURIComponent(item.event_id)}`}>
              <div className="feed-item">
                <div className="fi-row">
                  <div>
                    <div className="fi-id">{item.event_id}</div>
                    <div className="fi-name">{item.region}</div>
                    <div className="fi-loc">{item.network}</div>
                  </div>
                  <div className="fi-right">
                    <div className="fi-mag" style={{
                      color: (item.peak_magnitude || 0) < -6 ? "#facc15" :
                        (item.peak_magnitude || 0) < -3 ? "var(--accent2)" : "var(--muted)"
                    }}>{item.peak_magnitude != null ? item.peak_magnitude.toFixed(1) : "N/A"}</div>
                    <div className="fi-age">{item.station_count} st.</div>
                  </div>
                </div>
                <div className="fi-bar">
                  <div className="fi-bar-fill" style={{
                    width: `${Math.min(100, Math.abs(item.peak_magnitude || 1) * 12)}%`,
                    background: (item.peak_magnitude || 0) < -6 ? "#facc15" : "var(--accent2)"
                  }} />
                </div>
              </div>
            </Link>
          ))}
        </div>

        <div className="sparkline-panel">
          <div className="spark-title">Network Distribution · Events by Source</div>
          <svg width="100%" viewBox="0 0 260 55" style={{overflow:"visible"}}>
            <line x1="0" y1="55" x2="260" y2="55" stroke="rgba(255,255,255,.06)" strokeWidth=".5" />
            {(() => {
              const entries = Object.entries(stats.networks || {});
              const n = entries.length || 1;
              const barW = Math.min(40, Math.floor(240 / n) - 4);
              const spacing = Math.floor(260 / n);
              const maxN = Math.max(...entries.map(([,c]) => Number(c)), 1);
              const colors = ["var(--accent2)", "var(--accent)", "var(--accent3)", "#facc15", "#38bdf8", "#f472b6"];
              return entries.map(([name, count]: [string, any], i: number) => {
                const h = Math.max(5, (Number(count) / maxN) * 48);
                return (
                  <g key={name}>
                    <rect x={i * spacing + (spacing - barW) / 2} y={55-h} width={barW} height={h}
                      fill={colors[i % colors.length]} rx="2" opacity={0.8} />
                    <text x={i * spacing + spacing / 2} y="65" fill="rgba(255,255,255,.3)" fontSize="6"
                      fontFamily="'Space Mono',monospace" textAnchor="middle">{name.substring(0, 6)}</text>
                  </g>
                );
              });
            })()}
          </svg>
          <div style={{display:"flex",justifyContent:"space-between",marginTop:10}}>
            <div style={{textAlign:"center"}}>
              <div style={{fontFamily:"var(--mono)",fontSize:16,fontWeight:700}}>{stats.total_events || 0}</div>
              <div style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--dim)"}}>TOTAL</div>
            </div>
            <div style={{textAlign:"center"}}>
              <div style={{fontFamily:"var(--mono)",fontSize:16,fontWeight:700,color:"var(--accent)"}}>
                {stats.hourly_rate || 0}
              </div>
              <div style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--dim)"}}>PER HOUR</div>
            </div>
            <div style={{textAlign:"center"}}>
              <div style={{fontFamily:"var(--mono)",fontSize:16,fontWeight:700,color:"var(--accent2)"}}>
                {stats.fireballs || 0}
              </div>
              <div style={{fontFamily:"var(--mono)",fontSize:8,color:"var(--dim)"}}>FIREBALLS</div>
            </div>
          </div>
        </div>

        <div className="shower-panel">
          <div className="feed-head" style={{padding:"10px 16px"}}>
            <div className="sec-title" style={{fontSize:10}}>Shower Distribution</div>
          </div>
          {Object.entries(stats.showers || {}).slice(0, 5).map(([name, count], i) => {
            const maxCount = Math.max(...Object.values(stats.showers || {1: 1}).map(Number));
            const colors = ["var(--accent2)", "var(--accent)", "var(--accent3)", "#facc15", "#38bdf8"];
            return (
              <div className="shower-row" key={name}>
                <div className="sh-left">
                  <span className="sh-swatch" style={{background: colors[i % colors.length]}} />
                  <div>
                    <div className="sh-name">{name}</div>
                    <div className="sh-count">{String(count)} events</div>
                  </div>
                </div>
                <div className="sh-bar-wrap">
                  <div className="sh-bar" style={{
                    width: `${(Number(count) / maxCount) * 100}%`,
                    background: colors[i % colors.length]
                  }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
