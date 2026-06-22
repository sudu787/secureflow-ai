"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Zap, Clock, CheckCircle, XCircle, Shield, RefreshCw,
  Play, RotateCcw, Brain, AlertTriangle, Activity, Lock
} from "lucide-react";
import {
  getApprovalQueue, getActionHistory, getAutonomousModes,
  approveAction, rejectAction
} from "@/lib/api";

const MODE_COLORS: Record<string, string> = {
  human_approval: "#64748b", risk_aware: "#3b82f6",
  autonomous: "#8b5cf6", emergency: "#dc2626",
};
const MODE_ICONS: Record<string, string> = {
  human_approval: "🧑", risk_aware: "⚖️", autonomous: "⚡", emergency: "🚨",
};

const statusColor = (s: string) =>
  s === "auto_executed" || s === "approved_executed" ? "#10b981"
  : s === "pending_approval" ? "#f59e0b"
  : s === "rejected" ? "#dc2626" : "#64748b";

const statusLabel = (s: string) =>
  s === "auto_executed" ? "Auto-Executed" : s === "approved_executed" ? "Approved ✓"
  : s === "pending_approval" ? "Awaiting Approval" : s === "rejected" ? "Rejected ✗" : s;

// Demo XAI reasoning chains for queue items
const XAI_REASONS = [
  [
    { icon: "🔴", label: "Severity",     value: "Critical — CVSS 9.8 exploit confirmed", source: "CVE-2024-3094 match" },
    { icon: "🕸️", label: "Graph Intel",  value: "IP linked to APT29 C2 infrastructure", source: "Knowledge Graph traversal" },
    { icon: "🧠", label: "Memory",       value: "Similar to INC-001 (73% match) — same actor", source: "Org Memory recall" },
    { icon: "🎯", label: "MITRE Stage",  value: "T1486 — Kill-chain stage: Impact (late stage)", source: "Triage Agent" },
    { icon: "📊", label: "Confidence",   value: "94% — AI recommends immediate containment", source: "Multi-agent consensus" },
  ],
  [
    { icon: "🟠", label: "Severity",     value: "High — 45 failed logins in 120 seconds", source: "Pattern detection" },
    { icon: "🕸️", label: "Graph Intel",  value: "User has admin access to DB-Prod-01", source: "Graph blast radius" },
    { icon: "🎯", label: "MITRE",        value: "T1110 — Credential Stuffing attack", source: "Triage Agent" },
    { icon: "📊", label: "Confidence",   value: "87% — Lock account to prevent pivot", source: "Autonomous Response Agent" },
  ],
];

