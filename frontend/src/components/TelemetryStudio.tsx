// frontend/src/components/TelemetryStudio.tsx
// Interactive telemetry analyzer studio for running the 4-agent pipeline

import React, { useState } from "react";
import {
  Cpu,
  Play,
  RotateCcw,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  FileText,
  HelpCircle,
  Activity,
  Layers,
} from "lucide-react";
import { api, AnalyzeResponse } from "../lib/api";
import { RiskBadge } from "./RiskBadge";
import clsx from "clsx";

interface ParameterConfig {
  key: string;
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  normalMin: number;
  normalMax: number;
  description: string;
}

const PARAMETERS: ParameterConfig[] = [
  {
    key: "air_temperature",
    label: "Air Temperature",
    unit: "K",
    min: 295.0,
    max: 312.0,
    step: 0.1,
    normalMin: 298.0,
    normalMax: 304.5,
    description: "Ambient shop floor temperature surrounding CNC spindle",
  },
  {
    key: "process_temperature",
    label: "Process Temperature",
    unit: "K",
    min: 305.0,
    max: 320.0,
    step: 0.1,
    normalMin: 308.0,
    normalMax: 314.0,
    description: "Spindle motor & bearing operating thermodynamic temperature",
  },
  {
    key: "rotational_speed",
    label: "Rotational Speed",
    unit: "rpm",
    min: 1000.0,
    max: 2900.0,
    step: 5.0,
    normalMin: 1350.0,
    normalMax: 1800.0,
    description: "Chuck and tool rotational velocity",
  },
  {
    key: "torque",
    label: "Torque",
    unit: "Nm",
    min: 10.0,
    max: 85.0,
    step: 0.5,
    normalMin: 25.0,
    normalMax: 55.0,
    description: "Spindle drive shaft mechanical torque output",
  },
  {
    key: "tool_wear",
    label: "Tool Wear",
    unit: "min",
    min: 0.0,
    max: 270.0,
    step: 1.0,
    normalMin: 0.0,
    normalMax: 190.0,
    description: "Accumulated cutting tool time on current insert",
  },
];

const PRESETS: Record<string, { label: string; icon: string; params: Record<string, number> }> = {
  normal: {
    label: "Normal CNC Operation",
    icon: "🟢",
    params: {
      air_temperature: 300.1,
      process_temperature: 310.0,
      rotational_speed: 1525.0,
      torque: 39.2,
      tool_wear: 110.0,
    },
  },
  elevated: {
    label: "High Tool Wear & Elevated Torque",
    icon: "🟠",
    params: {
      air_temperature: 304.8,
      process_temperature: 315.2,
      rotational_speed: 1180.0,
      torque: 68.5,
      tool_wear: 235.0,
    },
  },
  critical: {
    label: "Critical Heat / Extreme Stress",
    icon: "🔴",
    params: {
      air_temperature: 307.5,
      process_temperature: 317.0,
      rotational_speed: 1100.0,
      torque: 75.0,
      tool_wear: 255.0,
    },
  },
  overstrain: {
    label: "High Power Strain Risk",
    icon: "🟡",
    params: {
      air_temperature: 301.8,
      process_temperature: 311.5,
      rotational_speed: 1350.0,
      torque: 63.0,
      tool_wear: 215.0,
    },
  },
};

interface TelemetryStudioProps {
  onAnalysisComplete?: () => void;
}

