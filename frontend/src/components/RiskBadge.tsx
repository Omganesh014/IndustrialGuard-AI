// frontend/src/components/RiskBadge.tsx
// Reusable risk level / severity badge with dark-industrial styling

import React from "react";
import clsx from "clsx";

export interface RiskBadgeProps {
  level: string;
  size?: "xs" | "sm" | "md" | "lg";
  showDot?: boolean;
}

const LEVEL_STYLES: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  HIGH: {
    bg: "bg-rose-500/15",
    text: "text-rose-400",
    border: "border-rose-500/40",
    dot: "bg-rose-500",
  },
  CRITICAL: {
    bg: "bg-red-600/20",
    text: "text-red-400",
    border: "border-red-500/60 shadow-[0_0_12px_rgba(239,68,68,0.3)]",
    dot: "bg-red-500 animate-ping",
  },
  DEFECTIVE: {
    bg: "bg-rose-500/15",
    text: "text-rose-400",
    border: "border-rose-500/40",
    dot: "bg-rose-500",
  },
  ELEVATED: {
    bg: "bg-amber-500/15",
    text: "text-amber-400",
    border: "border-amber-500/40",
    dot: "bg-amber-500",
  },
  ELEVATED_RISK: {
    bg: "bg-amber-500/15",
    text: "text-amber-400",
    border: "border-amber-500/40",
    dot: "bg-amber-500",
  },
  MODERATE: {
    bg: "bg-yellow-500/15",
    text: "text-yellow-400",
    border: "border-yellow-500/30",
    dot: "bg-yellow-500",
  },
  MEDIUM: {
    bg: "bg-yellow-500/15",
    text: "text-yellow-400",
    border: "border-yellow-500/30",
    dot: "bg-yellow-500",
  },
  CAUTION: {
    bg: "bg-yellow-500/15",
    text: "text-yellow-400",
    border: "border-yellow-500/30",
    dot: "bg-yellow-500",
  },
  AWAITING_REVIEW: {
    bg: "bg-amber-500/15",
    text: "text-amber-300",
    border: "border-amber-500/40",
    dot: "bg-amber-400 animate-pulse",
  },
  APPROVED: {
    bg: "bg-emerald-500/15",
    text: "text-emerald-400",
    border: "border-emerald-500/40",
    dot: "bg-emerald-500",
  },
  REJECTED: {
    bg: "bg-slate-700/40",
    text: "text-slate-400",
    border: "border-slate-600/40",
    dot: "bg-slate-500",
  },
  LOW: {
    bg: "bg-blue-500/15",
    text: "text-blue-400",
    border: "border-blue-500/30",
    dot: "bg-blue-500",
  },
  NORMAL: {
    bg: "bg-emerald-500/15",
    text: "text-emerald-400",
    border: "border-emerald-500/40",
    dot: "bg-emerald-500",
  },
  UNKNOWN: {
    bg: "bg-slate-800/50",
    text: "text-slate-400",
    border: "border-slate-700/50",
    dot: "bg-slate-500",
  },
};

const SIZE_STYLES: Record<string, string> = {
  xs: "text-[10px] px-1.5 py-0.5 tracking-wider font-mono uppercase",
  sm: "text-xs px-2 py-0.5 tracking-wider font-mono uppercase",
  md: "text-xs px-2.5 py-1 tracking-wider font-mono uppercase",
  lg: "text-sm px-3.5 py-1.5 tracking-wider font-mono uppercase",
};

export function RiskBadge({ level, size = "md", showDot = true }: RiskBadgeProps) {
  const normalized = (level ?? "UNKNOWN").toUpperCase().replace(/[- ]/g, "_");
  const style = LEVEL_STYLES[normalized] ?? LEVEL_STYLES.UNKNOWN;

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 font-semibold rounded-md border backdrop-blur-sm transition-all duration-200",
        style.bg,
        style.text,
        style.border,
        SIZE_STYLES[size]
      )}
    >
      {showDot && <span className={clsx("w-1.5 h-1.5 rounded-full shrink-0", style.dot)} />}
      <span>{level ?? "UNKNOWN"}</span>
    </span>
  );
}
