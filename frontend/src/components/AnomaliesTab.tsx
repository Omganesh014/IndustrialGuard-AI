// frontend/src/components/AnomaliesTab.tsx
// Dual anomaly detection monitor (IQR bounds + Isolation Forest)

import React, { useState } from "react";
import { AlertTriangle, Search, Filter, ShieldAlert, Cpu } from "lucide-react";
import { AnomalyRecord } from "../lib/api";
import { RiskBadge } from "./RiskBadge";
import clsx from "clsx";

interface AnomaliesTabProps {
  anomalies: AnomalyRecord[];
}

export function AnomaliesTab({ anomalies }: AnomaliesTabProps) {
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const filtered = anomalies.filter((a) => {
    if (severityFilter !== "ALL" && a.severity !== severityFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      const paramsMatch = (a.affected_parameters || []).some((p) =>
        p.parameter.toLowerCase().includes(q)
      );
      return a.record_id.toLowerCase().includes(q) || paramsMatch;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Dual Anomaly Detection Monitor
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Stage 1 evidentiary filtering combining empirical IQR limits with Isolation Forest scoring
          </p>
        </div>

        {/* Severity Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((s) => (
            <button
              key={s}
              onClick={() => setSeverityFilter(s)}
              className={clsx(
                "rounded-lg px-3 py-1.5 text-xs font-mono font-medium border transition-all",
                severityFilter === s
                  ? "bg-blue-600/20 text-blue-300 border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.3)]"
                  : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
              )}
            >
              {s} ({anomalies.filter(a => s === "ALL" ? true : a.severity === s).length})
            </button>
          ))}
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search by Record ID or Parameter (e.g. torque, tool_wear)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-slate-900/60 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500/60 font-mono"
        />
      </div>

      {/* Anomaly Table */}
      <div className="overflow-hidden rounded-xl border border-slate-800/80 bg-slate-900/60 backdrop-blur-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-[11px] font-mono uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">Record ID</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Statistical Violations</th>
                <th className="px-4 py-3">Isolation Forest Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 font-mono">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-slate-500 font-sans">
                    No anomalies recorded for this filter.
                  </td>
                </tr>
              ) : (
                filtered.map((a) => (
                  <tr key={a.anomaly_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3 text-slate-400 whitespace-nowrap">
                      {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : "—"}
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-100 whitespace-nowrap">
                      {a.record_id}
                    </td>
                    <td className="px-4 py-3">
                      <RiskBadge level={a.severity} size="xs" />
                    </td>
                    <td className="px-4 py-3">
                      {a.affected_parameters && a.affected_parameters.length > 0 ? (
                        <div className="space-y-1">
                          {a.affected_parameters.map((p, idx) => (
                            <span
                              key={idx}
                              className="inline-block mr-2 mb-1 px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 text-[11px]"
                            >
                              {p.parameter}: {p.value} ({p.direction} bounds by {p.deviation_iqr_units} IQR)
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-500 italic">Multivariate anomaly (No single parameter breach)</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {a.isolation_forest_score !== null && a.isolation_forest_score !== undefined
                        ? a.isolation_forest_score.toFixed(3)
                        : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
