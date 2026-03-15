const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchEvents(params: Record<string, string> = {}) {
  const q = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/api/events?${q}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch events");
  return res.json();
}

export async function fetchEvent(id: string) {
  const res = await fetch(`${API_BASE}/api/events/${encodeURIComponent(id)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Event not found");
  return res.json();
}

export async function fetchTrajectory(id: string) {
  const res = await fetch(`${API_BASE}/api/events/${encodeURIComponent(id)}/trajectory`, { cache: "no-store" });
  if (!res.ok) throw new Error("Trajectory not found");
  return res.json();
}

export async function reconstruct(id: string) {
  const res = await fetch(`${API_BASE}/api/events/${encodeURIComponent(id)}/reconstruct`, { method: "POST" });
  if (!res.ok) throw new Error("Reconstruction failed");
  return res.json();
}

export async function runMonteCarlo(id: string, n = 100) {
  const res = await fetch(`${API_BASE}/api/events/${encodeURIComponent(id)}/montecarlo?n_iterations=${n}`, { method: "POST" });
  if (!res.ok) throw new Error("MC failed");
  return res.json();
}

export async function compareEvents(ids: string[]) {
  const res = await fetch(`${API_BASE}/api/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_ids: ids }),
  });
  if (!res.ok) throw new Error("Comparison failed");
  return res.json();
}

export async function fetchLiveFeed() {
  const res = await fetch(`${API_BASE}/api/livefeed`, { cache: "no-store" });
  if (!res.ok) throw new Error("Feed failed");
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/api/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error("Stats failed");
  return res.json();
}
