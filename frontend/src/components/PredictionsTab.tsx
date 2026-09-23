// frontend/src/components/PredictionsTab.tsx
// Comprehensive defect predictions history table with filtering and probability bars

import React, { useState } from "react";
import { Activity, Search, Filter, ShieldCheck, AlertCircle, Clock } from "lucide-react";
import { PredictionRecord } from "../lib/api";
import { RiskBadge } from "./RiskBadge";
import clsx from "clsx";

interface PredictionsTabProps {
  predictions: PredictionRecord[];
}

export function PredictionsTab({ predictions }: PredictionsTabProps) {
  const [search, setSearch] = useState("");
  const [filterClass, setFilterClass] = useState<string>("ALL");

  const filtered = predictions.filter((p) => {
    if (filterClass === "DEFECTIVE" && p.predicted_class !== "DEFECTIVE") return false;
    if (filterClass === "NORMAL" && p.predicted_class !== "NORMAL") return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return p.record_id.toLowerCase().includes(q) || (p.model_version && p.model_version.toLowerCase().includes(q));
    }
    return true;
  });

  const defectiveCount = predictions.filter((p) => p.predicted_class === "DEFECTIVE").length;
  const normalCount = predictions.filter((p) => p.predicted_class === "NORMAL").length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            Supervised Defect Predictions Log
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Historical classification outputs from the trained XGBoost model (DECISION-007)
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {[
            { key: "ALL", label: `All Records (${predictions.length})` },
            { key: "DEFECTIVE", label: `Defective (${defectiveCount})` },
            { key: "NORMAL", label: `Normal (${normalCount})` },
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setFilterClass(item.key)}
              className={clsx(
                "rounded-lg px-3 py-1.5 text-xs font-mono font-medium border transition-all",
                filterClass === item.key
                  ? "bg-blue-600/20 text-blue-300 border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.3)]"
                  : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search by Record ID (e.g. SEED_NORMAL, STUDIO)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-slate-900/60 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500/60 font-mono"
        />
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-slate-800/80 bg-slate-900/60 backdrop-blur-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-[11px] font-mono uppercase tracking-wider text-slate-400">
              <tr>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">Record ID</th>
                <th className="px-4 py-3">Classification</th>
                <th className="px-4 py-3">Defect Probability</th>
                <th className="px-4 py-3">Risk Level</th>
                <th className="px-4 py-3">Model</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 font-mono">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-slate-500 font-sans">
                    No matching predictions found. Submit records using the Telemetry Studio.
                  </td>
                </tr>
              ) : (
                filtered.map((p) => {
                  const prob = p.probability !== null && p.probability !== undefined ? p.probability : 0;
                  const isHigh = prob > 0.6;
                  const isMed = prob > 0.3 && prob <= 0.6;
                  return (
                    <tr key={p.prediction_id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-4 py-3 text-slate-400 whitespace-nowrap">
                        {p.timestamp ? new Date(p.timestamp).toLocaleTimeString() : "—"}
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-100 whitespace-nowrap">
                        {p.record_id}
                      </td>
                      <td className="px-4 py-3">
                        <RiskBadge level={p.predicted_class} size="xs" />
                      </td>
                      <td className="px-4 py-3 w-48">
                        <div className="space-y-1">
                          <div className="flex justify-between text-[11px]">
                            <span>{(prob * 100).toFixed(1)}%</span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={clsx(
                                "h-full rounded-full",
                                isHigh ? "bg-rose-500" : isMed ? "bg-amber-500" : "bg-emerald-500"
                              )}
                              style={{ width: `${Math.min(100, prob * 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <RiskBadge level={p.risk_level ?? "UNKNOWN"} size="xs" />
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-[11px]">
                        {p.model_version ?? "v1.0"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
