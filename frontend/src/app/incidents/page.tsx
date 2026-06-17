"use client";

import { useEffect, useState } from "react";
import { getIncidents } from "@/lib/api";
import type { Incident } from "@/lib/types";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<Incident | null>(null);
  const [view, setView] = useState<"executive" | "technical">("executive");

  useEffect(() => { loadIncidents(); }, []);

  async function loadIncidents() {
    try { setIncidents(await getIncidents({ limit: 50 })); } catch {}
  }

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">🔍 Incident Response</h1>
          <p className="sf-page-subtitle">{incidents.length} incidents • AI-powered investigation & reporting</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: selected ? "400px 1fr" : "1fr", gap: "20px" }}>
        {/* Incident List */}
        <div className="sf-card" style={{ overflow: "auto", maxHeight: "calc(100vh - 160px)" }}>
          {incidents.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px", color: "var(--sf-text-muted)" }}>
              <div style={{ fontSize: "48px", marginBottom: "16px" }}>🔍</div>
              <div style={{ fontSize: "16px", fontWeight: 600 }}>No incidents yet</div>
              <div style={{ fontSize: "13px", marginTop: "8px" }}>Incidents are created when alerts are analyzed by AI agents</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {incidents.map(inc => (
                <div key={inc.id} onClick={() => setSelected(inc)}
                  style={{
                    padding: "16px", borderRadius: "10px", cursor: "pointer",
                    background: selected?.id === inc.id ? "rgba(99,102,241,0.08)" : "rgba(255,255,255,0.02)",
                    border: `1px solid ${selected?.id === inc.id ? "rgba(99,102,241,0.3)" : "var(--sf-border)"}`,
                    transition: "all 0.2s ease",
                  }}>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: "8px" }}>
                    #{inc.id} {inc.title}
                  </div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    <span className={`sf-badge ${inc.severity}`}>{inc.severity}</span>
                    <span className={`sf-badge ${inc.status}`}>{inc.status}</span>
                    <span className={`sf-badge ${inc.priority.toLowerCase()}`}>{inc.priority}</span>
                  </div>
                  {inc.root_cause && (
                    <div style={{ fontSize: "12px", color: "var(--sf-text-muted)", marginTop: "8px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {inc.root_cause.slice(0, 100)}...
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Incident Detail */}
        {selected && (
          <div className="sf-card sf-animate-in" style={{ overflow: "auto", maxHeight: "calc(100vh - 160px)" }}>
            <div style={{ marginBottom: "20px" }}>
              <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "8px" }}>{selected.title}</h2>
              <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
                <span className={`sf-badge ${selected.severity}`}>{selected.severity}</span>
                <span className={`sf-badge ${selected.status}`}>{selected.status}</span>
                <span className={`sf-badge ${selected.priority.toLowerCase()}`}>{selected.priority}</span>
              </div>

              {/* Report Toggle */}
              <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
                <button onClick={() => setView("executive")}
                  className={`sf-btn sf-btn-sm ${view === "executive" ? "sf-btn-primary" : "sf-btn-secondary"}`}>
                  📊 Executive Report
                </button>
                <button onClick={() => setView("technical")}
                  className={`sf-btn sf-btn-sm ${view === "technical" ? "sf-btn-primary" : "sf-btn-secondary"}`}>
                  🔧 Technical Report
                </button>
              </div>
            </div>

            {/* Report Content */}
            <div className="sf-markdown" style={{
              padding: "20px", borderRadius: "12px",
              background: "rgba(0,0,0,0.2)", border: "1px solid var(--sf-border)",
              fontSize: "13px", lineHeight: 1.8, whiteSpace: "pre-wrap",
              color: "var(--sf-text-secondary)",
            }}>
              {view === "executive" ? (selected.executive_summary || "Executive report not yet generated.") :
                (selected.technical_summary || "Technical report not yet generated.")}
            </div>

            {/* Investigation Results */}
            {selected.investigation_results && (
              <div style={{ marginTop: "16px" }}>
                <h3 style={{ fontSize: "14px", fontWeight: 700, marginBottom: "8px" }}>Investigation Details</h3>

                {selected.investigation_results.what_happened && (
                  <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--sf-border)", marginBottom: "8px" }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--sf-accent-light)", marginBottom: "4px" }}>What Happened</div>
                    <div style={{ fontSize: "13px", color: "var(--sf-text-secondary)" }}>{selected.investigation_results.what_happened}</div>
                  </div>
                )}

                {selected.investigation_results.risk_assessment && (
                  <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(239,68,68,0.05)", border: "1px solid rgba(239,68,68,0.15)", marginBottom: "8px" }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: "#fca5a5", marginBottom: "4px" }}>Risk Assessment</div>
                    <div style={{ fontSize: "13px", color: "var(--sf-text-secondary)" }}>{selected.investigation_results.risk_assessment}</div>
                  </div>
                )}

                {selected.attack_path && (
                  <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--sf-border)" }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--sf-warning)", marginBottom: "4px" }}>Attack Path</div>
                    <pre style={{ fontSize: "12px", color: "var(--sf-text-secondary)", whiteSpace: "pre-wrap", margin: 0 }}>{selected.attack_path}</pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
