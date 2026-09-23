// frontend/src/components/PipelineStageFlow.tsx
// Visual representation of the 4-agent evidential architecture

import React from "react";
import { CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, Microscope, Cpu, Sparkles } from "lucide-react";
import clsx from "clsx";

interface PipelineStageFlowProps {
  currentStage?: number;
  highlightDefect?: boolean;
}

export function PipelineStageFlow({ currentStage = 4, highlightDefect = false }: PipelineStageFlowProps) {
  const stages = [
    {
      step: 1,
      name: "Process Monitoring",
      role: "Physical range & dual anomaly checks (IQR + Isolation Forest)",
      icon: <Microscope className="w-4 h-4" />,
      color: "blue",
    },
    {
      step: 2,
      name: "Quality Analysis & RCA",
      role: "SHAP feature attribution & RAG knowledge grounding",
      icon: <Cpu className="w-4 h-4" />,
      color: "indigo",
    },
    {
      step: 3,
      name: "Defect Prediction",
      role: "Supervised XGBoost inference with calibrated risk probability",
      icon: <ShieldCheck className="w-4 h-4" />,
      color: highlightDefect ? "rose" : "blue",
    },
    {
      step: 4,
      name: "Process Optimization",
      role: "Prescriptive what-if parameter guidance & human review gate",
      icon: <Sparkles className="w-4 h-4" />,
      color: "emerald",
    },
  ];

  return (
    <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-5 backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            4-Agent Decision-Support Pipeline
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Evidential deterministic processing layered with IBM Granite synthesis
          </p>
        </div>
        <span className="text-[11px] font-mono text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded">
          Gate-Verified Workflow
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 relative">
        {stages.map((st, idx) => {
          const isCompleted = currentStage >= st.step;
          return (
            <div
              key={st.step}
              className={clsx(
                "relative rounded-lg border p-4 transition-all duration-200",
                isCompleted
                  ? "border-slate-700/80 bg-slate-800/40"
                  : "border-slate-800/40 bg-slate-900/30 opacity-60"
              )}
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="flex items-center gap-1.5 text-xs font-mono font-semibold text-slate-300">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-[10px] text-blue-400">
                    {st.step}
                  </span>
                  Stage {st.step}
                </span>
                <div className="text-slate-400">{st.icon}</div>
              </div>

              <h4 className="font-semibold text-sm text-slate-100">{st.name}</h4>
              <p className="mt-1 text-xs text-slate-400 leading-relaxed">{st.role}</p>

              <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono">
                <span className="text-slate-500">STATUS</span>
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  Active
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
