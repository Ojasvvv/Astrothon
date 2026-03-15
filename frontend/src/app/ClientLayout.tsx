"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return mounted ? (
    <div className="shell">
      <Sidebar />
      <main className="main">{children}</main>
    </div>
  ) : (
    <div className="shell">
      <div style={{width: 200, borderRight: "1px solid var(--cb)"}} />
      <main className="main">
        {/* Empty layout placeholder pre-hydration */}
      </main>
    </div>
  );
}
