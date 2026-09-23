// frontend/src/components/RiskBadge.tsx
// Reusable risk level / severity badge

import React from "react";
import clsx from "clsx";

interface RiskBadgeProps {
  level: string;
  size?: "sm" | "md" | "lg";
}

const LEVEL_STYLES: Record<string, string> = {
  HIGH:          "bg-red-100 text-red-800 border-red-300",
  CRITICAL:      "bg-red-200 text-red-900 border-red-400",
  ELEVATED:      "bg-orange-100 text-orange-800 border-orange-300",
  ELEVATED_RISK: "bg-orange-100 text-orange-800 border-orange-300",
  MODERATE:      "bg-yellow-100 text-yellow-800 border-yellow-300",
  MEDIUM:        "bg-yellow-100 text-yellow-800 border-yellow-300",
  CAUTION:       "bg-yellow-100 text-yellow-800 border-yellow-300",
  LOW:           "bg-blue-100 text-blue-800 border-blue-300",
  NORMAL:        "bg-green-100 text-green-800 border-green-300",
  UNKNOWN:       "bg-gray-100 text-gray-600 border-gray-300",
  ERROR:         "bg-gray-200 text-gray-700 border-gray-400",
};

const SIZE_STYLES: Record<string, string> = {
  sm: "text-xs px-2 py-0.5",
  md: "text-sm px-2.5 py-1",
  lg: "text-base px-3 py-1.5",
};

export function RiskBadge({ level, size = "md" }: RiskBadgeProps) {
  const style = LEVEL_STYLES[level?.toUpperCase()] ?? LEVEL_STYLES.UNKNOWN;
  return (
    <span
      className={clsx(
        "inline-flex items-center font-semibold rounded border",
        style,
        SIZE_STYLES[size]
      )}
    >
      {level ?? "UNKNOWN"}
    </span>
  );
}

// frontend/src/components/MetricCard.tsx
// Reusable metric card for the overview dashboard

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  variant?: "default" | "warning" | "danger" | "success";
  sourceLabel?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  variant = "default",
  sourceLabel,
}: MetricCardProps) {
  const borderColor = {
    default: "border-gray-200",
    warning: "border-yellow-300",
    danger: "border-red-300",
    success: "border-green-300",
  }[variant];

  const valueColor = {
    default: "text-gray-900",
    warning: "text-yellow-700",
    danger: "text-red-700",
    success: "text-green-700",
  }[variant];

  return (
    <div className={`bg-white rounded-lg border-2 ${borderColor} p-4 flex flex-col gap-1`}>
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{title}</span>
      <span className={`text-2xl font-bold ${valueColor}`}>{value}</span>
      {subtitle && <span className="text-xs text-gray-500">{subtitle}</span>}
      {sourceLabel && (
        <span className="text-[10px] text-gray-400 mt-1 font-mono">{sourceLabel}</span>
      )}
    </div>
  );
}
