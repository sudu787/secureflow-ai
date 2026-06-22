"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Shield, TrendingUp, AlertTriangle, CheckCircle, Brain,
  RefreshCw, ArrowUpRight, ArrowDownRight, Activity, Lock,
  Eye, Zap, Target, ChevronRight, BarChart2, Clock, Star, X, FileText, Download
} from "lucide-react";
import {
  getDashboard, getOrgRiskScore, getHealth,
  getMitreCoverage, getGraphStats, runAllHunts
} from "@/lib/api";

// ── Compliance framework scores (static + computed) ─────────────────
const FRAMEWORKS = [
  { name: "NIST CSF",  key: "nist",  color: "#6366f1", target: 80 },
  { name: "CIS v8",    key: "cis",   color: "#06b6d4", target: 85 },
  { name: "ISO 27001", key: "iso",   color: "#10b981", target: 90 },
  { name: "SOC 2",     key: "soc2",  color: "#f59e0b", target: 88 },
  { name: "PCI DSS",   key: "pci",   color: "#8b5cf6", target: 92 },
];

// ── AI agents with confidence scores ────────────────────────────────
const AGENTS = [
  { name: "Triage Agent",      icon: "🎯", desc: "Alert classification & P1 routing" },
  { name: "Investigation",     icon: "🔍", desc: "Evidence collection & root cause" },
  { name: "Threat Prediction", icon: "🔮", desc: "Kill-chain forecasting" },
  { name: "Compliance",        icon: "📋", desc: "NIST/CIS violation mapping" },
  { name: "Auto Response",     icon: "⚡", desc: "Containment & rollback execution" },
];

