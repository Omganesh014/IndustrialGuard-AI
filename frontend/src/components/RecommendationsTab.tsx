// frontend/src/components/RecommendationsTab.tsx
// Human-in-the-loop engineering review interface for prescriptive actions

import React, { useState } from "react";
import {
  UserCheck,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  AlertTriangle,
  ShieldAlert,
  Search,
} from "lucide-react";
import { api, RecommendationRecord } from "../lib/api";
import { RiskBadge } from "./RiskBadge";
import clsx from "clsx";

interface RecommendationsTabProps {
  recommendations: RecommendationRecord[];
  onRefresh: () => void;
}

export function RecommendationsTab({ recommendations, onRefresh }: RecommendationsTabProps) {
  const [filter, setFilter] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");
  const [reviewModal, setReviewModal] = useState<{
    id: string;
    action: "APPROVED" | "REJECTED";
    recommendationAction: string;
  } | null>(null);
  const [engineerId, setEngineerId] = useState<string>("engineer_001");
  const [correctiveAction, setCorrectiveAction] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const filtered = recommendations.filter((r) => {
    if (filter === "PENDING" && r.status !== "AWAITING_REVIEW") return false;
    if (filter === "APPROVED" && r.status !== "APPROVED") return false;
    if (filter === "REJECTED" && r.status !== "REJECTED") return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        r.action.toLowerCase().includes(q) ||
        r.record_id.toLowerCase().includes(q) ||
        (r.basis && r.basis.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const handleReviewSubmit = async () => {
    if (!reviewModal) return;
    if (!engineerId.trim()) {
      alert("Please provide an Engineer ID for the audit log.");
      return;
    }
    setSubmitting(true);
    try {
      await api.reviewRecommendation(
        reviewModal.id,
        reviewModal.action,
        engineerId,
        correctiveAction.trim() || undefined
      );
      setToastMessage(
        `Recommendation ${reviewModal.id} has been marked as ${reviewModal.action} by ${engineerId}.`
      );
      setTimeout(() => setToastMessage(null), 4000);
      setReviewModal(null);
      setCorrectiveAction("");
      onRefresh();
    } catch (e: unknown) {
      alert(`Review submission failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="rounded-lg border border-emerald-500/40 bg-emerald-950/60 p-4 text-emerald-300 text-xs font-mono shadow-[0_0_20px_rgba(16,185,129,0.2)] flex items-center justify-between">
          <span>✓ {toastMessage}</span>
          <button onClick={() => setToastMessage(null)} className="text-emerald-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-amber-400" />
            Human-in-the-Loop Review Queue
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Mandatory engineer sign-off gate before implementing prescriptive machine adjustments
          </p>
        </div>

        {/* Filter Chips */}
        <div className="flex flex-wrap items-center gap-2">
          {["ALL", "PENDING", "APPROVED", "REJECTED"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={clsx(
                "rounded-lg px-3 py-1.5 text-xs font-mono font-medium border transition-all",
                filter === f
                  ? "bg-blue-600/20 text-blue-300 border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.3)]"
                  : "bg-slate-900/60 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-200"
              )}
            >
              {f} ({recommendations.filter(r => f === "ALL" ? true : f === "PENDING" ? r.status === "AWAITING_REVIEW" : r.status === f).length})
            </button>
          ))}
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Filter recommendations by action, record ID, or basis..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-slate-900/60 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-blue-500/60"
        />
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center text-slate-400">
          <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm font-medium">No recommendations found in this category.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((rec) => {
            const isPending = rec.status === "AWAITING_REVIEW";
            return (
              <div
                key={rec.recommendation_id}
                className={clsx(
                  "rounded-xl border p-5 backdrop-blur-md transition-all flex flex-col justify-between space-y-4",
                  isPending
                    ? "border-amber-500/30 bg-amber-950/15 shadow-[0_0_15px_-5px_rgba(245,158,11,0.2)]"
                    : "border-slate-800/80 bg-slate-900/60"
                )}
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[10px] font-mono text-slate-500 uppercase">
                      ID: {rec.recommendation_id} · Record: {rec.record_id}
                    </span>
                    <RiskBadge level={rec.status} size="xs" />
                  </div>

                  <h4 className="text-sm font-semibold text-slate-100">{rec.action}</h4>

                  {rec.basis && (
                    <p className="text-xs text-slate-400 font-mono">
                      Basis: <span className="text-slate-300 font-semibold">{rec.basis}</span>
                      {rec.uncertainty && <span> · Uncertainty: {rec.uncertainty}</span>}
                    </p>
                  )}

                  {rec.evidence && (
                    <p className="text-xs text-slate-300 bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/60">
                      {rec.evidence}
                    </p>
                  )}

                  {rec.rag_source && (
                    <div className="flex items-center gap-1.5 text-[11px] text-blue-400 font-mono">
                      <FileText className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">RAG Knowledge: {rec.rag_source}</span>
                    </div>
                  )}

                  {rec.approved_by && (
                    <div className="text-[11px] font-mono text-slate-400 pt-1 border-t border-slate-800/60">
                      Reviewed by: <span className="text-emerald-400 font-semibold">{rec.approved_by}</span>
                      {rec.approval_timestamp && (
                        <span> at {new Date(rec.approval_timestamp).toLocaleTimeString()}</span>
                      )}
                      {rec.corrective_action && (
                        <p className="text-xs text-slate-300 mt-1">Action: {rec.corrective_action}</p>
                      )}
                    </div>
                  )}
                </div>

                {isPending && (
                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-3">
                    <span className="text-[11px] text-amber-400/90 font-mono">
                      Sign-off required
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() =>
                          setReviewModal({
                            id: rec.recommendation_id,
                            action: "APPROVED",
                            recommendationAction: rec.action,
                          })
                        }
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/40 text-emerald-300 text-xs font-medium transition-all"
                      >
                        <CheckCircle className="w-3.5 h-3.5" /> Approve
                      </button>
                      <button
                        onClick={() =>
                          setReviewModal({
                            id: rec.recommendation_id,
                            action: "REJECTED",
                            recommendationAction: rec.action,
                          })
                        }
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 text-rose-300 text-xs font-medium transition-all"
                      >
                        <XCircle className="w-3.5 h-3.5" /> Reject
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Review Modal Dialog */}
      {reviewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                {reviewModal.action === "APPROVED" ? (
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-400" />
                )}
                Confirm Recommendation {reviewModal.action}
              </h3>
              <button onClick={() => setReviewModal(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 text-xs font-mono text-slate-300">
              {reviewModal.recommendationAction}
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">
                  Engineer ID (Audit Trail) *
                </label>
                <input
                  type="text"
                  value={engineerId}
                  onChange={(e) => setEngineerId(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
                  placeholder="e.g. engineer_001"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">
                  Corrective Action / Engineering Notes (Optional)
                </label>
                <textarea
                  value={correctiveAction}
                  onChange={(e) => setCorrectiveAction(e.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-sans"
                  placeholder="Note reason for sign-off or physical tool replacement details..."
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setReviewModal(null)}
                className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleReviewSubmit}
                disabled={submitting}
                className={clsx(
                  "px-4 py-2 text-xs font-semibold rounded-lg text-white transition-all",
                  reviewModal.action === "APPROVED"
                    ? "bg-emerald-600 hover:bg-emerald-500"
                    : "bg-rose-600 hover:bg-rose-500"
                )}
              >
                {submitting ? "Recording..." : `Confirm ${reviewModal.action}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
