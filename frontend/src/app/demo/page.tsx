"use client";

import { useEffect, useState } from "react";
import { getDemoScenarios, startDemoScenario, startAllScenarios, resetDemo, testPromptInjection, getAttackSamples } from "@/lib/api";
import type { DemoScenario } from "@/lib/types";

export default function DemoPage() {
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [running, setRunning] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, any>>({});
  const [runningAll, setRunningAll] = useState(false);

  // Security Test State
  const [attackSamples, setAttackSamples] = useState<any>(null);
  const [testPrompt, setTestPrompt] = useState("");
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => { 
    loadScenarios(); 
    loadAttackSamples();
  }, []);

  async function loadAttackSamples() {
    try { setAttackSamples(await getAttackSamples()); } catch {}
  }

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

  async function handleTestSecurity() {
    if (!testPrompt.trim()) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await testPromptInjection(testPrompt);
      setTestResult(result);
    } catch (e: any) {
      alert("Test failed: " + e.message);
    } finally {
      setIsTesting(false);
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

      {/* Security Testing Section */}
      <div style={{ marginTop: "40px" }}>
        <h2 className="sf-page-title" style={{ fontSize: "20px", marginBottom: "8px" }}>🛡️ Self-Defending AI: Live Security Test</h2>
        <p className="sf-page-subtitle" style={{ marginBottom: "20px" }}>
          Try to jailbreak the agents or inject malicious prompts. Our 11-category defense system runs <em>before</em> any LLM sees the input.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
          {/* Input Panel */}
          <div className="sf-card" style={{ padding: "24px" }}>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "14px", fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: "8px" }}>
                Select an Attack Sample (or write your own)
              </label>
              <select 
                className="sf-input"
                style={{ width: "100%", marginBottom: "12px", background: "var(--sf-bg-elevated)", color: "var(--sf-text-primary)" }}
                onChange={(e) => setTestPrompt(e.target.value)}
                defaultValue=""
              >
                <option value="" disabled>Choose an attack vector...</option>
                {attackSamples?.categories?.map((cat: any) => (
                  <optgroup key={cat.category} label={`${cat.name} (${cat.severity})`}>
                    {cat.samples.map((sample: string, i: number) => (
                      <option key={i} value={sample}>{sample}</option>
                    ))}
                  </optgroup>
                ))}
              </select>
              
              <textarea
                className="sf-input"
                style={{ width: "100%", height: "120px", resize: "none", fontFamily: "monospace", fontSize: "13px" }}
                placeholder="Enter prompt injection attempt..."
                value={testPrompt}
                onChange={(e) => setTestPrompt(e.target.value)}
              />
            </div>
            
            <button 
              className="sf-btn sf-btn-danger" 
              style={{ width: "100%", justifyContent: "center" }}
              onClick={handleTestSecurity}
              disabled={isTesting || !testPrompt.trim()}
            >
              {isTesting ? "⏳ Testing Defense Layer..." : "💥 Launch Attack"}
            </button>
          </div>

          {/* Results Panel */}
          <div className="sf-card" style={{ padding: "24px", display: "flex", flexDirection: "column" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: "16px", borderBottom: "1px solid var(--sf-border)", paddingBottom: "12px" }}>
              Defense System Analysis
            </h3>
            
            {testResult ? (
              <div className="sf-animate-in">
                {testResult.is_blocked ? (
                  <div style={{ padding: "16px", borderRadius: "8px", background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                      <span style={{ fontSize: "20px" }}>🛡️</span>
                      <strong style={{ color: "#fca5a5", fontSize: "16px" }}>ATTACK BLOCKED</strong>
                    </div>
                    
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px", fontSize: "13px" }}>
                      <div>
                        <div style={{ color: "var(--sf-text-muted)", marginBottom: "4px" }}>Layer Detected</div>
                        <div style={{ color: "var(--sf-text-primary)", fontWeight: 600 }}>{testResult.defense_layer}</div>
                      </div>
                      <div>
                        <div style={{ color: "var(--sf-text-muted)", marginBottom: "4px" }}>Attack Category</div>
                        <div style={{ color: "var(--sf-text-primary)", fontWeight: 600 }}>{testResult.category?.replace(/_/g, ' ').toUpperCase()}</div>
                      </div>
                      <div>
                        <div style={{ color: "var(--sf-text-muted)", marginBottom: "4px" }}>Severity</div>
                        <span className={`sf-badge critical`}>{testResult.severity?.toUpperCase()}</span>
                      </div>
                      <div>
                        <div style={{ color: "var(--sf-text-muted)", marginBottom: "4px" }}>Confidence</div>
                        <div style={{ color: "var(--sf-text-primary)", fontWeight: 600 }}>{(testResult.confidence * 100).toFixed(0)}%</div>
                      </div>
                    </div>

                    <div style={{ fontSize: "13px" }}>
                      <div style={{ color: "var(--sf-text-muted)", marginBottom: "4px" }}>Reasoning</div>
                      <div style={{ color: "var(--sf-text-secondary)", fontFamily: "monospace", padding: "8px", background: "rgba(0,0,0,0.2)", borderRadius: "4px" }}>
                        {testResult.details}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ padding: "16px", borderRadius: "8px", background: "rgba(16, 185, 129, 0.05)", border: "1px solid rgba(16, 185, 129, 0.2)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                      <span style={{ fontSize: "20px" }}>✅</span>
                      <strong style={{ color: "var(--sf-success)", fontSize: "16px" }}>INPUT PASSED</strong>
                    </div>
                    <div style={{ fontSize: "13px", color: "var(--sf-text-secondary)" }}>
                      No malicious intent detected by Layer 1. The prompt would be passed to the LLM.
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--sf-text-muted)", fontSize: "13px" }}>
                Select a payload and launch an attack to see how the defense system responds.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
