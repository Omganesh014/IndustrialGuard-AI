// frontend/src/components/MetricCard.tsx
// High-tech industrial metric card with glow accents and icons

import React from "react";
import clsx from "clsx";

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  variant?: "default" | "warning" | "danger" | "success" | "accent";
  sourceLabel?: string;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
}

export function MetricCard({
  title,
  value,
  subtitle,
  variant = "default",
  sourceLabel,
  icon,
  badge,
}: MetricCardProps) {
  const styles = {
    default: {
      card: "border-slate-800/80 hover:border-slate-700 bg-slate-900/60",
      value: "text-slate-100",
      accent: "from-slate-700/20 to-transparent",
    },
    warning: {
      card: "border-amber-500/30 hover:border-amber-500/50 bg-amber-950/20 shadow-[0_0_20px_-8px_rgba(245,158,11,0.25)]",
      value: "text-amber-300",
      accent: "from-amber-500/10 to-transparent",
    },
    danger: {
      card: "border-rose-500/40 hover:border-rose-500/60 bg-rose-950/25 shadow-[0_0_25px_-8px_rgba(244,63,94,0.3)]",
      value: "text-rose-400",
      accent: "from-rose-500/15 to-transparent",
    },
    success: {
      card: "border-emerald-500/30 hover:border-emerald-500/50 bg-emerald-950/20 shadow-[0_0_20px_-8px_rgba(16,185,129,0.25)]",
      value: "text-emerald-400",
      accent: "from-emerald-500/10 to-transparent",
    },
    accent: {
      card: "border-blue-500/40 hover:border-blue-500/60 bg-blue-950/20 shadow-[0_0_20px_-8px_rgba(59,130,246,0.25)]",
      value: "text-blue-400",
      accent: "from-blue-500/15 to-transparent",
    },
  }[variant];

  return (
    <div
      className={clsx(
        "relative overflow-hidden rounded-xl border p-5 backdrop-blur-md transition-all duration-300 group hover:-translate-y-0.5",
        styles.card
      )}
    >
      <div
        className={clsx(
          "pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br blur-xl opacity-60 transition-opacity group-hover:opacity-100",
          styles.accent
        )}
      />
      <div className="flex items-center justify-between gap-3 mb-2">
        <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase font-mono">
          {title}
        </span>
        {icon && (
          <div className="p-2 rounded-lg bg-slate-800/60 border border-slate-700/50 text-slate-300">
            {icon}
          </div>
        )}
        {badge && <div>{badge}</div>}
      </div>

      <div className="flex items-baseline gap-2">
        <span className={clsx("text-3xl font-bold font-mono tracking-tight", styles.value)}>
          {value}
        </span>
      </div>

      {subtitle && (
        <p className="mt-1 text-xs text-slate-400 font-medium">{subtitle}</p>
      )}

      {sourceLabel && (
        <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <span>SOURCE</span>
          <span className="text-slate-400 truncate max-w-[200px]">{sourceLabel}</span>
        </div>
      )}
    </div>
  );
}
