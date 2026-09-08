import React from "react";
import { cn } from "@/lib/utils/cn";

export interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  color?: "blue" | "emerald" | "amber" | "rose" | "purple";
  size?: "sm" | "md";
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showPercentage = true,
  color = "blue",
  size = "md",
  className,
  ...props
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const colors = {
    blue: "bg-blue-600",
    emerald: "bg-emerald-500",
    amber: "bg-amber-500",
    rose: "bg-rose-500",
    purple: "bg-violet-500",
  };

  const heights = {
    sm: "h-1.5",
    md: "h-2",
  };

  return (
    <div className={cn("w-full", className)} {...props}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between text-xs text-slate-600 mb-1.5">
          {label && <span className="font-medium">{label}</span>}
          {showPercentage && (
            <span className="font-semibold text-slate-700 tabular-nums">
              {percentage.toFixed(0)}%
            </span>
          )}
        </div>
      )}
      <div className={cn("w-full bg-slate-100 rounded-full overflow-hidden", heights[size])}>
        <div
          className={cn("h-full rounded-full transition-all duration-500 ease-out", colors[color])}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
