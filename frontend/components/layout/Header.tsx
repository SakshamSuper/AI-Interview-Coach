"use client";

import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

const PAGE_LABELS: Record<string, string> = {
  "/": "Dashboard",
  "/resume": "Resume Analysis",
  "/jobs": "Job Description",
  "/matching": "Match & Skill Gaps",
  "/knowledge": "Knowledge Base",
  "/interview": "Practice Interview",
  "/analytics": "Analytics",
  "/history": "History",
  "/settings": "Settings",
};

export function Header() {
  const pathname = usePathname();
  const [isOnline, setIsOnline] = useState<boolean | null>(null);

  useEffect(() => {
    async function check() {
      try {
        const res = await fetch("/api/py/health", { signal: AbortSignal.timeout(4000) });
        setIsOnline(res.ok);
      } catch {
        setIsOnline(false);
      }
    }
    check();
    const id = setInterval(check, 30000);
    return () => clearInterval(id);
  }, []);

  const pageLabel = PAGE_LABELS[pathname] ?? "AI Interview Coach";

  return (
    <header className="h-12 border-b border-slate-200 bg-white px-6 flex items-center justify-between shrink-0">
      <h1 className="text-sm font-semibold text-slate-800">{pageLabel}</h1>
      <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
        <span
          className={[
            "inline-flex w-1.5 h-1.5 rounded-full",
            isOnline === null ? "bg-slate-400" : isOnline ? "bg-emerald-500" : "bg-red-500",
          ].join(" ")}
        />
        <span>
          {isOnline === null ? "Connecting" : isOnline ? "API online" : "API offline"}
        </span>
      </div>
    </header>
  );
}