export function TelemetryStudio({ onAnalysisComplete }: TelemetryStudioProps) {
  const [params, setParams] = useState<Record<string, number>>(PRESETS.normal.params);
  const [activePreset, setActivePreset] = useState<string>("normal");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleParamChange = (key: string, val: number) => {
    setParams((prev) => ({ ...prev, [key]: val }));
    setActivePreset("");
  };

  const loadPreset = (presetKey: string) => {
    setActivePreset(presetKey);
    setParams(PRESETS[presetKey].params);
  };

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.analyze(params, {
        record_id: `STUDIO_${Date.now().toString(36).toUpperCase()}`,
        data_source_label: "STUDIO INTERACTIVE TELEMETRY",
      });
      setResult(res);
      if (onAnalysisComplete) onAnalysisComplete();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const stages = result?.pipeline_result?.stages;
  const pred = result?.prediction;
  const anomaly = stages?.process_monitoring?.anomaly_detection;
  const qa = stages?.quality_analysis;
  const opt = stages?.optimization;

  return (
    <div className="space-y-6">
      {/* Studio Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-blue-500" />
            Telemetry Studio & Simulation
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Simulate CNC sensor streams and observe the full 4-agent pipeline execution in real time
          </p>
        </div>

        {/* Quick Presets */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-mono text-slate-500 uppercase">Presets:</span>
          {Object.entries(PRESETS).map(([key, data]) => (
            <button
              key={key}
              onClick={() => loadPreset(key)}
              className={clsx(
                "rounded-lg px-2.5 py-1.5 text-xs font-medium border transition-all flex items-center gap-1.5",
                activePreset === key
                  ? "bg-blue-600/20 text-blue-300 border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.3)]"
                  : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
              )}
            >
              <span>{data.icon}</span>
              <span>{data.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Parameter Sliders */}
        <div className="lg:col-span-5 rounded-xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-md space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h3 className="text-sm font-semibold text-slate-200 font-mono uppercase tracking-wider">
              Sensor Parameters
            </h3>
            <button
              onClick={() => loadPreset("normal")}
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 font-mono"
            >
              <RotateCcw className="w-3 h-3" /> Reset
            </button>
          </div>

          <div className="space-y-4">
            {PARAMETERS.map((p) => {
              const val = params[p.key] ?? p.min;
              const isViolating = val < p.normalMin || val > p.normalMax;
              return (
                <div key={p.key} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-medium text-slate-300">{p.label}</span>
                    <div className="flex items-center gap-2">
                      <span
                        className={clsx(
                          "font-mono font-bold text-xs px-2 py-0.5 rounded border",
                          isViolating
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                            : "bg-slate-800/80 text-emerald-400 border-slate-700"
                        )}
                      >
                        {val.toFixed(1)} {p.unit}
                      </span>
                    </div>
                  </div>

                  <input
                    type="range"
                    min={p.min}
                    max={p.max}
                    step={p.step}
                    value={val}
                    onChange={(e) => handleParamChange(p.key, parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />

                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>Min: {p.min}</span>
                    <span className="text-slate-400">Normal: {p.normalMin}–{p.normalMax} {p.unit}</span>
                    <span>Max: {p.max}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <button
            onClick={runAnalysis}
            disabled={loading}
            className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-3 font-semibold text-sm text-white shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 transition-all cursor-pointer"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                <span>Running 4-Agent Pipeline...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Analyze CNC Record Now</span>
              </>
            )}
          </button>
        </div>

        {/* Right: Evidentiary Analysis Result */}
        <div className="lg:col-span-7 rounded-xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-md">
          {error && (
            <div className="p-4 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 text-sm mb-4">
              Error executing analysis: {error}
            </div>
          )}

          {!result && !loading && !error && (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 border border-dashed border-slate-800 rounded-lg">
              <div className="p-4 rounded-full bg-slate-800/60 border border-slate-700/60 text-slate-400 mb-3">
                <Cpu className="w-8 h-8" />
              </div>
              <h4 className="text-base font-semibold text-slate-200">No Active Analysis</h4>
              <p className="text-xs text-slate-400 max-w-sm mt-1">
                Select a preset on the top right or adjust parameter sliders, then click &ldquo;Analyze CNC Record Now&rdquo; to execute the multi-agent pipeline.
              </p>
            </div>
          )}

          {loading && (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4">
              <div className="w-12 h-12 rounded-full border-2 border-blue-500/20 border-t-blue-500 animate-spin" />
              <div>
                <h4 className="text-sm font-semibold text-slate-200 font-mono">
                  Processing Telemetry Pipeline
                </h4>
                <p className="text-xs text-slate-400 mt-1">
                  Executing physical validation, dual anomaly scoring, XGBoost classification, and RAG retrieval...
                </p>
              </div>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-5">
              {/* Verdict Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-lg border border-slate-800 bg-slate-800/40">
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                    Pipeline Run ID: {result.record_id}
                  </span>
                  <div className="flex items-center gap-2 mt-1">
                    <RiskBadge level={result.final_status} size="lg" />
                    <RiskBadge level={result.final_risk_level} size="lg" />
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                    Execution Latency
                  </span>
                  <div className="text-sm font-mono font-bold text-slate-200 mt-0.5">
                    {result.duration_ms} ms
                  </div>
                </div>
              </div>

              {/* Stage Breakdown Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Stage 1: Anomaly */}
                <div className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400 font-semibold uppercase flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                      Stage 1: Anomaly Detection
                    </span>
                    <RiskBadge level={anomaly?.severity ?? "NORMAL"} size="xs" />
                  </div>

                  <div className="text-xs space-y-1.5 pt-1">
                    <div className="flex justify-between text-slate-300">
                      <span>Status:</span>
                      <span className="font-mono">{anomaly?.is_anomaly ? "ABNORMAL" : "NORMAL"}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Isolation Forest Score:</span>
                      <span className="font-mono text-slate-200">
                        {anomaly?.isolation_forest_score !== undefined && anomaly?.isolation_forest_score !== null
                          ? anomaly.isolation_forest_score.toFixed(3)
                          : "—"}
                      </span>
                    </div>
                    {anomaly?.statistical_violations && anomaly.statistical_violations.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-800/60">
                        <span className="text-[11px] text-rose-400 font-semibold block mb-1">
                          Statistical Bounds Exceeded:
                        </span>
                        {anomaly.statistical_violations.map((v, i) => (
                          <div key={i} className="text-[11px] font-mono text-rose-300">
                            • {v.parameter}: {v.value} ({v.direction} bounds by {v.deviation_iqr_units} IQR units)
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Stage 3: Supervised Classification */}
                <div className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-4 space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400 font-semibold uppercase flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-blue-400" />
                      Stage 3: Defect Prediction
                    </span>
                    <RiskBadge level={pred?.predicted_class ?? "NORMAL"} size="xs" />
                  </div>

                  <div className="space-y-2 pt-1">
                    <div className="flex items-baseline justify-between">
                      <span className="text-xs text-slate-400">Defect Probability:</span>
                      <span className="text-sm font-mono font-bold text-slate-100">
                        {pred?.probability !== null && pred?.probability !== undefined
                          ? `${(pred.probability * 100).toFixed(1)}%`
                          : "0.0%"}
                      </span>
                    </div>

                    {/* Probability Progress Bar */}
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={clsx(
                          "h-full rounded-full transition-all duration-500",
                          (pred?.probability ?? 0) > 0.6
                            ? "bg-rose-500"
                            : (pred?.probability ?? 0) > 0.3
                            ? "bg-amber-500"
                            : "bg-emerald-500"
                        )}
                        style={{ width: `${Math.min(100, (pred?.probability ?? 0) * 100)}%` }}
                      />
                    </div>

                    <div className="text-[11px] text-slate-400 font-mono">
                      Model: {pred?.model_version ?? "XGBoost v1.0"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Stage 2: SHAP Feature Attributions */}
              {qa?.contributing_factors && qa.contributing_factors.length > 0 && (
                <div className="rounded-lg border border-slate-800/80 bg-slate-950/40 p-4 space-y-3">
                  <span className="text-xs font-mono text-slate-400 font-semibold uppercase flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
                    Stage 2: Root-Cause Analysis (SHAP Attributions)
                  </span>

                  <div className="space-y-2">
                    {qa.contributing_factors.map((f, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="font-mono text-slate-300">{f.feature}</span>
                          <span className="font-mono text-slate-400">
                            {f.importance !== undefined ? `${(f.importance * 100).toFixed(0)}% weight` : ""}
                          </span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={clsx(
                              "h-full rounded-full",
                              f.direction?.includes("increase") ? "bg-rose-500" : "bg-blue-500"
                            )}
                            style={{ width: `${Math.min(100, (f.importance ?? 0.2) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Stage 4: Prescriptive Recommendations */}
              {result.final_recommendations && result.final_recommendations.length > 0 && (
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 space-y-2">
                  <span className="text-xs font-mono text-amber-300 font-semibold uppercase flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    Stage 4: Prescriptive Guidance (Requires Review)
                  </span>

                  {result.final_recommendations.map((rec, i) => (
                    <div key={i} className="text-xs space-y-1 pt-1">
                      <p className="font-semibold text-slate-100">{rec.action}</p>
                      {rec.basis && (
                        <p className="text-slate-400 font-mono text-[11px]">
                          Evidential Basis: <span className="text-slate-300">{rec.basis}</span>
                        </p>
                      )}
                      {rec.evidence && (
                        <p className="text-slate-300 text-xs italic">{rec.evidence}</p>
                      )}
                      {rec.rag_source && (
                        <p className="text-blue-400 font-mono text-[10px]">
                          📄 Knowledge Base: {rec.rag_source}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
