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
  const [status, setStatus] = useState<"connecting" | "waking" | "online" | "offline">("connecting");

  useEffect(() => {
    let timerId: NodeJS.Timeout;
    let isMounted = true;
    let failCount = 0;

    async function check() {
      try {
        const res = await fetch("/api/py/health", { signal: AbortSignal.timeout(12000) });
        if (!isMounted) return;
        if (res.ok) {
          setStatus("online");
          failCount = 0;
          timerId = setTimeout(check, 30000);
        } else {
          failCount++;
          setStatus(failCount >= 3 ? "offline" : "waking");
          timerId = setTimeout(check, 5000);
        }
      } catch {
        if (!isMounted) return;
        failCount++;
        setStatus(failCount >= 3 ? "offline" : "waking");
        timerId = setTimeout(check, 5000);
      }
    }

    check();

    return () => {
      isMounted = false;
      clearTimeout(timerId);
    };
  }, []);

  const pageLabel = PAGE_LABELS[pathname] ?? "AI Interview Coach";

  return (
    <header className="h-12 border-b border-slate-200 bg-white px-6 flex items-center justify-between shrink-0">
      <h1 className="text-sm font-semibold text-slate-800">{pageLabel}</h1>
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <span
          className={[
            "inline-flex w-2 h-2 rounded-full transition-colors duration-300",
            status === "online"
              ? "bg-emerald-500 ring-2 ring-emerald-100"
              : status === "waking"
              ? "bg-amber-400 animate-pulse ring-2 ring-amber-100"
              : status === "connecting"
              ? "bg-slate-400 animate-pulse"
              : "bg-rose-500 ring-2 ring-rose-100",
          ].join(" ")}
        />
        <span className="font-medium text-[11px]">
          {status === "online"
            ? "API online"
            : status === "waking"
            ? "Waking up server..."
            : status === "connecting"
            ? "Connecting..."
            : "API offline"}
        </span>
      </div>
    </header>
  );
}
