import React from "react";
import { cn } from "@/lib/utils/cn";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-8 text-center gap-3.5", className)}>
      {icon && (
        <div className="w-12 h-12 rounded-2xl bg-indigo-50/80 border border-indigo-100/90 flex items-center justify-center text-indigo-600 shadow-sm ring-4 ring-indigo-50/40">
          {icon}
        </div>
      )}
      <div className="max-w-sm">
        <p className="text-sm font-bold text-slate-800 tracking-tight">{title}</p>
        {description && <p className="text-xs text-slate-500 mt-1 leading-relaxed">{description}</p>}
      </div>
      {action && <div className="mt-1.5">{action}</div>}
    </div>
  );
}
