"use client";

// frontend/src/pages/index.tsx (or app/page.tsx in Next.js App Router)
// Dashboard Overview page — the top-level view engineers see first

import React, { useState } from "react";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { MetricCard } from "../components/RiskBadge";
import { RiskBadge } from "../components/RiskBadge";
import { api, QualityMetrics, AnomalyRecord, PredictionRecord, RecommendationRecord } from "../lib/api";

// ── Simple data-fetching hook (avoids react-query dependency for scaffold) ─────
function useData<T>(fetcher: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    setLoading(true);
    fetcher()
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error };
}

// ── Overview Section ───────────────────────────────────────────────────────────
function OverviewSection({ metrics }: { metrics: QualityMetrics }) {
  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-700 mb-3">Overview — Last {metrics.period_hours}h</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-2">
        <MetricCard
          title="Records Processed"
          value={metrics.total_records}
          sourceLabel={metrics.data_source_note}
        />
        <MetricCard
          title="Anomalies Detected"
          value={metrics.anomaly_count}
          subtitle={`${metrics.high_severity_anomalies} high severity`}
          variant={metrics.high_severity_anomalies > 0 ? "danger" : "default"}
        />
        <MetricCard
          title="Predicted Defective"
          value={metrics.predicted_defective}
          subtitle={`${(metrics.defect_rate * 100).toFixed(1)}% of predictions`}
          variant={metrics.defect_rate > 0.1 ? "warning" : "success"}
        />
        <MetricCard
          title="Pending Reviews"
          value={metrics.pending_recommendations}
          subtitle="Awaiting engineer action"
          variant={metrics.pending_recommendations > 0 ? "warning" : "default"}
        />
      </div>
      <p className="text-xs text-gray-400 font-mono">{metrics.data_source_note}</p>
    </section>
  );
}

