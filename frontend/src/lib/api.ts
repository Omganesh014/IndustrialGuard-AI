// frontend/src/lib/api.ts
// Typed API client for IndustrialGuard AI backend

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${error}`);
  }
  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────────

export interface QualityMetrics {
  period_hours: number;
  total_records: number;
  anomaly_count: number;
  high_severity_anomalies: number;
  predicted_defective: number;
  total_predictions: number;
  defect_rate: number;
  pending_recommendations: number;
  data_source_note: string;
}

export interface ProcessStatusRecord {
  record_id: string;
  timestamp: string | null;
  machine_id: string | null;
  quality_status: string | null;
  data_source_label: string;
}

export interface AnomalyRecord {
  anomaly_id: string;
  record_id: string;
  severity: string;
  anomaly_type: string | null;
  affected_parameters: Array<{
    parameter: string;
    value: number;
    normal_range: [number, number];
    direction: string;
    deviation_iqr_units: number;
  }> | null;
  isolation_forest_score: number | null;
  timestamp: string | null;
}

export interface PredictionRecord {
  prediction_id: string;
  record_id: string;
  predicted_class: string;
  probability: number | null;
  risk_level: string | null;
  model_version: string | null;
  timestamp: string | null;
}

export interface RecommendationRecord {
  recommendation_id: string;
  record_id: string;
  action: string;
  basis: string | null;
  evidence: string | null;
  rag_source: string | null;
  uncertainty: string | null;
  status: string;
  approved_by: string | null;
  approval_timestamp: string | null;
  corrective_action: string | null;
  timestamp: string | null;
}

export interface AnalyzeResponse {
  record_id: string;
  final_status: string;
  final_risk_level: string;
  prediction: {
    predicted_class: string;
    probability: number | null;
    model_version: string | null;
    is_defective: boolean | null;
  } | null;
  recommendations_count: number;
  pipeline_result: unknown;
  duration_ms: number;
  disclaimer: string;
}

export interface ChatResponse {
  response: string;
  rag_sources: string[];
  disclaimer: string;
}

// ── API Functions ──────────────────────────────────────────────────────────────

export const api = {
  health: () => apiFetch<{ status: string }>("/health"),

  getMetrics: (hours = 24) =>
    apiFetch<QualityMetrics>(`/api/metrics?hours=${hours}`),

  getProcessStatus: (limit = 20) =>
    apiFetch<ProcessStatusRecord[]>(`/api/process-status?limit=${limit}`),

  getAnomalies: (limit = 50) =>
    apiFetch<AnomalyRecord[]>(`/api/anomalies?limit=${limit}`),

  getPredictions: (limit = 50) =>
    apiFetch<PredictionRecord[]>(`/api/predictions?limit=${limit}`),

  getRecommendations: (status?: string, limit = 50) =>
    apiFetch<RecommendationRecord[]>(
      `/api/recommendations?limit=${limit}${status ? `&status=${status}` : ""}`
    ),

  analyze: (params: Record<string, number | string>, options?: {
    record_id?: string;
    machine_id?: string;
    data_source_label?: string;
  }) =>
    apiFetch<AnalyzeResponse>("/api/analyze", {
      method: "POST",
      body: JSON.stringify({
        parameters: params,
        ...options,
        data_source_label: options?.data_source_label ?? "USER-PROVIDED DATA",
      }),
    }),

  reviewRecommendation: (
    id: string,
    action: "APPROVED" | "REJECTED",
    reviewer_id: string,
    corrective_action?: string
  ) =>
    apiFetch(`/api/recommendations/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ action, reviewer_id, corrective_action }),
    }),

  chat: (message: string, record_id?: string) =>
    apiFetch<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, record_id }),
    }),

  getModelPerformance: () =>
    apiFetch<{ model_versions: unknown[]; note: string }>("/api/model-performance"),
};
