"use client";

import { useEffect, useState, useRef } from "react";
import { getDemoScenarios, startDemoScenario, startAllScenarios, resetDemo, testPromptInjection, getAttackSamples } from "@/lib/api";
import type { DemoScenario } from "@/lib/types";

const KILL_CHAIN = [
  { stage: 1, name: "Credential Stuffing",   technique: "T1110", tactic: "Credential Access",   icon: "🔐", color: "#f97316" },
  { stage: 2, name: "Initial Access",         technique: "T1078", tactic: "Initial Access",        icon: "🚪", color: "#ef4444" },
  { stage: 3, name: "Privilege Escalation",   technique: "T1068", tactic: "Privilege Escalation",  icon: "⬆️", color: "#dc2626" },
  { stage: 4, name: "Lateral Movement",       technique: "T1021", tactic: "Lateral Movement",      icon: "↔️", color: "#b91c1c" },
  { stage: 5, name: "Malware Execution",      technique: "T1204", tactic: "Execution",             icon: "🦠", color: "#7c3aed" },
  { stage: 6, name: "C2 Communication",       technique: "T1071", tactic: "Command & Control",     icon: "📡", color: "#6d28d9" },
  { stage: 7, name: "Data Staging",           technique: "T1074", tactic: "Collection",            icon: "📦", color: "#a21caf" },
  { stage: 8, name: "Data Exfiltration",      technique: "T1048", tactic: "Exfiltration",          icon: "📤", color: "#be185d" },
  { stage: 9, name: "Ransomware Encryption",  technique: "T1486", tactic: "Impact",               icon: "🔒", color: "#9f1239" },
];