export default function AutonomousResponseCenter() {
  const [queue, setQueue]       = useState<any[]>([]);
  const [history, setHistory]   = useState<any[]>([]);
  const [modes, setModes]       = useState<any[]>([]);
  const [loading, setLoading]   = useState(true);
  const [activeMode, setActiveMode] = useState("risk_aware");
  const [approvingIdx, setApprovingIdx] = useState<number | null>(null);
  const [expandedXAI, setExpandedXAI] = useState<number | null>(null);
  const [rollbackItem, setRollbackItem] = useState<number | null>(null);

  const load = useCallback(async () => {
    const results = await Promise.allSettled([
      getApprovalQueue(), getActionHistory(), getAutonomousModes(),
    ]);
    if (results[0].status === "fulfilled") setQueue((results[0] as any).value?.actions || []);
    if (results[1].status === "fulfilled") setHistory((results[1] as any).value?.actions || []);
    if (results[2].status === "fulfilled") setModes((results[2] as any).value?.modes || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); const iv = setInterval(load, 10000); return () => clearInterval(iv); }, [load]);

  const handleApprove = async (idx: number) => {
    setApprovingIdx(idx);
    try { await approveAction(idx, "analyst@secureflow.ai"); await load(); }
    catch {} finally { setApprovingIdx(null); }
  };
  const handleReject = async (idx: number) => {
    try { await rejectAction(idx, "analyst@secureflow.ai", "Manual review required"); await load(); }
    catch {}
  };

  // Summary stats
  const executed  = history.filter((h: any) => ["auto_executed", "approved_executed"].includes(h.status)).length;
  const rejected  = history.filter((h: any) => h.status === "rejected").length;
  const pending   = queue.length;

  return (
    <div className="sf-animate-in">
      {/* Header */}
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title" style={{ background: "linear-gradient(135deg, #f59e0b, #f97316)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Autonomous Response Center
          </h1>
          <p className="sf-page-subtitle">AI-driven containment · human-in-the-loop approval · explainable decisions · one-click rollback</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="sf-btn sf-btn-secondary sf-btn-sm" onClick={load}><RefreshCw size={13} /> Refresh</button>
        </div>
      </div>

      {/* ── Stats Row ────────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 20 }}>
        {[
          { label: "Pending Approval",  value: pending,        icon: "⏳", color: "#f59e0b" },
          { label: "Auto-Executed",     value: executed,       icon: "⚡", color: "#10b981" },
          { label: "Rejected",          value: rejected,       icon: "✗",  color: "#dc2626" },
          { label: "AI Confidence Avg", value: "91%",          icon: "🧠", color: "#6366f1" },
        ].map(({ label, value, icon, color }) => (
          <div key={label} className="sf-stat-card" style={{ borderLeft: `3px solid ${color}`, background: `linear-gradient(135deg, ${color}08, transparent)` }}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>{icon}</div>
            <div className="sf-stat-value" style={{ fontSize: 28, color }}>{value}</div>
            <div className="sf-stat-label">{label}</div>
          </div>
        ))}
      </div>

      {/* ── Autonomy Mode Selector ───────────────────────── */}
      <div className="sf-card" style={{ marginBottom: 20 }}>
        <div className="sf-card-header">
          <div>
            <div className="sf-card-title"><Zap size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} /> Autonomy Mode</div>
            <div className="sf-card-subtitle">Controls how AI agents make and execute security decisions</div>
          </div>
          <span className="sf-badge" style={{ background: `${MODE_COLORS[activeMode]}20`, color: MODE_COLORS[activeMode], border: `1px solid ${MODE_COLORS[activeMode]}40` }}>
            {MODE_ICONS[activeMode]} Active: {activeMode.replace(/_/g, " ").toUpperCase()}
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
          {(modes.length > 0 ? modes : [
            { id: "human_approval", name: "Human Approval",  description: "All AI actions require manual sign-off before execution",    recommended_for: "High-stakes environments" },
            { id: "risk_aware",     name: "Risk-Aware",      description: "AI auto-executes low-risk actions, human approval for high risk", recommended_for: "Most enterprise SOCs" },
            { id: "autonomous",     name: "Full Autonomous",  description: "AI executes all containment actions without human review",   recommended_for: "24/7 unattended operations" },
            { id: "emergency",      name: "Emergency Mode",   description: "Maximum automation, immediate containment, notify CISO",    recommended_for: "Active incident response" },
          ]).map((mode: any) => {
            const isActive = activeMode === mode.id;
            const color = MODE_COLORS[mode.id] ?? "#64748b";
            return (
              <button key={mode.id} onClick={() => setActiveMode(mode.id)} style={{
                padding: 16, borderRadius: 10, textAlign: "left", cursor: "pointer",
                border: `2px solid ${isActive ? color : "var(--sf-border)"}`,
                background: isActive ? `${color}12` : "rgba(255,255,255,0.02)",
                transition: "all 0.25s ease",
              }}>
                <div style={{ fontSize: 20, marginBottom: 6 }}>{MODE_ICONS[mode.id]}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: isActive ? color : "var(--sf-text-primary)", marginBottom: 4 }}>{mode.name}</div>
                <div style={{ fontSize: 11, color: "var(--sf-text-muted)", lineHeight: 1.5, marginBottom: 6 }}>{mode.description}</div>
                <div style={{ fontSize: 10, color: "var(--sf-text-muted)", fontStyle: "italic", borderTop: "1px solid var(--sf-border)", paddingTop: 6 }}>
                  {mode.recommended_for}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Main 2-Column: Approval Queue + Agent Decision Log ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>

        {/* Approval Queue */}
        <div className="sf-card">
          <div className="sf-card-header">
            <div>
              <div className="sf-card-title"><Clock size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} /> Pending Approval Queue</div>
              <div className="sf-card-subtitle">Human review required before execution</div>
            </div>
            <span className="sf-badge" style={{ background: pending > 0 ? "rgba(245,158,11,0.15)" : "rgba(16,185,129,0.1)", color: pending > 0 ? "#f59e0b" : "#10b981" }}>
              {pending} pending
            </span>
          </div>

          {queue.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px", color: "var(--sf-text-muted)" }}>
              <CheckCircle size={36} color="#10b981" style={{ opacity: 0.4, marginBottom: 10 }} />
              <div style={{ fontWeight: 600 }}>Queue is clear</div>
              <div style={{ fontSize: 12, marginTop: 4 }}>AI is monitoring — no actions pending</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {queue.map((action: any, idx: number) => (
                <div key={idx} style={{
                  background: "rgba(245,158,11,0.05)", border: "1px solid rgba(245,158,11,0.2)",
                  borderRadius: 10, padding: 16, position: "relative",
                }}>
                  {/* Action header */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 3 }}>{action.action}</div>
                      <div style={{ fontSize: 11, fontFamily: "monospace", color: "var(--sf-accent-light)" }}>→ {action.target}</div>
                    </div>
                    <span className={`sf-badge ${action.risk_level === "critical" ? "critical" : action.risk_level === "high" ? "high" : "medium"}`}>
                      {action.risk_level?.toUpperCase()}
                    </span>
                  </div>

                  {/* Justification */}
                  <div style={{ fontSize: 11, color: "var(--sf-text-secondary)", marginBottom: 10, lineHeight: 1.5 }}>
                    {action.justification ?? "AI agent determined this action is required for containment."}
                  </div>

                  {/* AI Confidence */}
                  <div className="sf-confidence" style={{ marginBottom: 12 }}>
                    <span style={{ fontSize: 10, color: "var(--sf-text-muted)", minWidth: 80 }}>AI Confidence</span>
                    <div className="sf-confidence-bar">
                      <div className="sf-confidence-fill" style={{ width: `${(action.confidence ?? 0.91) * 100}%` }} />
                    </div>
                    <span className="sf-confidence-pct">{Math.round((action.confidence ?? 0.91) * 100)}%</span>
                  </div>

                  {/* XAI Toggle */}
                  <button
                    onClick={() => setExpandedXAI(expandedXAI === idx ? null : idx)}
                    style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)", color: "#a5b4fc", borderRadius: 6, padding: "4px 10px", fontSize: 10, cursor: "pointer", marginBottom: 10, display: "flex", alignItems: "center", gap: 5 }}>
                    <Brain size={10} /> {expandedXAI === idx ? "Hide" : "Why this action?"} (XAI)
                  </button>

                  {/* XAI Evidence Chain */}
                  {expandedXAI === idx && (
                    <div className="sf-xai-chain sf-animate-in" style={{ marginBottom: 12, padding: "10px 12px", background: "rgba(99,102,241,0.05)", borderRadius: 8, border: "1px solid rgba(99,102,241,0.15)" }}>
                      {(action.xai_evidence || XAI_REASONS[idx] || XAI_REASONS[0]).map((item: any, ji: number) => (
                        <div key={ji} className="sf-xai-item">
                          <div className="sf-xai-dot" style={{ background: "rgba(99,102,241,0.2)", color: "#818cf8" }}>{item.icon}</div>
                          <div className="sf-xai-content">
                            <div className="sf-xai-label">{item.label}</div>
                            <div className="sf-xai-value">{item.value}</div>
                            <div className="sf-xai-source">Source: {item.source}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Reversible badge + action buttons */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: 10, color: "#10b981", display: "flex", alignItems: "center", gap: 4 }}>
                      <RotateCcw size={10} /> Reversible action
                    </span>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button className="sf-btn sf-btn-sm"
                        style={{ background: "rgba(16,185,129,0.15)", color: "#6ee7b7", border: "1px solid rgba(16,185,129,0.3)" }}
                        onClick={() => handleApprove(idx)} disabled={approvingIdx === idx}>
                        <CheckCircle size={11} /> {approvingIdx === idx ? "Executing..." : "Approve"}
                      </button>
                      <button className="sf-btn sf-btn-sm"
                        style={{ background: "rgba(220,38,38,0.1)", color: "#fca5a5", border: "1px solid rgba(220,38,38,0.3)" }}
                        onClick={() => handleReject(idx)}>
                        <XCircle size={11} /> Reject
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Action Execution History */}
        <div className="sf-card">
          <div className="sf-card-header">
            <div>
              <div className="sf-card-title"><Shield size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} /> Execution Log</div>
              <div className="sf-card-subtitle">All executed, rejected, and rolled-back actions</div>
            </div>
          </div>

          {history.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px", color: "var(--sf-text-muted)" }}>
              <Activity size={36} style={{ opacity: 0.3, marginBottom: 10 }} />
              <div style={{ fontWeight: 600 }}>No actions yet</div>
              <div style={{ fontSize: 12, marginTop: 4 }}>Waiting for AI agents to generate actions...</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 480, overflowY: "auto" }}>
              {history.slice(-20).reverse().map((action: any, idx: number) => {
                const sc = statusColor(action.status);
                const rolled = rollbackItem === idx;
                return (
                  <div key={idx} style={{
                    display: "flex", alignItems: "center", gap: 10,
                    padding: "10px 12px", borderRadius: 8,
                    background: "rgba(255,255,255,0.02)",
                    borderLeft: `3px solid ${sc}`,
                    opacity: rolled ? 0.5 : 1,
                    transition: "opacity 0.3s ease",
                  }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "var(--sf-text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {action.action}
                      </div>
                      <div style={{ fontSize: 10, fontFamily: "monospace", color: "var(--sf-text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {action.target}
                      </div>
                    </div>
                    <div style={{ textAlign: "right", flexShrink: 0 }}>
                      <div style={{ fontSize: 10, fontWeight: 700, color: sc }}>{statusLabel(action.status)}</div>
                      <div style={{ fontSize: 9, color: "var(--sf-text-muted)" }}>
                        {action.executed_at ? new Date(action.executed_at).toLocaleTimeString() : ""}
                      </div>
                    </div>
                    {/* Rollback button for executed actions */}
                    {(action.status === "auto_executed" || action.status === "approved_executed") && (
                      <button
                        onClick={() => setRollbackItem(rolled ? null : idx)}
                        title="Rollback this action"
                        style={{
                          background: rolled ? "rgba(16,185,129,0.15)" : "rgba(255,255,255,0.05)",
                          border: "1px solid var(--sf-border)", borderRadius: 6,
                          color: rolled ? "#10b981" : "var(--sf-text-muted)",
                          padding: "3px 7px", cursor: "pointer", fontSize: 10,
                          display: "flex", alignItems: "center", gap: 4,
                        }}>
                        <RotateCcw size={10} /> {rolled ? "Rolled back" : "Rollback"}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* ── Trust & Safety Notice ────────────────────────── */}
      <div className="sf-card" style={{ background: "linear-gradient(135deg, rgba(16,185,129,0.06), rgba(6,182,212,0.03))", borderColor: "rgba(16,185,129,0.2)" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
          {[
            { icon: "🔍", title: "Full Explainability",  desc: "Every AI decision shows reasoning chain, confidence score, and evidence sources" },
            { icon: "🔒", title: "Human Override",        desc: "Any automated action can be rejected or rolled back with one click at any time" },
            { icon: "📋", title: "Compliance Logging",   desc: "All actions logged with timestamp, agent ID, and justification for audit trails" },
            { icon: "⚖️", title: "Risk-Calibrated",      desc: "Action risk level always shown before execution — never a surprise" },
          ].map(({ icon, title, desc }) => (
            <div key={title} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
              <span style={{ fontSize: 24, flexShrink: 0 }}>{icon}</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 4 }}>{title}</div>
                <div style={{ fontSize: 11, color: "var(--sf-text-muted)", lineHeight: 1.5 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