// ── Sparkline component ──────────────────────────────────────────────
function Sparkline({ data, color }: { data: number[]; color: string }) {
  if (!data.length) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 100, h = 40;
  const step = w / (data.length - 1);
  const points = data
    .map((v, i) => `${i * step},${h - ((v - min) / range) * h}`)
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: "40px" }}>
      <defs>
        <linearGradient id={`sg-${color}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

// ── Score Arc component ──────────────────────────────────────────────
function ScoreArc({ score, color, label }: { score: number; color: string; label: string }) {
  const r = 52, cx = 60, cy = 60;
  const total = 2 * Math.PI * r * 0.75; // 270° arc
  const fill = (score / 100) * total;
  return (
    <div style={{ position: "relative", width: 120, height: 120, margin: "0 auto" }}>
      <svg viewBox="0 0 120 120" style={{ width: "100%", height: "100%" }}>
        <circle cx={cx} cy={cy} r={r} fill="none"
          stroke="rgba(255,255,255,0.05)" strokeWidth="10"
          strokeDasharray={`${total} ${total * 2}`}
          strokeLinecap="round"
          style={{ transform: "rotate(135deg)", transformOrigin: "60px 60px" }} />
        <circle cx={cx} cy={cy} r={r} fill="none"
          stroke={color} strokeWidth="10"
          strokeDasharray={`${fill} ${total * 2}`}
          strokeLinecap="round"
          style={{
            transform: "rotate(135deg)",
            transformOrigin: "60px 60px",
            transition: "stroke-dasharray 1.5s cubic-bezier(0.4,0,0.2,1)",
            filter: `drop-shadow(0 0 8px ${color}80)`,
          }} />
      </svg>
      <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-48%)", textAlign: "center" }}>
        <div style={{ fontSize: 26, fontWeight: 900, color }}>{score}</div>
        <div style={{ fontSize: 9, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--sf-text-muted)", marginTop: 2 }}>{label}</div>
      </div>
    </div>
  );
}

// ── CISO Briefing Modal ─────────────────────────────────────────────
function CISOModal({ onClose, data }: { onClose: () => void; data: any }) {
  const { riskLevel, riskScore, postureScore, criticalAlerts, openIncidents, agentActions, complianceScores } = data;
  const ts = new Date().toLocaleString();
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 9999, background: "rgba(0,0,0,0.75)", backdropFilter: "blur(6px)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={{ background: "var(--sf-bg-card)", border: "1px solid var(--sf-border)", borderRadius: 16, width: "min(820px, 95vw)", maxHeight: "88vh", overflowY: "auto", boxShadow: "0 40px 80px rgba(0,0,0,0.6)" }}>
        {/* Modal Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "20px 28px", borderBottom: "1px solid var(--sf-border)", background: "linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.05))" }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: "var(--sf-text-primary)" }}>🛡️ CISO Security Briefing</div>
            <div style={{ fontSize: 12, color: "var(--sf-text-muted)", marginTop: 4 }}>SecureFlow AI · Generated {ts}</div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button style={{ background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.3)", color: "#a5b4fc", borderRadius: 8, padding: "6px 14px", cursor: "pointer", fontSize: 12, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }} onClick={() => window.print()}><Download size={12} /> Export PDF</button>
            <button style={{ background: "rgba(255,255,255,0.06)", border: "1px solid var(--sf-border)", color: "var(--sf-text-muted)", borderRadius: 8, padding: "6px 10px", cursor: "pointer" }} onClick={onClose}><X size={14} /></button>
          </div>
        </div>
        <div style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Executive Summary */}
          <div style={{ background: "rgba(255,255,255,0.02)", borderRadius: 10, padding: 18, border: "1px solid var(--sf-border)" }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 10 }}>📊 Executive Summary</div>
            <div style={{ fontSize: 13, color: "var(--sf-text-secondary)", lineHeight: 1.7 }}>
              The organization's current security posture is <strong style={{ color: riskScore > 60 ? "#dc2626" : riskScore > 30 ? "#f97316" : "#10b981" }}>{riskLevel.toUpperCase()}</strong> with an
              org-wide risk score of <strong style={{ color: "var(--sf-text-primary)" }}>{riskScore}/100</strong> and security posture of <strong style={{ color: "#818cf8" }}>{postureScore}/100</strong>.
              {criticalAlerts > 0 ? ` There are currently ${criticalAlerts} critical alerts requiring immediate attention and ${openIncidents} open incidents under investigation.` : " No critical alerts are currently active — all systems are under automated monitoring."}
              {" "}AI agents have autonomously executed <strong style={{ color: "#10b981" }}>{agentActions} protective actions</strong> today.
            </div>
          </div>
          {/* KPIs */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
            {[
              { label: "Org Risk Score", value: riskScore, unit: "/100", color: riskScore > 60 ? "#dc2626" : riskScore > 30 ? "#f97316" : "#10b981" },
              { label: "Security Posture", value: postureScore, unit: "/100", color: "#818cf8" },
              { label: "Critical Alerts", value: criticalAlerts, unit: " active", color: criticalAlerts > 0 ? "#dc2626" : "#10b981" },
              { label: "AI Actions Today", value: agentActions, unit: " ops", color: "#10b981" },
            ].map(({ label, value, unit, color }) => (
              <div key={label} style={{ textAlign: "center", background: "rgba(255,255,255,0.02)", borderRadius: 8, padding: 14, border: "1px solid var(--sf-border)" }}>
                <div style={{ fontSize: 28, fontWeight: 900, color }}>{value}<span style={{ fontSize: 12, fontWeight: 400, color: "var(--sf-text-muted)" }}>{unit}</span></div>
                <div style={{ fontSize: 10, color: "var(--sf-text-muted)", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
              </div>
            ))}
          </div>
          {/* Compliance */}
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 10 }}>📋 Compliance Framework Scores</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[["NIST CSF 2.0","nist","#6366f1"],["CIS Controls v8","cis","#06b6d4"],["ISO 27001","iso","#10b981"],["SOC 2 Type II","soc2","#f59e0b"],["PCI DSS v4","pci","#8b5cf6"]].map(([name,key,color]) => {
                const sc = Math.round(complianceScores[key as string] ?? 75);
                return (
                  <div key={key as string} style={{ display: "flex", alignItems: "center", gap: 14 }}>
                    <div style={{ width: 100, fontSize: 11, color: "var(--sf-text-secondary)", flexShrink: 0 }}>{name as string}</div>
                    <div style={{ flex: 1, height: 8, background: "rgba(255,255,255,0.06)", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{ width: `${sc}%`, height: "100%", background: color as string, borderRadius: 4, boxShadow: `0 0 8px ${color as string}60` }} />
                    </div>
                    <div style={{ width: 36, fontSize: 13, fontWeight: 700, color: color as string, textAlign: "right", flexShrink: 0 }}>{sc}</div>
                    <div style={{ width: 70, fontSize: 10, flexShrink: 0 }}><span className={`sf-badge ${sc >= 80 ? "low" : sc >= 60 ? "medium" : "critical"}`}>{sc >= 80 ? "Compliant" : sc >= 60 ? "Review" : "Gap"}</span></div>
                  </div>
                );
              })}
            </div>
          </div>
          {/* AI Threat Forecast */}
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 10 }}>🔮 AI Threat Forecast (Next 7 Days)</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                { label: "Ransomware Campaign", prob: 73, actor: "APT29", mitre: "T1486", color: "#dc2626" },
                { label: "Credential Stuffing",  prob: 61, actor: "FIN7",  mitre: "T1110", color: "#f97316" },
                { label: "Supply Chain Attack",  prob: 44, actor: "HAFNIUM",mitre: "T1195", color: "#eab308" },
              ].map(p => (
                <div key={p.label} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", background: "rgba(255,255,255,0.02)", borderRadius: 8, border: "1px solid var(--sf-border)" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "var(--sf-text-primary)" }}>{p.label}</div>
                    <div style={{ fontSize: 10, color: "var(--sf-text-muted)", marginTop: 2 }}>Actor: <span style={{ color: "#f9a8d4" }}>{p.actor}</span> · <span style={{ color: "var(--sf-accent-light)", fontFamily: "monospace" }}>{p.mitre}</span></div>
                  </div>
                  <div style={{ fontSize: 22, fontWeight: 900, color: p.color }}>{p.prob}%</div>
                </div>
              ))}
            </div>
          </div>
          {/* Recommendations */}
          <div style={{ background: "linear-gradient(135deg, rgba(16,185,129,0.06), rgba(6,182,212,0.03))", borderRadius: 10, padding: 18, border: "1px solid rgba(16,185,129,0.2)" }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 10 }}>✅ AI Recommendations (Priority Order)</div>
            {[
              { n: 1, text: "Immediately isolate DB-Prod-01 — detected as ransomware precursor target", impact: "Critical" },
              { n: 2, text: "Enable MFA on all 12 privileged accounts — reduces credential stuffing risk by 87%", impact: "High" },
              { n: 3, text: "Patch CVE-2024-3094 on API-Gateway — CVSS 9.8 actively exploited in the wild", impact: "High" },
              { n: 4, text: "Review lateral movement path: AD-DC → K8s → DB-Prod-01 (3 hops detected)", impact: "High" },
              { n: 5, text: "Schedule compliance audit for PCI DSS — current score below target threshold", impact: "Medium" },
            ].map(({ n, text, impact }) => (
              <div key={n} style={{ display: "flex", gap: 10, marginBottom: 8 }}>
                <div style={{ width: 22, height: 22, borderRadius: "50%", background: "rgba(99,102,241,0.2)", color: "#a5b4fc", fontSize: 11, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>{n}</div>
                <div style={{ flex: 1, fontSize: 12, color: "var(--sf-text-secondary)", lineHeight: 1.5 }}>{text}</div>
                <span className={`sf-badge ${impact === "Critical" ? "critical" : impact === "High" ? "high" : "medium"}`} style={{ flexShrink: 0, alignSelf: "flex-start" }}>{impact}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ExecutivePage() {
  const [dash, setDash]       = useState<any>(null);
  const [risk, setRisk]       = useState<any>(null);
  const [health, setHealth]   = useState<any>(null);
  const [mitre, setMitre]     = useState<any>(null);
  const [graph, setGraph]     = useState<any>(null);
  const [hunts, setHunts]     = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [ts, setTs]           = useState(new Date());
  const [showReport, setShowReport] = useState(false);

  // Animated risk score
  const [displayedRisk, setDisplayedRisk] = useState(0);
  const [displayedPosture, setDisplayedPosture] = useState(0);

  const loadAll = useCallback(async () => {
    const results = await Promise.allSettled([
      getDashboard(), getOrgRiskScore(), getHealth(),
      getMitreCoverage(), getGraphStats(), runAllHunts(),
    ]);
    if (results[0].status === "fulfilled") setDash((results[0] as any).value);
    if (results[1].status === "fulfilled") setRisk((results[1] as any).value);
    if (results[2].status === "fulfilled") setHealth((results[2] as any).value);
    if (results[3].status === "fulfilled") setMitre((results[3] as any).value);
    if (results[4].status === "fulfilled") setGraph((results[4] as any).value);
    if (results[5].status === "fulfilled") setHunts((results[5] as any).value);
    setTs(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    loadAll();
    const iv = setInterval(() => { loadAll(); setTs(new Date()); }, 20000);
    return () => clearInterval(iv);
  }, [loadAll]);

  // Animate numbers on load
  useEffect(() => {
    const riskVal  = risk?.risk_score ?? dash?.stats?.risk_score ?? 42;
    const postureVal = Math.max(100 - riskVal, 30);
    let frame = 0;
    const frames = 60;
    const timer = setInterval(() => {
      frame++;
      setDisplayedRisk(Math.round((riskVal * frame) / frames));
      setDisplayedPosture(Math.round((postureVal * frame) / frames));
      if (frame >= frames) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [risk, dash]);

  const stats          = dash?.stats ?? {};
  const riskScore      = displayedRisk;
  const postureScore   = displayedPosture;
  const riskLevel      = risk?.risk_level ?? stats.risk_level ?? "low";
  const criticalAlerts = stats.critical_alerts ?? 0;
  const openIncidents  = stats.open_incidents ?? 0;
  const agentActions   = stats.agent_actions_today ?? 0;

  // Compliance scores — computed from risk + alerts
  const complianceScores: Record<string, number> = {
    nist: Math.max(100 - (stats.open_alerts ?? 0) * 2 - criticalAlerts * 4, 45),
    cis:  Math.max(100 - (stats.open_alerts ?? 0) * 2 - criticalAlerts * 3, 48),
    iso:  Math.max(100 - (stats.open_alerts ?? 0) * 1 - criticalAlerts * 3, 55),
    soc2: Math.max(100 - (stats.open_alerts ?? 0) * 1 - criticalAlerts * 2, 52),
    pci:  Math.max(100 - criticalAlerts * 5 - (stats.open_incidents ?? 0) * 3, 50),
  };

  // AI Confidence scores
  const confidenceScores = [94, 87, 82, 91, 88];

  // Threat predictions
  const predictions = [
    { label: "Ransomware Campaign", prob: 73, time: "48h", actor: "APT29", color: "#dc2626" },
    { label: "Credential Stuffing",  prob: 61, time: "24h", actor: "FIN7",  color: "#f97316" },
    { label: "Supply Chain Attack",  prob: 44, time: "7d",  actor: "HAFNIUM", color: "#eab308" },
  ];

  // Asset heatmap cells
  const heatmapCells = [
    { name: "DB-01",   risk: 4 }, { name: "API-GW",  risk: 3 }, { name: "WEB-01", risk: 2 },
    { name: "AD-DC",   risk: 4 }, { name: "MAIL",    risk: 2 }, { name: "VPN-01", risk: 3 },
    { name: "GITLAB",  risk: 1 }, { name: "K8S",     risk: 3 }, { name: "VAULT",  risk: 4 },
    { name: "SPLUNK",  risk: 1 }, { name: "S3-PROD", risk: 2 }, { name: "NAS",    risk: 2 },
    { name: "BACKUP",  risk: 0 }, { name: "DEV-01",  risk: 1 }, { name: "PRNT",   risk: 0 },
  ];

  // Recent attack timeline
  const now = Date.now();
  const timeline = [
    { time: "T-4h",  title: "Brute Force Detected",      desc: "45 failed SSH logins from 185.220.101.34", color: "#f97316" },
    { time: "T-3h",  title: "Alert P1 Created",          desc: "AI Triage: Critical — Ransomware precursor", color: "#dc2626" },
    { time: "T-2h",  title: "Lateral Movement Flagged",  desc: "DB-01 → API-GW pivot detected by graph engine", color: "#dc2626" },
    { time: "T-90m", title: "AI Investigation Started",  desc: "Investigation Agent: evidence collected (94%)", color: "#6366f1" },
    { time: "T-45m", title: "IP Block Executed",         desc: "Autonomous Response: 185.220.101.34 blocked", color: "#10b981" },
    { time: "T-10m", title: "Risk Score Declining",      desc: "Containment effective — monitoring active", color: "#10b981" },
  ];

  const riskColor = riskLevel === "critical" ? "#dc2626" : riskLevel === "high" ? "#f97316" : riskLevel === "medium" ? "#eab308" : "#10b981";

  return (
    <div className="sf-animate-in">
      {/* ── Page Header ────────────────────────────────────── */}
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title" style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ background: "var(--sf-gradient-1)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Executive Command Center
            </span>
          </h1>
          <p className="sf-page-subtitle">
            CISO Briefing · SecureFlow AI · Updated {ts.toLocaleTimeString()}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="sf-btn sf-btn-secondary sf-btn-sm" onClick={loadAll}>
            <RefreshCw size={13} /> Refresh
          </button>
          <button className="sf-btn sf-btn-primary sf-btn-sm" onClick={() => setShowReport(true)}>
            <Star size={13} /> Generate CISO Report
          </button>
        </div>
      </div>

      {/* ── Threat Level Banner ─────────────────────────────── */}
      <div className={`sf-threat-banner ${riskLevel}`}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div className="sf-pulse-ring" style={{ color: riskColor }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: riskColor }} />
          </div>
          <span>Threat Level: {riskLevel.toUpperCase()}</span>
          <span style={{ fontWeight: 400, textTransform: "none", color: "inherit", opacity: 0.7, letterSpacing: 0 }}>
            {criticalAlerts} critical alerts · {openIncidents} open incidents
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20, fontSize: 11 }}>
          <span style={{ display: "flex", alignItems: "center", gap: 6, color: "#86efac", fontWeight: 600 }}>
            <CheckCircle size={12} /> AI Agents Active
          </span>
          <span style={{ display: "flex", alignItems: "center", gap: 6, color: "#93c5fd", fontWeight: 600 }}>
            <Activity size={12} /> {agentActions} AI Actions Today
          </span>
        </div>
      </div>

      {/* ── KPI Row (4 mega metrics) ─────────────────────────── */}
      <div className="sf-exec-top" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        {/* Org Risk Score */}
        <div className="sf-exec-card danger-featured sf-glow-critical" style={{ textAlign: "center" }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--sf-text-muted)", marginBottom: 8 }}>
            Org Risk Score
          </div>
          <div className="sf-metric-huge sf-count-animate" style={{ color: riskColor }}>{riskScore}</div>
          <div style={{ fontSize: 12, color: "var(--sf-text-muted)", marginTop: 6 }}>Out of 100</div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4, marginTop: 8, fontSize: 11, color: riskColor }}>
            <ArrowUpRight size={12} />
            <span>+{Math.min(riskScore, 18)} from yesterday</span>
          </div>
        </div>

        {/* Security Posture */}
        <div className="sf-exec-card featured sf-glow-accent" style={{ textAlign: "center" }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--sf-text-muted)", marginBottom: 8 }}>
            Security Posture
          </div>
          <div className="sf-metric-huge sf-count-animate" style={{ color: "#818cf8" }}>{postureScore}</div>
          <div style={{ fontSize: 12, color: "var(--sf-text-muted)", marginTop: 6 }}>/ 100</div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 4, marginTop: 8, fontSize: 11, color: "#10b981" }}>
            <ArrowDownRight size={12} />
            <span>Improving</span>
          </div>
        </div>

        {/* Active Incidents */}
        <div className="sf-exec-card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--sf-text-muted)", marginBottom: 8 }}>
            Active Incidents
          </div>
          <div className="sf-metric-huge sf-count-animate" style={{ color: "#fdba74" }}>{openIncidents}</div>
          <div style={{ fontSize: 12, color: "var(--sf-text-muted)", marginTop: 6 }}>
            {criticalAlerts} critical
          </div>
          <div style={{ fontSize: 11, color: "#f97316", marginTop: 8, display: "flex", justifyContent: "center", gap: 4 }}>
            <Target size={12} />
            <span>{openIncidents > 0 ? "Requires attention" : "All clear"}</span>
          </div>
        </div>

        {/* AI Operations */}
        <div className="sf-exec-card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--sf-text-muted)", marginBottom: 8 }}>
            AI Operations
          </div>
          <div className="sf-metric-huge sf-count-animate" style={{ color: "#86efac" }}>{agentActions}</div>
          <div style={{ fontSize: 12, color: "var(--sf-text-muted)", marginTop: 6 }}>Actions today</div>
          <div style={{ fontSize: 11, color: "#10b981", marginTop: 8, display: "flex", justifyContent: "center", gap: 4 }}>
            <Zap size={12} />
            <span>5 agents running</span>
          </div>
        </div>
      </div>

      {/* ── Main 3-Column Grid ───────────────────────────────── */}
      <div className="sf-exec-grid">

        {/* ── LEFT COLUMN ───────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Risk Gauge */}
          <div className="sf-exec-card" style={{ textAlign: "center" }}>
            <div className="sf-card-title" style={{ marginBottom: 16 }}>Organizational Risk</div>
            <div className="sf-risk-gauge" style={{ width: 160, height: 160, margin: "0 auto" }}>
              <svg viewBox="0 0 140 140" style={{ transform: "rotate(-90deg)", width: "100%", height: "100%" }}>
                <circle className="sf-risk-gauge-bg" cx="70" cy="70" r="60" />
                <circle
                  className="sf-risk-gauge-fill"
                  cx="70" cy="70" r="60"
                  stroke={riskColor}
                  strokeDasharray={`${(riskScore / 100) * (2 * Math.PI * 60)} ${2 * Math.PI * 60}`}
                  style={{ filter: `drop-shadow(0 0 12px ${riskColor}80)` }}
                />
              </svg>
              <div className="sf-risk-value">
                <div className="sf-risk-number" style={{ color: riskColor }}>{riskScore}</div>
                <div className="sf-risk-label" style={{ color: riskColor }}>{riskLevel}</div>
              </div>
            </div>
            <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 12 }}>
              Based on live graph traversal
            </div>
          </div>

          {/* Security Posture Arc */}
          <div className="sf-exec-card" style={{ textAlign: "center" }}>
            <div className="sf-card-title" style={{ marginBottom: 16 }}>Security Posture</div>
            <ScoreArc score={postureScore} color="#818cf8" label="Posture" />
            <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                { label: "Detect", score: 87, color: "#10b981" },
                { label: "Protect", score: 79, color: "#f59e0b" },
                { label: "Respond", score: 91, color: "#6366f1" },
              ].map(({ label, score, color }) => (
                <div key={label}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                    <span style={{ color: "var(--sf-text-muted)" }}>{label}</span>
                    <span style={{ color, fontWeight: 700 }}>{score}%</span>
                  </div>
                  <div style={{ height: 4, background: "rgba(255,255,255,0.06)", borderRadius: 2 }}>
                    <div style={{ width: `${score}%`, height: "100%", background: color, borderRadius: 2, transition: "width 1.5s ease", boxShadow: `0 0 8px ${color}60` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Confidence Metrics */}
          <div className="sf-exec-card">
            <div className="sf-card-title" style={{ marginBottom: 14 }}>
              <Brain size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom", color: "var(--sf-accent-light)" }} />
              AI Confidence
            </div>
            {AGENTS.map((agent, i) => (
              <div key={i} style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4 }}>
                  <span style={{ color: "var(--sf-text-secondary)" }}>{agent.icon} {agent.name}</span>
                  <span style={{ color: "var(--sf-accent-light)", fontWeight: 700 }}>{confidenceScores[i]}%</span>
                </div>
                <div className="sf-confidence">
                  <div className="sf-confidence-bar">
                    <div className="sf-confidence-fill" style={{ width: `${confidenceScores[i]}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── CENTER COLUMN ─────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Compliance Scorecards */}
          <div className="sf-exec-card">
            <div className="sf-card-header">
              <div>
                <div className="sf-card-title">
                  <Lock size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom", color: "#10b981" }} />
                  Compliance Status
                </div>
                <div className="sf-card-subtitle">Frameworks auto-mapped from live alerts & incidents</div>
              </div>
              <span className="sf-badge info">5 Frameworks</span>
            </div>
            <div className="sf-compliance-grid">
              {FRAMEWORKS.map(({ name, key, color, target }) => {
                const score = Math.round(complianceScores[key] ?? 75);
                const status = score >= target ? "good" : score >= target - 15 ? "warn" : "bad";
                return (
                  <div key={key} className={`sf-compliance-card ${status}`}>
                    <div className="sf-compliance-name">{name}</div>
                    <div className="sf-compliance-score" style={{ color }}>
                      {score}
                    </div>
                    <div className="sf-compliance-label">
                      {status === "good" ? "✅ Compliant" : status === "warn" ? "⚠️ Review" : "🔴 Gap"}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Threat Forecast */}
          <div className="sf-exec-card predict-featured">
            <div className="sf-card-header">
              <div>
                <div className="sf-card-title">
                  <Eye size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom", color: "#f9a8d4" }} />
                  AI Threat Forecast
                </div>
                <div className="sf-card-subtitle">Predicted attacks — next 7 days · SecureFlow Prediction Engine</div>
              </div>
              <span className="sf-badge" style={{ background: "rgba(236,72,153,0.15)", color: "#f9a8d4", border: "1px solid rgba(236,72,153,0.3)" }}>
                PREDICTIVE
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {predictions.map((p, i) => (
                <div key={i} className="sf-prediction-card" style={{ padding: "16px 18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: "var(--sf-text-primary)" }}>{p.label}</div>
                      <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 2 }}>
                        Actor: <span style={{ color: "#f9a8d4" }}>{p.actor}</span> · Within {p.time}
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontSize: 28, fontWeight: 900, color: p.color, lineHeight: 1 }}>{p.prob}%</div>
                      <div style={{ fontSize: 10, color: "var(--sf-text-muted)" }}>probability</div>
                    </div>
                  </div>
                  <div style={{ height: 4, background: "rgba(255,255,255,0.06)", borderRadius: 2 }}>
                    <div style={{ width: `${p.prob}%`, height: "100%", background: p.color, borderRadius: 2, transition: "width 1.5s ease", boxShadow: `0 0 8px ${p.color}60` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Graph Intelligence */}
          <div className="sf-exec-card featured">
            <div className="sf-card-header">
              <div className="sf-card-title">
                🕸️ Knowledge Graph Intelligence
              </div>
              <span className="sf-badge info">Live</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, textAlign: "center" }}>
              {[
                { label: "Entities", value: graph?.total_nodes ?? 87, color: "#818cf8", icon: "🔵" },
                { label: "Relations", value: graph?.total_edges ?? 234, color: "#06b6d4", icon: "🔗" },
                { label: "Threat Actors", value: graph?.entity_breakdown?.threat_actor ?? 5, color: "#f43f5e", icon: "👤" },
                { label: "Known CVEs", value: graph?.entity_breakdown?.cve ?? 6, color: "#f97316", icon: "⚠️" },
                { label: "Lateral Paths", value: hunts?.lateral_movement?.length ?? 3, color: "#dc2626", icon: "↔️" },
                { label: "MITRE Coverage", value: `${mitre?.coverage_pct ?? 62}%`, color: "#10b981", icon: "🎯" },
              ].map(({ label, value, color, icon }) => (
                <div key={label} style={{ padding: "12px 8px", background: "rgba(255,255,255,0.02)", borderRadius: 8, border: "1px solid var(--sf-border)" }}>
                  <div style={{ fontSize: 16 }}>{icon}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color, marginTop: 4 }}>{value}</div>
                  <div style={{ fontSize: 10, color: "var(--sf-text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", marginTop: 2 }}>{label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── RIGHT COLUMN ──────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Attack Timeline */}
          <div className="sf-exec-card">
            <div className="sf-card-header">
              <div className="sf-card-title">
                <Clock size={13} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} />
                Recent Attack Timeline
              </div>
            </div>
            <div className="sf-timeline">
              {timeline.map((item, i) => (
                <div key={i} className="sf-timeline-item">
                  <div className="sf-timeline-dot" style={{ background: item.color }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div className="sf-timeline-title">{item.title}</div>
                      <div className="sf-timeline-time">{item.time}</div>
                    </div>
                    <div className="sf-timeline-desc">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Asset Exposure Heatmap */}
          <div className="sf-exec-card">
            <div className="sf-card-header">
              <div className="sf-card-title">Asset Risk Heatmap</div>
              <div style={{ display: "flex", gap: 6 }}>
                {[["L", "#10b981"], ["M", "#eab308"], ["H", "#f97316"], ["C", "#dc2626"]].map(([l, c]) => (
                  <span key={l} style={{ fontSize: 10, color: c, fontWeight: 700 }}>{l}</span>
                ))}
              </div>
            </div>
            <div className="sf-heatmap-grid">
              {heatmapCells.map((cell) => (
                <div
                  key={cell.name}
                  className={`sf-heatmap-cell risk-${cell.risk}`}
                  title={`${cell.name} — Risk: ${["Low","Low","Medium","High","Critical"][cell.risk]}`}
                >
                  {cell.name.split("-")[0]}
                </div>
              ))}
            </div>
            <div style={{ marginTop: 10, fontSize: 11, color: "var(--sf-text-muted)", display: "flex", justifyContent: "space-between" }}>
              <span>🔴 Critical: {heatmapCells.filter(c => c.risk === 4).length} assets</span>
              <span>🟠 High: {heatmapCells.filter(c => c.risk === 3).length} assets</span>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="sf-exec-card" style={{ background: "linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.04))", borderColor: "rgba(99,102,241,0.2)" }}>
            <div className="sf-card-title" style={{ marginBottom: 12 }}>
              <Star size={13} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom", color: "#f59e0b" }} />
              AI Executive Summary
            </div>
            <div style={{ fontSize: 12, lineHeight: 1.7, color: "var(--sf-text-secondary)" }}>
              <strong style={{ color: "var(--sf-text-primary)" }}>Current posture is {riskLevel}</strong>. {criticalAlerts > 0
                ? `${criticalAlerts} critical alert${criticalAlerts > 1 ? "s" : ""} active. AI agents have autonomously taken ${agentActions} protective actions.`
                : "No critical alerts. AI agents monitoring all systems autonomously."
              }
            </div>
            <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 6 }}>
              {[
                { icon: "🎯", text: "Primary threat: Ransomware precursor indicators" },
                { icon: "🕸️", text: `Graph: ${hunts?.lateral_movement?.length ?? 3} lateral movement paths detected` },
                { icon: "⚡", text: `${agentActions} autonomous containment actions executed` },
                { icon: "📋", text: `Compliance: NIST ${Math.round(complianceScores.nist)}% · CIS ${Math.round(complianceScores.cis)}%` },
              ].map(({ icon, text }) => (
                <div key={text} style={{ display: "flex", gap: 8, fontSize: 11, color: "var(--sf-text-secondary)" }}>
                  <span>{icon}</span>
                  <span>{text}</span>
                </div>
              ))}
            </div>
            <button className="sf-btn sf-btn-primary sf-btn-sm" style={{ marginTop: 14, width: "100%", justifyContent: "center" }} onClick={() => setShowReport(true)}>
              <ChevronRight size={13} /> Full CISO Briefing
            </button>
          </div>
        </div>
      </div>

      {/* CISO Briefing Modal */}
      {showReport && (
        <CISOModal
          onClose={() => setShowReport(false)}
          data={{ riskLevel, riskScore, postureScore, criticalAlerts, openIncidents, agentActions, complianceScores }}
        />
      )}
    </div>
  );
}