export default function DemoPage() {
  const [scenarios, setScenarios]         = useState<DemoScenario[]>([]);
  const [running, setRunning]             = useState<string | null>(null);
  const [results, setResults]             = useState<Record<string, any>>({});
  const [runningAll, setRunningAll]       = useState(false);
  const [attackPhase, setAttackPhase]     = useState(-1);   // -1 = idle, 0-8 = stage index, 9 = done
  const [attackResult, setAttackResult]   = useState<any>(null);
  const [elapsed, setElapsed]             = useState(0);
  const [attackSamples, setAttackSamples] = useState<any>(null);
  const [testPrompt, setTestPrompt]       = useState("");
  const [isTesting, setIsTesting]         = useState(false);
  const [testResult, setTestResult]       = useState<any>(null);

  const timerRef = useRef<any>(null);
  const startRef = useRef<number>(0);

  useEffect(() => {
    loadScenarios();
    try { getAttackSamples().then(setAttackSamples); } catch {}
  }, []);

  async function loadScenarios() {
    try {
      const all = await getDemoScenarios();
      setScenarios(all.filter((s: any) => s.type !== "flagship"));
    } catch {}
  }

  // ── Launch Operation NightOwl ────────────────────────────────────────────
  async function launchNightOwl() {
    if (running) return;
    setRunning("operation_nightowl");
    setAttackPhase(0);
    setAttackResult(null);
    setElapsed(0);
    startRef.current = Date.now();

    // Animate through stages while backend processes
    for (let i = 0; i < 9; i++) {
      await new Promise(r => setTimeout(r, 600));
      setAttackPhase(i + 1);
      setElapsed(Math.round((Date.now() - startRef.current) / 1000));
    }

    // Actually call the backend
    try {
      const result = await startDemoScenario("operation_nightowl");
      setAttackResult(result);
      setAttackPhase(9);
    } catch (e: any) {
      setAttackResult({ error: e.message });
    } finally {
      setRunning(null);
      setElapsed(Math.round((Date.now() - startRef.current) / 1000));
    }
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

  async function handleReset() {
    if (!confirm("This will delete all demo data. Continue?")) return;
    try {
      await resetDemo();
      setResults({});
      setAttackPhase(-1);
      setAttackResult(null);
      setElapsed(0);
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

  const isAttacking = running === "operation_nightowl";
  const isDone      = attackPhase === 9;

  return (
    <div className="sf-animate-in">
      {/* ── Page Header ─────────────────────────────────────────────────────── */}
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title" style={{ background: "linear-gradient(135deg, #ef4444, #dc2626, #7c3aed)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            🎮 Demo Command Center
          </h1>
          <p className="sf-page-subtitle">
            Launch simulated cyberattacks · Watch AI agents respond in real-time · Show judges what SecureFlow AI can do
          </p>
        </div>
        <button className="sf-btn sf-btn-danger sf-btn-sm" onClick={handleReset}>
          🗑️ Reset All Data
        </button>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          FLAGSHIP: OPERATION NIGHTOWL
      ══════════════════════════════════════════════════════════════════════ */}
      <div style={{
        borderRadius: 16, marginBottom: 32, overflow: "hidden",
        border: "1px solid rgba(220,38,38,0.3)",
        background: "linear-gradient(135deg, rgba(127,29,29,0.15) 0%, rgba(120,53,15,0.1) 50%, rgba(76,29,149,0.1) 100%)",
        boxShadow: "0 0 60px rgba(220,38,38,0.08)",
      }}>
        {/* Header */}
        <div style={{
          padding: "20px 28px",
          borderBottom: "1px solid rgba(220,38,38,0.2)",
          background: "linear-gradient(135deg, rgba(127,29,29,0.2), rgba(76,29,149,0.1))",
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4 }}>
              <span style={{ fontSize: 28 }}>🌙</span>
              <div>
                <div style={{ fontSize: 22, fontWeight: 900, color: "#fca5a5", letterSpacing: "-0.02em" }}>
                  Operation NightOwl
                </div>
                <div style={{ fontSize: 12, color: "rgba(252,165,165,0.7)", marginTop: 2 }}>
                  APT29 / CozyBear · Full 9-Stage Ransomware Kill Chain · FLAGSHIP DEMO
                </div>
              </div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
            {isDone && attackResult && !attackResult.error && (
              <>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 28, fontWeight: 900, color: "#10b981" }}>{attackResult.events_generated}</div>
                  <div style={{ fontSize: 10, color: "var(--sf-text-muted)", textTransform: "uppercase" }}>Events</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 28, fontWeight: 900, color: "#ef4444" }}>{attackResult.alerts_created}</div>
                  <div style={{ fontSize: 10, color: "var(--sf-text-muted)", textTransform: "uppercase" }}>Alerts</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 28, fontWeight: 900, color: "#818cf8" }}>{elapsed}s</div>
                  <div style={{ fontSize: 10, color: "var(--sf-text-muted)", textTransform: "uppercase" }}>Runtime</div>
                </div>
              </>
            )}
          </div>
        </div>

        <div style={{ padding: "24px 28px" }}>
          {/* IOC Strip */}
          <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
            {[
              { label: "Threat Actor", value: "APT29 / CozyBear", color: "#f97316" },
              { label: "Attacker IP",  value: "185.220.101.34",   color: "#ef4444" },
              { label: "C2 Server",    value: "91.121.87.18",     color: "#7c3aed" },
              { label: "Victim",       value: "john.miller",      color: "#06b6d4" },
              { label: "Malware",      value: "Akira Ransomware", color: "#a21caf" },
              { label: "CVE",          value: "CVE-2024-3094",    color: "#dc2626" },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ padding: "6px 14px", borderRadius: 8, border: `1px solid ${color}30`, background: `${color}10`, fontSize: 11 }}>
                <span style={{ color: "var(--sf-text-muted)", marginRight: 6 }}>{label}:</span>
                <span style={{ color, fontWeight: 700, fontFamily: "monospace" }}>{value}</span>
              </div>
            ))}
          </div>

          {/* Kill Chain Timeline */}
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--sf-text-muted)", marginBottom: 12 }}>
              MITRE ATT&CK Kill Chain
            </div>
            <div style={{ display: "flex", gap: 0, overflowX: "auto" }}>
              {KILL_CHAIN.map((stage, idx) => {
                const active  = attackPhase > idx;
                const current = attackPhase === idx && isAttacking;
                return (
                  <div key={stage.stage} style={{ flex: 1, minWidth: 80 }}>
                    <div style={{
                      position: "relative", padding: "12px 8px", borderRadius: idx === 0 ? "8px 0 0 8px" : idx === 8 ? "0 8px 8px 0" : 0,
                      background: active ? `${stage.color}25` : current ? `${stage.color}15` : "rgba(255,255,255,0.02)",
                      border: `1px solid ${active ? stage.color + "50" : current ? stage.color + "40" : "rgba(255,255,255,0.06)"}`,
                      borderLeft: idx === 0 ? undefined : "none",
                      transition: "all 0.4s ease",
                      textAlign: "center",
                    }}>
                      {current && (
                        <div style={{ position: "absolute", top: -3, left: "50%", transform: "translateX(-50%)", width: 6, height: 6, borderRadius: "50%", background: stage.color, boxShadow: `0 0 12px ${stage.color}` }} />
                      )}
                      <div style={{ fontSize: 16, marginBottom: 4 }}>{active ? "✅" : current ? "⚡" : stage.icon}</div>
                      <div style={{ fontSize: 9, fontWeight: 700, color: active ? stage.color : current ? stage.color : "var(--sf-text-muted)", marginBottom: 2, lineHeight: 1.2 }}>
                        {stage.name}
                      </div>
                      <div style={{ fontSize: 8, fontFamily: "monospace", color: active ? stage.color + "cc" : "var(--sf-text-muted)", opacity: 0.8 }}>
                        {stage.technique}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Launch Button */}
          <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
            <button
              onClick={launchNightOwl}
              disabled={isAttacking}
              style={{
                padding: "18px 48px", borderRadius: 12, cursor: isAttacking ? "not-allowed" : "pointer",
                fontSize: 18, fontWeight: 900, letterSpacing: "-0.01em",
                border: "2px solid rgba(220,38,38,0.5)",
                background: isAttacking
                  ? "rgba(127,29,29,0.3)"
                  : "linear-gradient(135deg, #dc2626, #b91c1c, #7c3aed)",
                color: "#ffffff",
                boxShadow: isAttacking ? "none" : "0 0 40px rgba(220,38,38,0.3), 0 8px 32px rgba(0,0,0,0.4)",
                transform: isAttacking ? "scale(0.98)" : "scale(1)",
                transition: "all 0.3s ease",
                display: "flex", alignItems: "center", gap: 12,
                animation: !isAttacking && !isDone ? "pulse 2s infinite" : "none",
              }}
            >
              {isAttacking ? (
                <><div className="sf-loading-spinner" style={{ width: 20, height: 20, borderWidth: 3 }} /> Executing Kill Chain... Stage {attackPhase}/9</>
              ) : isDone ? (
                <><span>✅</span> Attack Complete — Run Again</>
              ) : (
                <><span>🚨</span> Launch Ransomware Attack</>
              )}
            </button>

            {isAttacking && (
              <div style={{ fontSize: 13, color: "var(--sf-text-muted)" }}>
                <span style={{ color: "#f97316", fontWeight: 700 }}>LIVE:</span> {KILL_CHAIN[Math.min(attackPhase, 8)]?.name} in progress...
              </div>
            )}
          </div>

          {/* Success Result */}
          {isDone && attackResult && !attackResult.error && (
            <div className="sf-animate-in" style={{
              marginTop: 20, padding: 20, borderRadius: 12,
              background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.2)",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: "#10b981", marginBottom: 4 }}>
                    ✅ Operation NightOwl Executed — AI Agents Responding
                  </div>
                  <div style={{ fontSize: 12, color: "var(--sf-text-secondary)", maxWidth: 500, lineHeight: 1.6 }}>
                    {attackResult.description}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {[
                    { label: "→ War Room",   href: "/" },
                    { label: "→ Alerts",     href: "/alerts" },
                    { label: "→ Knowledge Graph", href: "/graph" },
                    { label: "→ Autonomous", href: "/autonomous" },
                    { label: "→ Risk",       href: "/risk" },
                  ].map(({ label, href }) => (
                    <a key={href} href={href} style={{
                      padding: "6px 14px", borderRadius: 8, fontSize: 12, fontWeight: 600,
                      border: "1px solid rgba(16,185,129,0.3)", background: "rgba(16,185,129,0.1)",
                      color: "#10b981", textDecoration: "none", transition: "all 0.2s ease",
                    }}>
                      {label}
                    </a>
                  ))}
                </div>
              </div>

              {/* Assets compromised */}
              {attackResult.assets_compromised && (
                <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "var(--sf-text-muted)" }}>Compromised assets:</span>
                  {attackResult.assets_compromised.map((a: string) => (
                    <span key={a} style={{ padding: "2px 10px", borderRadius: 6, background: "rgba(220,38,38,0.1)", color: "#fca5a5", fontSize: 11, fontFamily: "monospace", border: "1px solid rgba(220,38,38,0.2)" }}>
                      {a}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {attackResult?.error && (
            <div className="sf-animate-in" style={{ marginTop: 16, padding: 14, borderRadius: 10, background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.2)", fontSize: 12, color: "#fca5a5" }}>
              ❌ Backend error: {attackResult.error} — ensure backend is running on port 8000
            </div>
          )}
        </div>
      </div>

      {/* ── Before / After Contrast ─────────────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 32 }}>
        {/* Before */}
        <div style={{ borderRadius: 12, padding: 20, background: "rgba(239,68,68,0.05)", border: "1px solid rgba(239,68,68,0.2)" }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#fca5a5", marginBottom: 14 }}>❌ Traditional SOC</div>
          {[
            ["Detection Time",    "197 days"],
            ["Investigation",     "4+ hours manual"],
            ["Breach Cost",       "$4.5M average"],
            ["Memory",            "Lost at shift change"],
            ["Compliance",        "Manual quarterly"],
            ["Response",          "Human-only, slow"],
          ].map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid rgba(239,68,68,0.1)", fontSize: 12 }}>
              <span style={{ color: "var(--sf-text-muted)" }}>{k}</span>
              <span style={{ color: "#fca5a5", fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>
        {/* After */}
        <div style={{ borderRadius: 12, padding: 20, background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.2)" }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#10b981", marginBottom: 14 }}>✅ SecureFlow AI</div>
          {[
            ["Detection Time",    "4 seconds"],
            ["Investigation",     "Autonomous AI"],
            ["Breach Cost",       "Prevented"],
            ["Memory",            "Permanent graph memory"],
            ["Compliance",        "Real-time continuous"],
            ["Response",          "Autonomous + human approval"],
          ].map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid rgba(16,185,129,0.1)", fontSize: 12 }}>
              <span style={{ color: "var(--sf-text-muted)" }}>{k}</span>
              <span style={{ color: "#10b981", fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Secondary Scenarios ─────────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 12 }}>
          Additional Attack Scenarios
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12 }}>
          {scenarios.map(s => (
            <div key={s.id} className={`sf-scenario-card ${s.type}`} style={{ padding: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 4 }}>
                {s.type === "security" ? "🔴" : "🔵"} {s.name}
              </div>
              <p style={{ fontSize: 12, color: "var(--sf-text-secondary)", lineHeight: 1.5, marginBottom: 12 }}>
                {s.description}
              </p>
              {results[s.id] && !results[s.id].error && (
                <div style={{ fontSize: 11, color: "#10b981", marginBottom: 8 }}>
                  ✅ {results[s.id].events_generated} events · {results[s.id].alerts_created} alerts
                </div>
              )}
              {results[s.id]?.error && (
                <div style={{ fontSize: 11, color: "#fca5a5", marginBottom: 8 }}>❌ {results[s.id].error}</div>
              )}
              <button
                className={`sf-btn ${results[s.id] && !results[s.id].error ? "sf-btn-success" : "sf-btn-secondary"} sf-btn-sm`}
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() => handleRun(s.id)}
                disabled={running === s.id}
              >
                {running === s.id ? "⏳ Running..." : results[s.id] && !results[s.id].error ? "↻ Run Again" : "▶ Launch"}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Prompt Injection Security Test ──────────────────────────────────── */}
      <div>
        <div style={{ fontSize: 14, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 4 }}>🛡️ Self-Defending AI: Prompt Injection Test</div>
        <p style={{ fontSize: 12, color: "var(--sf-text-muted)", marginBottom: 16 }}>
          Try to jailbreak the agents. Our 11-category defense system runs before any LLM sees the input.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div className="sf-card" style={{ padding: 20 }}>
            <select className="sf-input" style={{ width: "100%", marginBottom: 10, background: "var(--sf-bg-elevated)", color: "var(--sf-text-primary)" }}
              onChange={e => setTestPrompt(e.target.value)} defaultValue="">
              <option value="" disabled>Choose an attack vector...</option>
              {attackSamples?.categories?.map((cat: any) => (
                <optgroup key={cat.category} label={`${cat.name} (${cat.severity})`}>
                  {cat.samples.map((s: string, i: number) => <option key={i} value={s}>{s}</option>)}
                </optgroup>
              ))}
            </select>
            <textarea className="sf-input" style={{ width: "100%", height: 100, resize: "none", fontFamily: "monospace", fontSize: 12, marginBottom: 10 }}
              placeholder="Enter prompt injection attempt..." value={testPrompt} onChange={e => setTestPrompt(e.target.value)} />
            <button className="sf-btn sf-btn-danger" style={{ width: "100%", justifyContent: "center" }}
              onClick={handleTestSecurity} disabled={isTesting || !testPrompt.trim()}>
              {isTesting ? "⏳ Testing..." : "💥 Attack Defense Layer"}
            </button>
          </div>
          <div className="sf-card" style={{ padding: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: 12, paddingBottom: 10, borderBottom: "1px solid var(--sf-border)" }}>Defense Analysis</div>
            {testResult ? (
              <div className="sf-animate-in">
                <div style={{ padding: 14, borderRadius: 8, background: testResult.is_blocked ? "rgba(239,68,68,0.05)" : "rgba(16,185,129,0.05)", border: `1px solid ${testResult.is_blocked ? "rgba(239,68,68,0.2)" : "rgba(16,185,129,0.2)"}`, marginBottom: 12 }}>
                  <div style={{ fontWeight: 700, fontSize: 15, color: testResult.is_blocked ? "#fca5a5" : "#10b981" }}>
                    {testResult.is_blocked ? "🛡️ ATTACK BLOCKED" : "✅ INPUT PASSED"}
                  </div>
                </div>
                {testResult.is_blocked && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 12 }}>
                    {[["Layer", testResult.defense_layer], ["Category", testResult.category?.replace(/_/g, " ").toUpperCase()], ["Severity", testResult.severity?.toUpperCase()], ["Confidence", `${(testResult.confidence * 100).toFixed(0)}%`]].map(([k, v]) => (
                      <div key={k}><div style={{ color: "var(--sf-text-muted)", marginBottom: 2 }}>{k}</div><div style={{ color: "var(--sf-text-primary)", fontWeight: 600 }}>{v}</div></div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: "var(--sf-text-muted)", fontSize: 12, marginTop: 20 }}>Launch an attack vector to see the defense response.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