// ── Anomaly Table ──────────────────────────────────────────────────────────────
function AnomalyTable({ anomalies }: { anomalies: AnomalyRecord[] }) {
  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-700 mb-3">Recent Anomalies</h2>
      {anomalies.length === 0 ? (
        <p className="text-sm text-gray-400">No anomalies detected.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border border-gray-200 rounded-lg">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
              <tr>
                {["Time", "Record ID", "Severity", "Affected Parameters", "IF Score"].map((h) => (
                  <th key={h} className="px-3 py-2 text-left border-b border-gray-200">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {anomalies.slice(0, 10).map((a) => (
                <tr key={a.anomaly_id} className="hover:bg-gray-50 border-b border-gray-100">
                  <td className="px-3 py-2 text-gray-500 font-mono text-xs">
                    {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : "—"}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">{a.record_id}</td>
                  <td className="px-3 py-2">
                    <RiskBadge level={a.severity} size="sm" />
                  </td>
                  <td className="px-3 py-2 text-gray-600">
                    {(a.affected_parameters ?? []).map((p) => p.parameter).join(", ") || "—"}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">
                    {a.isolation_forest_score?.toFixed(3) ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

// ── Recommendations Panel ──────────────────────────────────────────────────────
function RecommendationsPanel({ recommendations }: { recommendations: RecommendationRecord[] }) {
  const pending = recommendations.filter((r) => r.status === "AWAITING_REVIEW");

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-700 mb-3">
        Recommendations Awaiting Review ({pending.length})
      </h2>
      {pending.length === 0 ? (
        <p className="text-sm text-gray-400">No pending recommendations.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {pending.slice(0, 5).map((rec) => (
            <div key={rec.recommendation_id} className="border border-yellow-200 bg-yellow-50 rounded-lg p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <p className="font-medium text-gray-800">{rec.action}</p>
                  {rec.basis && (
                    <p className="text-xs text-gray-500 mt-1">
                      Basis: <span className="font-mono">{rec.basis}</span>
                    </p>
                  )}
                  {rec.evidence && (
                    <p className="text-xs text-gray-600 mt-1">{rec.evidence}</p>
                  )}
                  {rec.rag_source && (
                    <p className="text-xs text-blue-600 mt-1">📄 RAG source: {rec.rag_source}</p>
                  )}
                  {rec.uncertainty && (
                    <p className="text-xs text-gray-400 mt-1">Uncertainty: {rec.uncertainty}</p>
                  )}
                </div>
                <RiskBadge level={rec.status} size="sm" />
              </div>
              <p className="text-xs text-orange-700 mt-2 font-medium">
                ⚠ Human engineer review required before any process action.
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

// ── Defect Probability Chart ───────────────────────────────────────────────────
function DefectProbabilityChart({ predictions }: { predictions: PredictionRecord[] }) {
  const chartData = predictions
    .slice(0, 20)
    .reverse()
    .map((p, i) => ({
      index: i + 1,
      probability: p.probability !== null ? +(p.probability * 100).toFixed(1) : null,
      isDefective: p.predicted_class === "DEFECTIVE" ? 1 : 0,
    }));

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-700 mb-3">
        Defect Prediction Probability — Recent Records
      </h2>
      {chartData.length === 0 ? (
        <p className="text-sm text-gray-400">No predictions yet. Submit records via POST /api/analyze.</p>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="index" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
            <Tooltip formatter={(v) => [`${v}%`, "Defect Probability"]} />
            <Line
              type="monotone"
              dataKey="probability"
              stroke="#ef4444"
              dot={{ r: 3 }}
              strokeWidth={2}
              connectNulls
            />
          </LineChart>
        </ResponsiveContainer>
      )}
      <p className="text-xs text-gray-400 mt-1 font-mono">
        Model output probability — not a certified measurement.
      </p>
    </section>
  );
}

// ── AI Chat Assistant ──────────────────────────────────────────────────────────
function ChatAssistant() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState<{ text: string; sources: string[] } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!message.trim()) return;
    setLoading(true);
    try {
      const res = await api.chat(message);
      setResponse({ text: res.response, sources: res.rag_sources });
    } catch (e) {
      setResponse({ text: `Error: ${String(e)}`, sources: [] });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section>
      <h2 className="text-lg font-semibold text-gray-700 mb-3">AI Assistant (Granite)</h2>
      <div className="flex gap-2 mb-3">
        <input
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
          placeholder='e.g. "Why was the last batch flagged?" or "What parameters are abnormal?"'
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
          onClick={handleSend}
          disabled={loading}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </div>
      {response && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-800 whitespace-pre-wrap">{response.text}</p>
          {response.sources.length > 0 && (
            <p className="text-xs text-blue-600 mt-2">
              Sources: {response.sources.join(", ")}
            </p>
          )}
          <p className="text-xs text-gray-400 mt-2">
            AI-generated response grounded in available data. Not certified engineering advice.
          </p>
        </div>
      )}
    </section>
  );
}

// ── Main Dashboard Page ────────────────────────────────────────────────────────
export default function Dashboard() {
  const { data: metrics, loading: mLoading } = useData(() => api.getMetrics(24));
  const { data: anomalies } = useData(() => api.getAnomalies(50));
  const { data: predictions } = useData(() => api.getPredictions(50));
  const { data: recommendations } = useData(() => api.getRecommendations(undefined, 50));

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">IndustrialGuard AI</h1>
          <p className="text-xs text-gray-500">
            Manufacturing Quality Control · Decision-Support Prototype · IBM Problem Statement #37
          </p>
        </div>
        <div className="text-xs text-orange-600 bg-orange-50 border border-orange-200 rounded px-3 py-1">
          ⚠ Decision-support system — not for autonomous machine control
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-100 px-6 py-2 flex gap-4 text-sm text-gray-600">
        {["Overview", "Process Monitoring", "Defect Prediction", "Anomaly Detection",
          "Explainability", "Recommendations", "Model Performance"].map((item) => (
          <a key={item} href="#" className="hover:text-blue-600 py-1">{item}</a>
        ))}
      </nav>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-6 flex flex-col gap-8">
        {mLoading ? (
          <p className="text-sm text-gray-400">Loading metrics...</p>
        ) : metrics ? (
          <OverviewSection metrics={metrics} />
        ) : null}

        <DefectProbabilityChart predictions={predictions ?? []} />
        <AnomalyTable anomalies={anomalies ?? []} />
        <RecommendationsPanel recommendations={recommendations ?? []} />
        <ChatAssistant />
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-8 px-6 py-4 text-xs text-gray-400 text-center">
        IndustrialGuard AI · IBM Problem Statement #37 · Decision-support prototype ·
        Not validated for certified industrial deployment ·
        All predictions require human engineer review
      </footer>
    </div>
  );
}
