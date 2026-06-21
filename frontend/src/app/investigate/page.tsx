"use client";

import { useEffect, useState } from "react";
import { ShieldAlert, AlertTriangle, Activity, Search, Database, ExternalLink, RefreshCw, Zap } from "lucide-react";

export default function InvestigationWorkspace() {
  const [alertId, setAlertId] = useState<string>("");
  const [investigating, setInvestigating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>("");

  const handleInvestigate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!alertId.trim()) return;

    setInvestigating(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch(`http://localhost:8000/api/rag/investigate/alert?alert_id=${alertId}&use_agentic=true`, {
        method: "POST",
      });
      if (!res.ok) {
        throw new Error(await res.text());
      }
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Investigation failed");
    } finally {
      setInvestigating(false);
    }
  };

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">Investigation Workspace</h1>
          <p className="sf-page-subtitle">Agentic RAG-powered automated alert triage and contextual enrichment</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "350px 1fr", gap: "24px" }}>
        {/* Sidebar / Input */}
        <div>
          <form onSubmit={handleInvestigate} className="sf-card" style={{ padding: "20px", marginBottom: "20px" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, marginBottom: "16px" }}>Run Investigation</h3>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "12px", color: "var(--sf-text-muted)", marginBottom: "8px" }}>Alert ID</label>
              <input
                className="sf-input"
                style={{ width: "100%" }}
                placeholder="e.g. 1"
                value={alertId}
                onChange={(e) => setAlertId(e.target.value)}
              />
            </div>
            <button className="sf-btn sf-btn-primary" style={{ width: "100%", justifyContent: "center" }} type="submit" disabled={investigating || !alertId}>
              {investigating ? (
                <><RefreshCw size={14} className="spin" /> Analyzing...</>
              ) : (
                <><Search size={14} /> Investigate Alert</>
              )}
            </button>
          </form>

          {/* Quick links to demo alerts */}
          <div className="sf-card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "12px", color: "var(--sf-text-muted)", textTransform: "uppercase", marginBottom: "12px" }}>Demo Alerts</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {[
                { id: "1", label: "Brute Force Attack" },
                { id: "2", label: "Log4Shell Exploitation" },
                { id: "3", label: "Ransomware Activity" },
              ].map((demo) => (
                <button
                  key={demo.id}
                  onClick={() => { setAlertId(demo.id); }}
                  style={{
                    background: "rgba(255,255,255,0.03)", border: "1px solid var(--sf-border)",
                    padding: "10px", borderRadius: "6px", color: "var(--sf-text-secondary)",
                    cursor: "pointer", textAlign: "left", fontSize: "13px",
                  }}
                >
                  <strong style={{ color: "var(--sf-text-primary)" }}>ID {demo.id}</strong>: {demo.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Workspace */}
        <div className="sf-card" style={{ padding: "0", display: "flex", flexDirection: "column", minHeight: "500px" }}>
          <div className="sf-card-header" style={{ background: "rgba(255,255,255,0.02)" }}>
            <div className="sf-card-title">
              <Activity size={16} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} />
              Analysis Results
            </div>
          </div>

          <div style={{ padding: "24px", flex: 1, overflowY: "auto" }}>
            {investigating ? (
              <div style={{ textAlign: "center", paddingTop: "80px" }}>
                <div className="sf-loading-spinner" style={{ margin: "0 auto 20px" }} />
                <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--sf-text-primary)" }}>Agentic RAG Investigation in Progress</div>
                <div style={{ fontSize: "13px", color: "var(--sf-text-muted)", marginTop: "8px" }}>
                  Extracting alert context, identifying MITRE techniques, mapping to threat actors, and searching playbooks...
                </div>
              </div>
            ) : error ? (
              <div style={{ background: "rgba(220,38,38,0.1)", border: "1px solid rgba(220,38,38,0.3)", borderRadius: "8px", padding: "20px", color: "#f87171" }}>
                <AlertTriangle size={24} style={{ marginBottom: "12px" }} />
                <div style={{ fontWeight: 600, marginBottom: "4px" }}>Investigation Error</div>
                <div style={{ fontSize: "13px" }}>{error}</div>
              </div>
            ) : result ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                {/* Agent Metadata */}
                <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", padding: "16px", background: "rgba(99,102,241,0.05)", borderRadius: "8px", border: "1px solid rgba(99,102,241,0.2)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Zap size={16} color="#6366f1" />
                    <span style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Agent:</span>
                    <span style={{ fontSize: "13px", fontWeight: 600, color: "#a5b4fc" }}>{result.agent?.replace(/_/g, " ")}</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Database size={16} color="#10b981" />
                    <span style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Domain:</span>
                    <span style={{ fontSize: "13px", fontWeight: 600, color: "#10b981" }}>{result.domain}</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <Search size={16} color="#f59e0b" />
                    <span style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Extracted Queries:</span>
                    <span style={{ fontSize: "13px", fontWeight: 600, color: "#f59e0b" }}>{result.sub_queries?.length}</span>
                  </div>
                </div>

                {/* Sub Queries */}
                <div>
                  <h4 style={{ fontSize: "13px", fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: "12px", textTransform: "uppercase" }}>Generated Investigation Queries</h4>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                    {result.sub_queries?.map((q: string, i: number) => (
                      <span key={i} style={{ fontSize: "12px", background: "rgba(255,255,255,0.05)", padding: "6px 12px", borderRadius: "16px", color: "var(--sf-text-secondary)" }}>
                        {q}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Assembled Context Preview */}
                <div>
                  <h4 style={{ fontSize: "13px", fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: "12px", textTransform: "uppercase" }}>Assembled Context for LLM</h4>
                  <pre style={{
                    background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "8px", border: "1px solid var(--sf-border)",
                    fontSize: "12px", color: "var(--sf-text-secondary)", overflowX: "auto", whiteSpace: "pre-wrap",
                    maxHeight: "300px", overflowY: "auto", fontFamily: "monospace",
                  }}>
                    {result.assembled_context}
                  </pre>
                </div>

                {/* Top Sources */}
                <div>
                  <h4 style={{ fontSize: "13px", fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: "12px", textTransform: "uppercase" }}>Top Retrieved Intelligence</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {result.results?.slice(0, 3).map((r: any, i: number) => (
                      <div key={i} style={{ padding: "16px", background: "rgba(255,255,255,0.02)", borderRadius: "8px", border: "1px solid var(--sf-border)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                          <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--sf-accent)", textTransform: "uppercase" }}>{r.source}</span>
                          <span style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>Relevance: {(r.score * 100).toFixed(1)}%</span>
                        </div>
                        <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: "8px" }}>
                          {r.data?.name || r.data?.title || r.data?.control || "Document"}
                        </div>
                        <div style={{ fontSize: "13px", color: "var(--sf-text-secondary)", lineHeight: 1.5 }}>
                          {(r.data?.description || r.data?.content || r.data?.short_description || "").substring(0, 200)}...
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            ) : (
              <div style={{ textAlign: "center", paddingTop: "100px", color: "var(--sf-text-muted)" }}>
                <Search size={48} style={{ opacity: 0.15, margin: "0 auto 16px" }} />
                <div style={{ fontSize: "16px", fontWeight: 600, marginBottom: "8px" }}>Enter an Alert ID to begin</div>
                <div style={{ fontSize: "13px", maxWidth: "400px", margin: "0 auto", lineHeight: 1.5 }}>
                  The Agentic RAG system will automatically extract context from the alert, construct tailored search queries, and assemble intelligence from the most relevant knowledge bases.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
