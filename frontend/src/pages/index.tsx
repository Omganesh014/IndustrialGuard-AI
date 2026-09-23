"use client";

// frontend/src/pages/index.tsx
// Production-grade IndustrialGuard AI Dashboard

import React, { useState, useEffect, useCallback } from "react";
import Head from "next/head";
import { Navbar, TabKey } from "../components/Navbar";
import { OverviewTab } from "../components/OverviewTab";
import { TelemetryStudio } from "../components/TelemetryStudio";
import { PredictionsTab } from "../components/PredictionsTab";
import { AnomaliesTab } from "../components/AnomaliesTab";
import { RecommendationsTab } from "../components/RecommendationsTab";
import { ModelGovernanceTab } from "../components/ModelGovernanceTab";
import { ChatAssistantTab } from "../components/ChatAssistantTab";
import {
  api,
  QualityMetrics,
  AnomalyRecord,
  PredictionRecord,
  RecommendationRecord,
  ProcessStatusRecord,
} from "../lib/api";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabKey>("overview");
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  const [metrics, setMetrics] = useState<QualityMetrics | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([]);
  const [predictions, setPredictions] = useState<PredictionRecord[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationRecord[]>([]);
  const [processStatus, setProcessStatus] = useState<ProcessStatusRecord[]>([]);

  // Comprehensive data loader
  const refreshAllData = useCallback(async () => {
    try {
      const [hRes, mRes, aRes, pRes, rRes, sRes] = await Promise.allSettled([
        api.health(),
        api.getMetrics(24),
        api.getAnomalies(50),
        api.getPredictions(50),
        api.getRecommendations(undefined, 50),
        api.getProcessStatus(20),
      ]);

      if (hRes.status === "fulfilled") {
        setIsBackendHealthy(true);
      } else {
        setIsBackendHealthy(false);
      }

      if (mRes.status === "fulfilled") setMetrics(mRes.value);
      if (aRes.status === "fulfilled") setAnomalies(aRes.value);
      if (pRes.status === "fulfilled") setPredictions(pRes.value);
      if (rRes.status === "fulfilled") setRecommendations(rRes.value);
      if (sRes.status === "fulfilled") setProcessStatus(sRes.value);
    } catch {
      setIsBackendHealthy(false);
    }
  }, []);

  useEffect(() => {
    refreshAllData();
    // Poll every 15 seconds to keep telemetry synchronized
    const interval = setInterval(refreshAllData, 15000);
    return () => clearInterval(interval);
  }, [refreshAllData]);

  const pendingCount = recommendations.filter((r) => r.status === "AWAITING_REVIEW").length;
  const anomalyCount = anomalies.length;

  return (
    <>
      <Head>
        <title>IndustrialGuard AI — CNC Quality Control & Defect Prevention</title>
        <meta
          name="description"
          content="Agentic AI Manufacturing Quality Control System for IBM Problem Statement #37"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-[#0a0d14] text-slate-100 flex flex-col justify-between selection:bg-blue-500 selection:text-white">
        {/* Navigation Header */}
        <Navbar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          isBackendHealthy={isBackendHealthy}
          pendingCount={pendingCount}
          anomalyCount={anomalyCount}
        />

        {/* Main Content Area */}
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
          {activeTab === "overview" && (
            <OverviewTab
              metrics={metrics}
              anomalies={anomalies}
              predictions={predictions}
              recommendations={recommendations}
              processStatus={processStatus}
              onNavigateTab={setActiveTab}
            />
          )}

          {activeTab === "telemetry" && (
            <TelemetryStudio onAnalysisComplete={refreshAllData} />
          )}

          {activeTab === "predictions" && (
            <PredictionsTab predictions={predictions} />
          )}

          {activeTab === "anomalies" && (
            <AnomaliesTab anomalies={anomalies} />
          )}

          {activeTab === "recommendations" && (
            <RecommendationsTab
              recommendations={recommendations}
              onRefresh={refreshAllData}
            />
          )}

          {activeTab === "governance" && <ModelGovernanceTab />}

          {activeTab === "assistant" && <ChatAssistantTab />}
        </main>

        {/* Compliance Footer */}
        <footer className="border-t border-slate-800/80 bg-slate-950/80 px-4 py-4 backdrop-blur-md sm:px-6">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-400">IndustrialGuard AI</span>
              <span>·</span>
              <span>IBM Problem Statement #37</span>
              <span>·</span>
              <span className="font-mono text-blue-400">Decision-Support Architecture</span>
            </div>

            <div className="text-[11px] text-slate-500">
              Deterministic Analytics + IBM Granite Narration · Requires Human Sign-off
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
