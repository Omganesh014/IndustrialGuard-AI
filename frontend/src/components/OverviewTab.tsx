// frontend/src/components/OverviewTab.tsx
// High-level operational overview dashboard with KPIs, charts, and pipeline stage flow

import React from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  ArrowUpRight,
  TrendingDown,
  TrendingUp,
  Cpu,
  ShieldAlert,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { MetricCard } from "./MetricCard";
import { RiskBadge } from "./RiskBadge";
import { PipelineStageFlow } from "./PipelineStageFlow";
import {
  QualityMetrics,
  AnomalyRecord,
  PredictionRecord,
  RecommendationRecord,
  ProcessStatusRecord,
} from "../lib/api";
import { TabKey } from "./Navbar";

interface OverviewTabProps {
  metrics: QualityMetrics | null;
  anomalies: AnomalyRecord[];
  predictions: PredictionRecord[];
  recommendations: RecommendationRecord[];
  processStatus: ProcessStatusRecord[];
  onNavigateTab: (tab: TabKey) => void;
}

export function OverviewTab({
  metrics,
  anomalies,
  predictions,
  recommendations,
  processStatus,
  onNavigateTab,
}: OverviewTabProps) {
  const pendingCount = recommendations.filter((r) => r.status === "AWAITING_REVIEW").length;
  const defectiveRate = metrics ? (metrics.defect_rate * 100).toFixed(1) : "0.0";

  // Prepare chart data from predictions
  const chartData = predictions
    .slice(0, 20)
    .reverse()
    .map((p, idx) => ({
      index: idx + 1,
      recordId: p.record_id,
      probability: p.probability !== null ? +(p.probability * 100).toFixed(1) : 0,
      threshold: 60,
    }));

  return (
    <div className="space-y-6">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Telemetry Records"
          value={metrics?.total_records ?? 0}
          subtitle={`Analyzed over past ${metrics?.period_hours ?? 24} hours`}
          variant="default"
          icon={<Cpu className="w-4 h-4 text-blue-400" />}
          sourceLabel={metrics?.data_source_note}
        />
        <MetricCard
          title="Anomalies Detected"
          value={metrics?.anomaly_count ?? 0}
          subtitle={`${metrics?.high_severity_anomalies ?? 0} classified as HIGH severity`}
          variant={(metrics?.anomaly_count ?? 0) > 0 ? "warning" : "default"}
          icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
          badge={<RiskBadge level="Dual IQR+IF" size="xs" />}
        />
        <MetricCard
          title="Predicted Defects"
          value={metrics?.predicted_defective ?? 0}
          subtitle={`${defectiveRate}% of total production batches`}
          variant={(metrics?.defect_rate ?? 0) > 0.15 ? "danger" : "default"}
          icon={<ShieldAlert className="w-4 h-4 text-rose-400" />}
          badge={<RiskBadge level="XGBoost v1.0" size="xs" />}
        />
        <MetricCard
          title="Pending Reviews"
          value={pendingCount}
          subtitle="Human engineer sign-offs needed"
          variant={pendingCount > 0 ? "warning" : "success"}
          icon={<CheckCircle2 className="w-4 h-4 text-amber-400" />}
          badge={
            pendingCount > 0 ? (
              <button
                onClick={() => onNavigateTab("recommendations")}
                className="text-[10px] font-mono text-amber-400 hover:underline flex items-center gap-0.5"
              >
                Review <ArrowUpRight className="w-3 h-3" />
              </button>
            ) : undefined
          }
        />
      </div>

      {/* 4-Agent Pipeline Flow Visualizer */}
      <PipelineStageFlow />

      {/* Charts & Status Two-Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Defect Probability Trend */}
        <div className="lg:col-span-8 rounded-xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-md space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold text-slate-200 font-mono uppercase tracking-wider">
                Defect Probability Trend (Recent Records)
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Calibrated XGBoost posterior risk probability with 60% decision boundary
              </p>
            </div>
            <button
              onClick={() => onNavigateTab("telemetry")}
              className="text-xs text-blue-400 hover:text-blue-300 font-mono flex items-center gap-1 bg-blue-500/10 px-2.5 py-1 rounded-lg border border-blue-500/20"
            >
              + Simulate New Batch <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="h-64 w-full">
            {chartData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No recent telemetry records. Use the Telemetry Studio to analyze records.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="index" tick={{ fontSize: 10, fill: "#64748b" }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#64748b" }} unit="%" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "8px",
                      fontSize: "11px",
                      color: "#f8fafc",
                    }}
                    formatter={(val: number) => [`${val}%`, "Defect Probability"]}
                    labelFormatter={(idx) => `Sample #${idx}`}
                  />
                  <ReferenceLine
                    y={60}
                    stroke="#ef4444"
                    strokeDasharray="4 4"
                    label={{
                      value: "High Risk Threshold (60%)",
                      fill: "#ef4444",
                      fontSize: 10,
                      position: "insideTopRight",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="probability"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ r: 3, fill: "#3b82f6", strokeWidth: 0 }}
                    activeDot={{ r: 5, fill: "#60a5fa" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Right: Quick Recent Telemetry Stream */}
        <div className="lg:col-span-4 rounded-xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-md space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-200 font-mono uppercase tracking-wider">
                Recent Batch Log
              </h3>
              <button
                onClick={() => onNavigateTab("predictions")}
                className="text-xs text-slate-400 hover:text-slate-200 font-mono"
              >
                View All
              </button>
            </div>

            <div className="space-y-2">
              {processStatus.slice(0, 5).map((r) => (
                <div
                  key={r.record_id}
                  className="rounded-lg bg-slate-950/60 border border-slate-800/80 p-2.5 flex items-center justify-between text-xs"
                >
                  <div className="font-mono">
                    <span className="font-semibold text-slate-200 block truncate max-w-[140px]">
                      {r.record_id}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : "Recent"}
                    </span>
                  </div>
                  <RiskBadge level={r.quality_status ?? "UNKNOWN"} size="xs" />
                </div>
              ))}

              {processStatus.length === 0 && (
                <p className="text-xs text-slate-500 py-6 text-center">
                  No production records yet.
                </p>
              )}
            </div>
          </div>

          <div className="rounded-lg bg-blue-950/30 border border-blue-500/30 p-3">
            <span className="text-xs font-semibold text-blue-300 block mb-1">
              Ready to test a scenario?
            </span>
            <p className="text-[11px] text-slate-400 mb-2">
              Load and analyze simulated failure modes including Tool Wear, Heat Dissipation, and Power Strain.
            </p>
            <button
              onClick={() => onNavigateTab("telemetry")}
              className="w-full text-center py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-all"
            >
              Open Telemetry Studio
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
