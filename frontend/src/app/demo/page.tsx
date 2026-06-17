"use client";

import { useEffect, useState } from "react";
import { getDemoScenarios, startDemoScenario, startAllScenarios, resetDemo } from "@/lib/api";
import type { DemoScenario } from "@/lib/types";

export default function DemoPage() {
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, any>>({});
  const [runningAll, setRunningAll] = useState(false);

  useEffect(() => { loadScenarios(); }, []);

  async function loadScenarios() {
    try { setScenarios(await getDemoScenarios()); } catch {}
  }

  async function handleRun(id: string) {
    setRunning(id);
    try {
      const result = await startDemoScenario(id);
      setResults(prev => ({ ...prev, [id]: result }));
    } catch (e: any) {
      setResults(prev => ({ ...prev, [id]: { error: e.message } }));
    } finally {
      setRunning(null);
    }
  }

  async function handleRunAll() {
    setRunningAll(true);
    try {
      const result = await startAllScenarios();
      // Mark all as completed
      for (const r of result.results || []) {
        setResults(prev => ({ ...prev, [r.scenario?.toLowerCase().replace(/\s+/g, '_')]: r }));
      }
    } catch (e: any) {
      alert("Error: " + e.message);
    } finally {
      setRunningAll(false);
    }
  }

  async function handleReset() {
    if (!confirm("This will delete all demo data. Continue?")) return;
    try {
      await resetDemo();
      setResults({});
      alert("Demo data reset successfully!");
    } catch (e: any) {
      alert("Error: " + e.message);
    }
  }

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">🎮 Demo Center</h1>
          <p className="sf-page-subtitle">Launch simulated security attacks and IT issues to test the platform</p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button className="sf-btn sf-btn-primary" onClick={handleRunAll} disabled={runningAll}>
            {runningAll ? "⏳ Running..." : "🚀 Run All Scenarios"}
          </button>
          <button className="sf-btn sf-btn-danger" onClick={handleReset}>🗑️ Reset Data</button>
        </div>
      </div>

      {/* Info Banner */}
      <div style={{
        padding: "16px 20px", borderRadius: "12px", marginBottom: "24px",
        background: "rgba(99, 102, 241, 0.08)", border: "1px solid rgba(99, 102, 241, 0.2)",
        display: "flex", gap: "12px", alignItems: "center",
      }}>
        <span style={{ fontSize: "24px" }}>💡</span>
        <div style={{ fontSize: "13px", lineHeight: 1.6, color: "var(--sf-text-secondary)" }}>
          <strong style={{ color: "var(--sf-text-primary)" }}>How it works:</strong> Each scenario generates realistic log events, runs them through the detection engine, and triggers the full AI analysis pipeline (Triage → Investigation → Remediation → Report → Ticket). Navigate to the Dashboard, Alerts, or Tickets pages to see the results.
        </div>
      </div>

      {/* Scenario Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", gap: "16px" }}>
        {scenarios.map(s => (
          <div key={s.id} className={`sf-scenario-card ${s.type}`}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
              <div>
                <div style={{ fontSize: "16px", fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: "4px" }}>
                  {s.type === "security" ? "🔴" : "🔵"} {s.name}
                </div>
                <span className={`sf-badge ${s.type === "security" ? "critical" : "info"}`}>
                  {s.type === "security" ? "Security Attack" : "IT Support"}
                </span>
              </div>
            </div>

            <p style={{ fontSize: "13px", color: "var(--sf-text-secondary)", lineHeight: 1.6, marginBottom: "16px" }}>
              {s.description}
            </p>

            {results[s.id] && !results[s.id].error && (
              <div className="sf-animate-in" style={{
                padding: "12px", borderRadius: "8px", marginBottom: "12px",
                background: "rgba(16, 185, 129, 0.05)", border: "1px solid rgba(16, 185, 129, 0.2)",
              }}>
                <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--sf-success)", marginBottom: "4px" }}>✅ Completed</div>
                <div style={{ fontSize: "12px", color: "var(--sf-text-secondary)" }}>
                  {results[s.id].events_generated > 0 && `${results[s.id].events_generated} events generated • `}
                  {results[s.id].alerts_created > 0 && `${results[s.id].alerts_created} alerts created • `}
                  {results[s.id].description?.slice(0, 120)}
                </div>
              </div>
            )}

            {results[s.id]?.error && (
              <div style={{
                padding: "12px", borderRadius: "8px", marginBottom: "12px",
                background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)",
                fontSize: "12px", color: "#fca5a5",
              }}>
                ❌ Error: {results[s.id].error}
              </div>
            )}

            <button
              className={`sf-btn ${results[s.id] && !results[s.id].error ? "sf-btn-success" : "sf-btn-primary"} sf-btn-sm`}
              style={{ width: "100%", justifyContent: "center" }}
              onClick={() => handleRun(s.id)}
              disabled={running === s.id}
            >
              {running === s.id ? "⏳ Running..." : results[s.id] && !results[s.id].error ? "↻ Run Again" : "▶ Launch Scenario"}
            </button>
          </div>
        ))}

        {scenarios.length === 0 && (
          <div style={{ gridColumn: "1 / -1", textAlign: "center", padding: "60px", color: "var(--sf-text-muted)" }}>
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>🎮</div>
            <div style={{ fontSize: "16px", fontWeight: 600 }}>Loading scenarios...</div>
            <div style={{ fontSize: "13px", marginTop: "8px" }}>Make sure the backend is running on port 8000</div>
          </div>
        )}
      </div>
    </div>
  );
}
