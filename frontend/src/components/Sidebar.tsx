"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { group: "Explore", items: [
    { label: "Live feed", href: "/", icon: "◉" },
    { label: "Catalogue", href: "/", icon: "≡" },
    { label: "Comparison", href: "/compare", icon: "❙❙" },
  ]},
  { group: "Analysis", items: [
    { label: "Orbit explorer", href: "/orbit", icon: "◎" },
    { label: "Monte Carlo", href: "/montecarlo", icon: "⤴" },
    { label: "Fall predictor", href: "/fall", icon: "⬇" },
    { label: "Sky radiant", href: "/radiant", icon: "✺" },
  ]},
  { group: "System", items: [
    { label: "Diagnostics", href: "/diagnostics", icon: "▐" },
    { label: "How it works", href: "/physics", icon: "⚛" },
  ]},
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <nav className="sidebar">
      <div className="wordmark">
        <div className="wm-top">System</div>
        <div className="wm-name" style={{letterSpacing:"0.15em"}}>BOLIDE</div>
        <div className="wm-sub">Meteor reconstruction</div>
      </div>
      {NAV_ITEMS.map(g => (
        <div key={g.group}>
          <div className="nav-group-label">{g.group}</div>
          {g.items.map(item => (
            <Link key={item.label} href={item.href}
              className={`nav-item ${pathname === item.href || (pathname.startsWith('/event') && item.href === '/event') ? "active" : ""}`}>
              <span className="nav-icon" style={{fontSize: 12, textAlign: "center"}}>{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </div>
      ))}
      <div className="sidebar-footer">
        <div className="sf-live"><span className="live-ring" />Feed active</div>
        <div className="sf-line">
          GMN · NASA AFSN<br/>
          AMS · FRIPON · IAU<br/>
          <span style={{color: "var(--accent)"}}>5 networks</span>
        </div>
      </div>
    </nav>
  );
}
