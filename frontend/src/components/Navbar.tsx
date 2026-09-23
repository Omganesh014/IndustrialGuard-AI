// frontend/src/components/Navbar.tsx
// Top navigation bar with system status, active tabs, and problem statement branding

import React from "react";
import {
  LayoutDashboard,
  Cpu,
  Activity,
  AlertTriangle,
  UserCheck,
  BrainCircuit,
  Bot,
  Shield,
  Radio,
} from "lucide-react";
import clsx from "clsx";

export type TabKey =
  | "overview"
  | "telemetry"
  | "predictions"
  | "anomalies"
  | "recommendations"
  | "governance"
  | "assistant";

interface NavbarProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  isBackendHealthy: boolean | null;
  pendingCount?: number;
  anomalyCount?: number;
}

export function Navbar({
  activeTab,
  onTabChange,
  isBackendHealthy,
  pendingCount = 0,
  anomalyCount = 0,
}: NavbarProps) {
  const tabs: Array<{
    key: TabKey;
    label: string;
    icon: React.ReactNode;
    badgeCount?: number;
  }> = [
    { key: "overview", label: "Overview", icon: <LayoutDashboard className="w-4 h-4" /> },
    { key: "telemetry", label: "Telemetry Studio", icon: <Cpu className="w-4 h-4" /> },
    { key: "predictions", label: "Defect Analysis", icon: <Activity className="w-4 h-4" /> },
    {
      key: "anomalies",
      label: "Anomaly Monitor",
      icon: <AlertTriangle className="w-4 h-4" />,
      badgeCount: anomalyCount > 0 ? anomalyCount : undefined,
    },
    {
      key: "recommendations",
      label: "Human Review",
      icon: <UserCheck className="w-4 h-4" />,
      badgeCount: pendingCount > 0 ? pendingCount : undefined,
    },
    { key: "governance", label: "Model Governance", icon: <BrainCircuit className="w-4 h-4" /> },
    { key: "assistant", label: "Granite Assistant", icon: <Bot className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      {/* Top Banner */}
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)] ring-1 ring-blue-400/40">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-white">
                IndustrialGuard<span className="text-blue-500 font-mono">.AI</span>
              </span>
              <span className="rounded bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-mono font-medium text-blue-400 ring-1 ring-blue-500/30">
                IBM #37
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Agentic CNC Quality Control & Defect Prevention
            </p>
          </div>
        </div>

        {/* System Status Indicators */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs">
            <Radio className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400 font-mono text-[11px]">Backend Gateway:</span>
            {isBackendHealthy === null ? (
              <span className="text-slate-500 font-mono text-[11px]">Checking...</span>
            ) : isBackendHealthy ? (
              <span className="flex items-center gap-1.5 font-mono text-emerald-400 text-[11px]">
                <span className="h-2 w-2 rounded-full bg-emerald-500 radar-live" />
                ONLINE (8000)
              </span>
            ) : (
              <span className="flex items-center gap-1.5 font-mono text-rose-400 text-[11px]">
                <span className="h-2 w-2 rounded-full bg-rose-500" />
                OFFLINE
              </span>
            )}
          </div>

          <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-[11px] font-medium text-amber-300">
            ⚠ Decision-Support Only
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-t border-slate-800/60 bg-slate-900/40">
        <div className="mx-auto flex max-w-7xl overflow-x-auto px-4 sm:px-6">
          <nav className="flex space-x-1 py-1.5">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => onTabChange(tab.key)}
                  className={clsx(
                    "flex items-center gap-2 whitespace-nowrap rounded-lg px-3.5 py-2 text-xs font-medium transition-all duration-150",
                    isActive
                      ? "bg-blue-600/20 text-blue-400 border border-blue-500/40 shadow-[0_0_12px_rgba(59,130,246,0.2)]"
                      : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent"
                  )}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                  {tab.badgeCount !== undefined && tab.badgeCount > 0 && (
                    <span
                      className={clsx(
                        "ml-1 rounded-full px-1.5 py-0.2 text-[10px] font-mono font-semibold",
                        tab.key === "recommendations"
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                          : "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                      )}
                    >
                      {tab.badgeCount}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
