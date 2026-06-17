"use client";

import { useEffect, useState } from "react";
import { getAlerts, analyzeAlert } from "@/lib/api";
import type { Alert, AnalysisResult } from "@/lib/types";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => { loadAlerts(); }, []);

  async function loadAlerts() {
    try {
      const data = await getAlerts({ limit: 100 });
      setAlerts(data);
    } catch {}
  }

  async function handleAnalyze(alertId: number) {
    setAnalyzing(true);
    try {
      const result = await analyzeAlert(alertId);
      setAnalysis(result);
      loadAlerts();
    } catch (e: any) {
      alert("Analysis failed: " + e.message);
    } finally {
      setAnalyzing(false);
    }
  }

  const filtered = filter === "all" ? alerts : alerts.filter(a => a.severity === filter);

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">🚨 Security Alerts</h1>
          <p className="sf-page-subtitle">{alerts.length} total alerts • AI-powered investigation</p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          {["all", "critical", "high", "medium", "low"].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`sf-btn sf-btn-sm ${filter === f ? "sf-btn-primary" : "sf-btn-secondary"}`}>
              {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: selectedAlert ? "1fr 1fr" : "1fr", gap: "20px" }}>
        {/* Alert List */}
        <div className="sf-card" style={{ overflow: "auto", maxHeight: "calc(100vh - 160px)" }}>
          {filtered.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--sf-text-muted)" }}>
              <div style={{ fontSize: "48px", marginBottom: "16px" }}>🛡️</div>
              <div style={{ fontSize: "16px", fontWeight: 600 }}>No alerts found</div>
              <div style={{ fontSize: "13px", marginTop: "8px" }}>Run demo scenarios to generate security alerts</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {filtered.map(a => (
                <div key={a.id} onClick={() => { setSelectedAlert(a); setAnalysis(null); }}
                  style={{
                    padding: "16px", borderRadius: "10px", cursor: "pointer",
                    background: selectedAlert?.id === a.id ? "rgba(99, 102, 241, 0.08)" : "rgba(255,255,255,0.02)",
                    border: `1px solid ${selectedAlert?.id === a.id ? "rgba(99, 102, 241, 0.3)" : "var(--sf-border)"}`,
                    transition: "all 0.2s ease",
                  }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                    <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--sf-text-primary)", flex: 1 }}>{a.title}</div>
                    <span className={`sf-badge ${a.severity}`}>{a.severity}</span>
                  </div>
                  <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                    <span className={`sf-badge ${a.priority?.toLowerCase()}`}>{a.priority}</span>
                    <span className={`sf-badge ${a.status}`}>{a.status}</span>
                    {a.mitre_id && <span style={{ fontSize: "11px", fontFamily: "monospace", color: "var(--sf-accent-light)", background: "rgba(99,102,241,0.1)", padding: "2px 8px", borderRadius: "4px" }}>{a.mitre_id}</span>}
                    {a.source_ip && <span style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>📍 {a.source_ip}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Alert Detail Panel */}
        {selectedAlert && (
          <div className="sf-card sf-animate-in" style={{ overflow: "auto", maxHeight: "calc(100vh - 160px)" }}>
            <div style={{ marginBottom: "20px" }}>
              <h2 style={{ fontSize: "18px", fontWeight: 700, marginBottom: "8px" }}>{selectedAlert.title}</h2>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "12px" }}>
                <span className={`sf-badge ${selectedAlert.severity}`}>{selectedAlert.severity}</span>
                <span className={`sf-badge ${selectedAlert.priority?.toLowerCase()}`}>{selectedAlert.priority}</span>
                <span className={`sf-badge ${selectedAlert.status}`}>{selectedAlert.status}</span>
              </div>
              <p style={{ fontSize: "13px", color: "var(--sf-text-secondary)", lineHeight: 1.6 }}>{selectedAlert.description}</p>
            </div>

            {/* MITRE ATT&CK Info */}
            {selectedAlert.mitre_id && (
              <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(99,102,241,0.05)", border: "1px solid rgba(99,102,241,0.15)", marginBottom: "16px" }}>
                <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--sf-accent-light)", marginBottom: "6px" }}>MITRE ATT&CK</div>
                <div style={{ fontSize: "14px", fontWeight: 600 }}>{selectedAlert.mitre_id} — {selectedAlert.mitre_technique_name}</div>
                <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Tactic: {selectedAlert.mitre_tactic}</div>
              </div>
            )}

            {/* Evidence */}
            {selectedAlert.evidence && Object.keys(selectedAlert.evidence).length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <div style={{ fontSize: "13px", fontWeight: 700, marginBottom: "8px" }}>📋 Evidence</div>
                <pre style={{ fontSize: "11px", background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", overflow: "auto", maxHeight: "200px", color: "var(--sf-text-secondary)" }}>
                  {JSON.stringify(selectedAlert.evidence, null, 2)}
                </pre>
              </div>
            )}

            {/* AI Analysis Button */}
            {!analysis && (
              <button className="sf-btn sf-btn-primary sf-btn-lg" style={{ width: "100%", justifyContent: "center" }}
                onClick={() => handleAnalyze(selectedAlert.id)} disabled={analyzing}>
                {analyzing ? "🔄 AI Analyzing..." : "🤖 Run AI Investigation"}
              </button>
            )}

            {/* AI Analysis Results */}
            {analysis && (
              <div className="sf-animate-in" style={{ marginTop: "16px" }}>
                <h3 style={{ fontSize: "16px", fontWeight: 700, marginBottom: "12px" }}>🤖 AI Investigation Results</h3>

                {/* Multi-LLM Banner */}
                {analysis.multi_llm && analysis.agent_providers && (
                  <div style={{
                    padding: "14px 18px", borderRadius: "10px", marginBottom: "16px",
                    background: "linear-gradient(135deg, rgba(99,102,241,0.08), rgba(168,85,247,0.08))",
                    border: "1px solid rgba(139,92,246,0.3)",
                  }}>
                    <div style={{ fontSize: "12px", fontWeight: 700, color: "#a78bfa", marginBottom: "10px" }}>
                      ⚡ Multi-LLM Agent Pipeline
                    </div>
                    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                      {Object.entries(analysis.agent_providers).map(([key, info]: [string, any]) => (
                        <div key={key} style={{
                          display: "flex", alignItems: "center", gap: "6px",
                          padding: "4px 10px", borderRadius: "6px", fontSize: "11px",
                          background: info.llm === "gemini" ? "rgba(66,133,244,0.15)" : "rgba(239,68,68,0.15)",
                          border: `1px solid ${info.llm === "gemini" ? "rgba(66,133,244,0.3)" : "rgba(239,68,68,0.3)"}`,
                          color: info.llm === "gemini" ? "#93c5fd" : "#fca5a5",
                        }}>
                          <span>{info.llm === "gemini" ? "🔵" : "🔴"}</span>
                          <span style={{ fontWeight: 600, textTransform: "capitalize" }}>{key}</span>
                          <span style={{ opacity: 0.7 }}>→ {info.llm === "gemini" ? "Google Gemini" : "xAI Grok"}</span>
                          {info.ai_powered && <span style={{ color: "#4ade80" }}>✓</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Triage */}
                <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--sf-border)", marginBottom: "12px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--sf-accent-light)" }}>🎯 Triage Agent</span>
                    <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "4px", background: "rgba(66,133,244,0.15)", color: "#93c5fd", fontWeight: 600 }}>
                      🔵 Gemini
                    </span>
                  </div>
                  <div style={{ fontSize: "13px", lineHeight: 1.6, color: "var(--sf-text-secondary)" }}>
                    <div><strong>Priority:</strong> {analysis.triage?.priority} | <strong>False Positive:</strong> {((analysis.triage?.false_positive_score || 0) * 100).toFixed(0)}%</div>
                    <div style={{ marginTop: "4px" }}>{analysis.triage?.triage_summary}</div>
                  </div>
                </div>

                {/* Investigation */}
                <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--sf-border)", marginBottom: "12px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--sf-warning)" }}>🔍 Investigation Agent</span>
                    <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "4px", background: "rgba(239,68,68,0.15)", color: "#fca5a5", fontWeight: 600 }}>
                      🔴 Grok
                    </span>
                  </div>
                  <div style={{ fontSize: "13px", lineHeight: 1.6, color: "var(--sf-text-secondary)" }}>
                    <div><strong>What happened:</strong> {analysis.investigation?.what_happened}</div>
                    <div style={{ marginTop: "8px" }}><strong>Root cause:</strong> {analysis.investigation?.why_it_happened}</div>
                    <div style={{ marginTop: "8px" }}><strong>Risk:</strong> {analysis.investigation?.risk_assessment}</div>
                  </div>
                </div>

                {/* Remediation */}
                <div style={{ padding: "14px", borderRadius: "10px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--sf-border)", marginBottom: "12px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--sf-success)" }}>🔧 Remediation Agent</span>
                    <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "4px", background: "rgba(66,133,244,0.15)", color: "#93c5fd", fontWeight: 600 }}>
                      🔵 Gemini
                    </span>
                  </div>
                  <div style={{ fontSize: "13px", lineHeight: 1.6, color: "var(--sf-text-secondary)", whiteSpace: "pre-wrap" }}>
                    {analysis.remediation?.remediation_summary || "Remediation plan generated"}
                  </div>
                </div>

                {/* Meta */}
                <div style={{ display: "flex", gap: "12px", fontSize: "11px", color: "var(--sf-text-muted)", flexWrap: "wrap", alignItems: "center" }}>
                  <span>Confidence: {(analysis.confidence * 100).toFixed(0)}%</span>
                  <span>Time: {analysis.processing_time_ms}ms</span>
                  {analysis.ticket_created && <span>Ticket: #{analysis.ticket_created}</span>}
                  {analysis.incident_id && <span>Incident: #{analysis.incident_id}</span>}
                  {analysis.multi_llm && <span style={{ color: "#a78bfa", fontWeight: 600 }}>🔀 Multi-LLM</span>}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
