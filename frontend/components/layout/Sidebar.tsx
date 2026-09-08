"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut } from "next-auth/react";
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  GitMerge,
  BookOpen,
  Mic,
  BarChart3,
  History,
  Settings,
  BrainCircuit,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { useAuth } from "@/contexts/AuthContext";

const navigation = [
  {
    title: "Overview",
    items: [
      { name: "Dashboard", href: "/", icon: LayoutDashboard },
    ],
  },
  {
    title: "Prepare",
    items: [
      { name: "Resume", href: "/resume", icon: FileText },
      { name: "Job Description", href: "/jobs", icon: Briefcase },
      { name: "Match & Skill Gaps", href: "/matching", icon: GitMerge },
      { name: "Knowledge Base", href: "/knowledge", icon: BookOpen },
    ],
  },
  {
    title: "Interview",
    items: [
      { name: "Practice Interview", href: "/interview", icon: Mic },
    ],
  },
  {
    title: "Review",
    items: [
      { name: "History", href: "/history", icon: History },
      { name: "Analytics", href: "/analytics", icon: BarChart3 },
    ],
  },
  {
    title: "System",
    items: [
      { name: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

function getInitials(name: string) {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function Sidebar() {
  const pathname = usePathname();
  const { name, email, image, targetRole, isLoading } = useAuth();

  const displayName = isLoading ? "..." : name;
  const displaySub = isLoading ? "" : (targetRole || email || "No role set");

  return (
    <aside className="w-56 bg-slate-900 flex flex-col h-screen shrink-0">
      {/* Brand */}
      <div className="px-4 py-4 border-b border-slate-800 flex items-center gap-2.5">
        <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-blue-600 text-white flex-shrink-0">
          <BrainCircuit className="w-4 h-4" />
        </div>
        <div className="min-w-0">
          <div className="text-sm font-semibold text-white leading-tight truncate">
            Interview Coach
          </div>
          <div className="text-[10px] text-slate-400 leading-tight">AI-powered prep</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {navigation.map((section) => (
          <div key={section.title}>
            <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-2 mb-1">
              {section.title}
            </div>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                return (
                  <li key={item.name}>
                    <Link
                      href={item.href}
                      className={cn(
                        "flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-sm transition-colors duration-100",
                        isActive
                          ? "bg-blue-600 text-white font-medium"
                          : "text-slate-400 hover:text-white hover:bg-slate-800"
                      )}
                    >
                      <Icon
                        className={cn(
                          "w-4 h-4 flex-shrink-0",
                          isActive ? "text-white" : "text-slate-500"
                        )}
                      />
                      <span className="truncate">{item.name}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* User profile + sign out */}
      <div className="px-3 py-3 border-t border-slate-800 space-y-1">
        <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg bg-slate-800">
          {image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={image}
              alt={displayName}
              className="w-7 h-7 rounded-full flex-shrink-0 object-cover"
            />
          ) : (
            <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-[11px] font-bold text-white flex-shrink-0">
              {getInitials(displayName)}
            </div>
          )}
          <div className="min-w-0 flex-1">
            <div className="text-xs font-semibold text-slate-200 truncate">{displayName}</div>
            <div className="text-[10px] text-slate-500 truncate">{displaySub}</div>
          </div>
        </div>
        <button
          onClick={() => signOut({ callbackUrl: "/login" })}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-xs text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-colors duration-100"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}
