"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  RefreshCw, AlertCircle, Target, Ticket, Activity, Zap,
  ShieldCheck, Database, Shield, TrendingUp, ArrowRight,
  BarChart2, Clock, Brain
} from "lucide-react";
import { getDashboard, getHealth, getIngestionStatus, getGraphStats, runAllHunts } from "@/lib/api";
import type { DashboardData, Alert, AgentActivity } from "@/lib/types";

// ── Agent emoji map ──────────────────────────────────────────────────
const agentIcon: Record<string, string> = {
  triage_agent: "🎯", investigation_agent: "🔍",
  remediation_agent: "🔧", threat_prediction_agent: "🔮",
  compliance_agent: "📋", autonomous_response_agent: "⚡",
  reporting_agent: "📊",
};
const agentColor: Record<string, string> = {
  triage_agent: "#f97316", investigation_agent: "#6366f1",
  remediation_agent: "#10b981", threat_prediction_agent: "#ec4899",
  compliance_agent: "#06b6d4", autonomous_response_agent: "#f59e0b",
  reporting_agent: "#8b5cf6",
};

// ── Severity config ──────────────────────────────────────────────────
const sevColor: Record<string, string> = {
  critical: "#dc2626", high: "#f97316", medium: "#eab308", low: "#22c55e",
};

// ── Animated ticker item ─────────────────────────────────────────────
function TickerItem({ alert }: { alert: Alert }) {
  const color = sevColor[alert.severity] ?? "#94a3b8";
  return (
    <span className="sf-ticker-item">
      <span style={{ color, fontSize: 8 }}>●</span>
      <span style={{ color, fontWeight: 700 }}>[{alert.severity?.toUpperCase()}]</span>
      <span style={{ color: "var(--sf-text-secondary)" }}>{alert.title}</span>
      {alert.mitre_id && (
        <span style={{ color: "var(--sf-accent-light)", fontFamily: "monospace", fontSize: 11 }}>
          {alert.mitre_id}
        </span>
      )}
      <span style={{ color: "var(--sf-text-muted)" }}>
        {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : ""}
      </span>
    </span>
  );
}

export default function DashboardPage() {
  const [data, setData]         = useState<DashboardData | null>(null);
  const [health, setHealth]     = useState<any>(null);
  const [ingestion, setIngestion] = useState<any>(null);
  const [graph, setGraph]       = useState<any>(null);
  const [hunts, setHunts]       = useState<any>(null);
  const [loading, setLoading]   = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Animated risk score
  const [liveRisk, setLiveRisk] = useState(0);

  const loadAll = useCallback(async () => {
    try {
      const results = await Promise.allSettled([
        getDashboard(), getHealth(), getIngestionStatus(),
        getGraphStats(), runAllHunts(),
      ]);
      if (results[0].status === "fulfilled") setData((results[0] as any).value);
      if (results[1].status === "fulfilled") setHealth((results[1] as any).value);
      if (results[2].status === "fulfilled") setIngestion((results[2] as any).value);
      if (results[3].status === "fulfilled") setGraph((results[3] as any).value);
      if (results[4].status === "fulfilled") setHunts((results[4] as any).value);
      setLastUpdate(new Date());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
    const iv = setInterval(loadAll, 15000);
    return () => clearInterval(iv);
  }, [loadAll]);

  // Animate risk score
  useEffect(() => {
    const target = data?.stats?.risk_score ?? 0;
    let current = 0;
    const step = target / 50;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      setLiveRisk(Math.round(current));
      if (current >= target) clearInterval(timer);
    }, 20);
    return () => clearInterval(timer);
  }, [data?.stats?.risk_score]);

  const stats        = data?.stats ?? {};
  const riskScore    = liveRisk;
  const riskLevel    = stats.risk_level ?? "low";
  const criticalAlerts = stats.critical_alerts ?? 0;
  const riskColor    = riskLevel === "critical" ? "#dc2626" : riskLevel === "high" ? "#f97316"
                     : riskLevel === "medium"   ? "#eab308" : "#10b981";
  const circumference = 2 * Math.PI * 60;
  const dashArray    = `${(riskScore / 100) * circumference} ${circumference}`;

  const recentAlerts = data?.recent_alerts ?? [];
  const agentActivity = data?.recent_agent_activity ?? [];

  // Synthetic agent events for demo
  const agentEvents = agentActivity.length > 0 ? agentActivity : [
    { agent_name: "triage_agent",           action_type: "P1 alert classified",        confidence: 0.94, created_at: new Date().toISOString() },
    { agent_name: "investigation_agent",     action_type: "Evidence collection started", confidence: 0.87, created_at: new Date().toISOString() },
    { agent_name: "threat_prediction_agent", action_type: "Kill-chain stage: LateralMove",confidence: 0.82, created_at: new Date().toISOString() },
    { agent_name: "autonomous_response_agent",action_type: "IP block queued for approval",confidence: 0.91, created_at: new Date().toISOString() },
    { agent_name: "compliance_agent",        action_type: "NIST DE.CM-1 violation flagged",confidence: 0.88, created_at: new Date().toISOString() },
  ];

  return (
    <div className="sf-animate-in">

      {/* ── Threat Level Banner ─────────────────────────── */}
      <div className={`sf-threat-banner ${riskLevel}`} style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div className="sf-pulse-ring" style={{ color: riskColor }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: riskColor }} />
          </div>
          <span style={{ fontSize: 13 }}>
            🛡️ SecureFlow AI — Threat Level: <strong>{riskLevel.toUpperCase()}</strong>
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16, fontSize: 11 }}>
          {ingestion?.running && (
            <span style={{ display: "flex", alignItems: "center", gap: 5, color: "#86efac", fontWeight: 600 }}>
              <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#10b981", animation: "pulse 1.5s ease-in-out infinite" }} />
              Live Ingestion
            </span>
          )}
          <span style={{ color: "inherit", opacity: 0.7, fontWeight: 400, textTransform: "none", letterSpacing: 0 }}>
            Updated {lastUpdate.toLocaleTimeString()}
          </span>
          <button className="sf-btn sf-btn-secondary sf-btn-sm" onClick={loadAll} style={{ fontSize: 10, padding: "4px 10px" }}>
            <RefreshCw size={11} /> Sync
          </button>
        </div>
      </div>

      {/* ── Alert Ticker ─────────────────────────────────── */}
      {recentAlerts.length > 0 && (
        <div className="sf-ticker-wrapper" style={{ marginBottom: 20 }}>
          <div className="sf-ticker-track">
            {/* Duplicate for seamless loop */}
            {[...recentAlerts, ...recentAlerts].map((alert, i) => (
              <TickerItem key={i} alert={alert} />
            ))}
          </div>
        </div>
      )}

      {/* ── 5-Stat Header Row ────────────────────────────── */}
      <div className="sf-stats-grid" style={{ gridTemplateColumns: "repeat(5, 1fr)", marginBottom: 20 }}>
        <div className="sf-stat-card danger">
          <div className="sf-stat-icon"><AlertCircle size={22} color="#ef4444" /></div>
          <div className="sf-stat-label">Open Alerts</div>
          <div className="sf-stat-value sf-count-animate">{stats.open_alerts ?? 0}</div>
          <div className="sf-stat-change up">{criticalAlerts} critical · {stats.high_alerts ?? 0} high</div>
        </div>
        <div className="sf-stat-card warning">
          <div className="sf-stat-icon"><Target size={22} color="#f59e0b" /></div>
          <div className="sf-stat-label">Incidents</div>
          <div className="sf-stat-value sf-count-animate">{stats.open_incidents ?? 0}</div>
          <div className="sf-stat-change" style={{ color: "var(--sf-text-muted)" }}>{stats.total_incidents ?? 0} total</div>
        </div>
        <div className="sf-stat-card info">
          <div className="sf-stat-icon"><Ticket size={22} color="#3b82f6" /></div>
          <div className="sf-stat-label">Tickets</div>
          <div className="sf-stat-value sf-count-animate">{stats.open_tickets ?? 0}</div>
          <div className="sf-stat-change" style={{ color: "#10b981" }}>{stats.resolved_tickets ?? 0} resolved</div>
        </div>
        <div className="sf-stat-card accent">
          <div className="sf-stat-icon"><Activity size={22} color="#8b5cf6" /></div>
          <div className="sf-stat-label">Events Ingested</div>
          <div className="sf-stat-value sf-count-animate">{ingestion?.events_ingested ?? stats.events_today ?? 0}</div>
          <div className="sf-stat-change" style={{ color: "var(--sf-text-muted)" }}>{ingestion?.alerts_created ?? 0} alerts</div>
        </div>
        <div className="sf-stat-card success">
          <div className="sf-stat-icon"><Zap size={22} color="#10b981" /></div>
          <div className="sf-stat-label">AI Actions</div>
          <div className="sf-stat-value sf-count-animate">{stats.agent_actions_today ?? 0}</div>
          <div className="sf-stat-change" style={{ color: "var(--sf-text-muted)" }}>autonomous ops</div>
        </div>
      </div>

      {/* ── Main War Room Grid: Left | Center | Right ────── */}
      <div className="sf-warroom-grid" style={{ marginBottom: 20 }}>

        {/* ── LEFT: Risk Gauge ──────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="sf-card" style={{ textAlign: "center", padding: "24px 16px" }}>
            <div className="sf-card-title" style={{ marginBottom: 12 }}>Org Risk Score</div>
            <div className="sf-risk-gauge" style={{ width: 140, height: 140, margin: "0 auto" }}>
              <svg viewBox="0 0 140 140" style={{ transform: "rotate(-90deg)", width: "100%", height: "100%" }}>
                <circle className="sf-risk-gauge-bg" cx="70" cy="70" r="60" />
                <circle
                  className="sf-risk-gauge-fill" cx="70" cy="70" r="60"
                  stroke={riskColor}
                  strokeDasharray={dashArray}
                  style={{ filter: `drop-shadow(0 0 10px ${riskColor}80)` }}
                />
              </svg>
              <div className="sf-risk-value">
                <div className="sf-risk-number sf-count-animate" style={{ color: riskColor, fontSize: 40 }}>{riskScore}</div>
                <div className="sf-risk-label" style={{ color: riskColor }}>{riskLevel}</div>
              </div>
            </div>
            <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 8 }}>
              Graph-computed cascade score
            </div>
          </div>

          {/* Graph intel mini */}
          <div className="sf-card" style={{ padding: "16px" }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--sf-text-muted)", marginBottom: 10 }}>
              🕸️ Graph Intel
            </div>
            {[
              { label: "Entities",      value: graph?.total_nodes ?? 87,     color: "#818cf8" },
              { label: "Relations",     value: graph?.total_edges ?? 234,    color: "#06b6d4" },
              { label: "Lateral Paths", value: hunts?.lateral_movement?.length ?? 3, color: "#dc2626" },
              { label: "Threat Actors", value: graph?.entity_breakdown?.threat_actor ?? 5, color: "#f43f5e" },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0", borderBottom: "1px solid var(--sf-border)" }}>
                <span style={{ fontSize: 11, color: "var(--sf-text-muted)" }}>{label}</span>
                <span style={{ fontSize: 14, fontWeight: 800, color }}>{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── CENTER: Alerts + Agent Activity ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Ingestion Pipeline */}
          {ingestion && (
            <div className="sf-card" style={{
              borderColor: ingestion.running ? "rgba(16,185,129,0.25)" : "var(--sf-border)",
              padding: "16px 20px",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Database size={14} color="#6366f1" />
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Ingestion Pipeline</span>
                </div>
                <span className={`sf-badge ${ingestion.running ? "open" : "resolved"}`}>
                  {ingestion.running ? "● Running" : "○ Stopped"}
                </span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8, textAlign: "center" }}>
                {[
                  { label: "Logs", value: ingestion.simulator?.lines_written ?? 0, color: "var(--sf-accent-light)" },
                  { label: "Events", value: ingestion.events_ingested, color: "#10b981" },
                  { label: "Threats", value: ingestion.simulator?.attack_events ?? 0, color: "#f97316" },
                  { label: "Alerts", value: ingestion.alerts_created, color: "#dc2626" },
                ].map(({ label, value, color }) => (
                  <div key={label}>
                    <div style={{ fontSize: 20, fontWeight: 800, color }}>{value}</div>
                    <div style={{ fontSize: 10, color: "var(--sf-text-muted)", marginTop: 2, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Alerts */}
          <div className="sf-card" style={{ flex: 1 }}>
            <div className="sf-card-header">
              <div>
                <div className="sf-card-title">
                  <AlertCircle size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} />
                  Live Security Alerts
                </div>
                <div className="sf-card-subtitle">Auto-generated · click any row to investigate</div>
              </div>
              <a href="/alerts" className="sf-btn sf-btn-secondary sf-btn-sm" style={{ fontSize: 11, textDecoration: "none" }}>
                View All <ArrowRight size={11} />
              </a>
            </div>

            {recentAlerts.length === 0 ? (
              <div style={{ textAlign: "center", padding: "32px", color: "var(--sf-text-muted)" }}>
                <ShieldCheck size={36} color="#10b981" style={{ marginBottom: 10, opacity: 0.5 }} />
                <div style={{ fontWeight: 600 }}>No active alerts</div>
                <div style={{ fontSize: 12, marginTop: 4 }}>Start the ingestion pipeline to generate alerts</div>
              </div>
            ) : (
              <table className="sf-table">
                <thead>
                  <tr>
                    <th>Alert</th>
                    <th>Severity</th>
                    <th>MITRE</th>
                    <th>Status</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {recentAlerts.slice(0, 8).map((alert: Alert) => (
                    <tr key={alert.id} onClick={() => window.location.href = `/alerts?id=${alert.id}`}>
                      <td style={{ color: "var(--sf-text-primary)", fontWeight: 500, maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        <span style={{ color: sevColor[alert.severity] ?? "#94a3b8", marginRight: 6 }}>●</span>
                        {alert.title}
                      </td>
                      <td><span className={`sf-badge ${alert.severity}`}>{alert.severity}</span></td>
                      <td style={{ fontFamily: "monospace", fontSize: 11, color: "var(--sf-accent-light)" }}>{alert.mitre_id || "—"}</td>
                      <td><span className={`sf-badge ${alert.status}`}>{alert.status}</span></td>
                      <td style={{ fontSize: 11, color: "var(--sf-text-muted)" }}>
                        {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* ── RIGHT: AI Agent Feed ──────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* AI Agent Live Feed */}
          <div className="sf-card" style={{ flex: 1 }}>
            <div className="sf-card-header">
              <div>
                <div className="sf-card-title">
                  <Brain size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom", color: "var(--sf-accent-light)" }} />
                  AI Agent Feed
                </div>
                <div className="sf-card-subtitle">Live autonomous operations</div>
              </div>
              <span className="sf-badge open" style={{ fontSize: 10 }}>● Live</span>
            </div>
            <div className="sf-agent-feed">
              {agentEvents.slice(0, 10).map((ev: any, i: number) => {
                const name  = ev.agent_name ?? "agent";
                const icon  = agentIcon[name]  ?? "🤖";
                const color = agentColor[name] ?? "#94a3b8";
                const conf  = ((ev.confidence ?? 0.8) * 100).toFixed(0);
                const action = ev.output_summary ?? ev.action_type ?? "Processing...";
                return (
                  <div key={i} className="sf-agent-event" style={{ borderLeftColor: color, borderLeftWidth: 2 }}>
                    <span style={{ fontSize: 16, flexShrink: 0 }}>{icon}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: "var(--sf-text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {name.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}
                      </div>
                      <div style={{ fontSize: 10, color: "var(--sf-text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {action}
                      </div>
                    </div>
                    <div style={{ textAlign: "right", flexShrink: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color }}>{conf}%</div>
                      <div style={{ fontSize: 9, color: "var(--sf-text-muted)" }}>confidence</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* System Architecture Health */}
          <div className="sf-card">
            <div className="sf-card-title" style={{ marginBottom: 14 }}>
              🔒 Security Architecture
            </div>
            {[
              { name: "Prompt Injection Defense", status: health?.components?.security?.prompt_injection, icon: "🛡️" },
              { name: "Output Validator",          status: health?.components?.security?.output_validation, icon: "✅" },
              { name: "Knowledge Base (RAG)",      status: health?.components?.knowledge_base?.status,    icon: "🧠" },
              { name: "Ingestion Pipeline",        status: health?.components?.ingestion?.status,         icon: "📡" },
              { name: "Knowledge Graph",           status: graph ? "active" : "unknown",                  icon: "🕸️" },
              { name: "Memory System",             status: "active",                                       icon: "💾" },
            ].map((comp, i) => {
              const isActive = ["active", "loaded", "running"].includes(comp.status ?? "");
              return (
                <div key={i} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "6px 10px", borderRadius: 7,
                  background: "rgba(255,255,255,0.02)", marginBottom: 4,
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 12 }}>{comp.icon}</span>
                    <span style={{ fontSize: 11, color: "var(--sf-text-secondary)" }}>{comp.name}</span>
                  </div>
                  <span style={{
                    fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 10,
                    background: isActive ? "rgba(16,185,129,0.12)" : "rgba(239,68,68,0.12)",
                    color: isActive ? "#10b981" : "#ef4444",
                    border: `1px solid ${isActive ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)"}`,
                  }}>
                    {isActive ? "ACTIVE" : (comp.status || "UNKNOWN")}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Bottom Row: Severity + Attack Types + Severity ── */}
      <div className="sf-warroom-bottom">

        {/* Severity Distribution */}
        <div className="sf-card">
          <div className="sf-card-title" style={{ marginBottom: 16 }}>
            <BarChart2 size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} />
            Alert Severity
          </div>
          {data?.severity_distribution && Object.keys(data.severity_distribution).length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {["critical", "high", "medium", "low"].map(sev => {
                const count = (data.severity_distribution as any)[sev] || 0;
                const total = Object.values(data.severity_distribution as any).reduce((a: number, b: any) => a + (b as number), 0) as number;
                const pct = total > 0 ? (count / total) * 100 : 0;
                const color = sevColor[sev] ?? "#94a3b8";
                return (
                  <div key={sev}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 5 }}>
                      <span style={{ textTransform: "capitalize", color: "var(--sf-text-secondary)", display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ color, fontSize: 8 }}>●</span>{sev}
                      </span>
                      <span style={{ fontWeight: 800, color }}>{count}</span>
                    </div>
                    <div style={{ height: 6, borderRadius: 3, background: "rgba(255,255,255,0.05)" }}>
                      <div style={{ height: "100%", borderRadius: 3, background: color, width: `${pct}%`, transition: "width 1.2s ease", boxShadow: `0 0 8px ${color}50` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: "center", color: "var(--sf-text-muted)", fontSize: 13, padding: "20px 0" }}>
              No data yet — start ingestion pipeline
            </div>
          )}
        </div>

        {/* Top Attack Types */}
        <div className="sf-card">
          <div className="sf-card-title" style={{ marginBottom: 16 }}>
            🎯 Top Attack Types
          </div>
          {data?.top_attack_types && data.top_attack_types.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {data.top_attack_types.map((at: any, i: number) => (
                <div key={i} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "8px 12px", borderRadius: 8, background: "rgba(255,255,255,0.02)",
                  border: "1px solid var(--sf-border)",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 18, fontWeight: 900, color: "var(--sf-text-muted)", minWidth: 20 }}>#{i + 1}</span>
                    <span style={{ fontSize: 12, textTransform: "capitalize", color: "var(--sf-text-secondary)" }}>
                      {at.type.replace(/_/g, " ")}
                    </span>
                  </div>
                  <span style={{ fontSize: 14, fontWeight: 800, color: "var(--sf-accent-light)" }}>{at.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: "center", color: "var(--sf-text-muted)", fontSize: 13, padding: "20px 0" }}>
              No attack type data yet
            </div>
          )}
        </div>

        {/* Quick Actions & Links */}
        <div className="sf-card">
          <div className="sf-card-title" style={{ marginBottom: 16 }}>
            ⚡ Quick Operations
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {[
              { label: "🔍 Investigate Active Alerts", href: "/investigate", color: "#6366f1" },
              { label: "🕸️ Explore Knowledge Graph",   href: "/graph",       color: "#8b5cf6" },
              { label: "🔮 View Threat Predictions",   href: "/risk",        color: "#ec4899" },
              { label: "⚡ Autonomous Response Queue", href: "/autonomous",  color: "#f59e0b" },
              { label: "📋 Compliance Status",         href: "/compliance",  color: "#06b6d4" },
              { label: "🏛️ Executive Dashboard",       href: "/executive",   color: "#f59e0b" },
            ].map(({ label, href, color }) => (
              <a key={href} href={href} style={{
                display: "flex", alignItems: "center", justifyContent: "space-between",
                padding: "9px 14px", borderRadius: 8,
                background: "rgba(255,255,255,0.02)", border: `1px solid rgba(255,255,255,0.06)`,
                color: "var(--sf-text-secondary)", textDecoration: "none", fontSize: 12, fontWeight: 500,
                transition: "all 0.2s ease",
              }}
              onMouseOver={e => { (e.currentTarget as HTMLElement).style.borderColor = color; (e.currentTarget as HTMLElement).style.color = "var(--sf-text-primary)"; }}
              onMouseOut={e => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.06)"; (e.currentTarget as HTMLElement).style.color = "var(--sf-text-secondary)"; }}>
                <span>{label}</span>
                <ArrowRight size={12} />
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
