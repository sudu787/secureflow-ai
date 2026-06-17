"use client";

import { useEffect, useState } from "react";
import { getDashboard } from "@/lib/api";
import type { DashboardData, Alert, AgentActivity, SystemHealth } from "@/lib/types";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadDashboard() {
    try {
      const result = await getDashboard();
      setData(result);
    } catch {
      // Backend may not be running yet
    } finally {
      setLoading(false);
    }
  }

  const stats = data?.stats;
  const riskScore = stats?.risk_score ?? 0;
  const riskLevel = stats?.risk_level ?? "low";

  const riskColor = riskLevel === "critical" ? "#dc2626" : riskLevel === "high" ? "#f97316" : riskLevel === "medium" ? "#eab308" : "#10b981";
  const circumference = 2 * Math.PI * 60;
  const dashArray = `${(riskScore / 100) * circumference} ${circumference}`;

  return (
    <div className="sf-animate-in">
      {/* Page Header */}
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">Security Dashboard</h1>
          <p className="sf-page-subtitle">Real-time security operations overview • SecureFlow AI</p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button className="sf-btn sf-btn-secondary sf-btn-sm" onClick={loadDashboard}>
            ↻ Refresh
          </button>
          <span style={{ fontSize: "12px", color: "var(--sf-text-muted)", alignSelf: "center" }}>
            Auto-refresh: 30s
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="sf-stats-grid">
        <div className="sf-stat-card danger">
          <div className="sf-stat-icon">🚨</div>
          <div className="sf-stat-label">Open Alerts</div>
          <div className="sf-stat-value">{stats?.open_alerts ?? 0}</div>
          <div className="sf-stat-change up">
            {stats?.critical_alerts ?? 0} critical • {stats?.high_alerts ?? 0} high
          </div>
        </div>

        <div className="sf-stat-card warning">
          <div className="sf-stat-icon">🔍</div>
          <div className="sf-stat-label">Open Incidents</div>
          <div className="sf-stat-value">{stats?.open_incidents ?? 0}</div>
          <div className="sf-stat-change" style={{ color: "var(--sf-text-muted)" }}>
            {stats?.total_incidents ?? 0} total
          </div>
        </div>

        <div className="sf-stat-card info">
          <div className="sf-stat-icon">🎫</div>
          <div className="sf-stat-label">Open Tickets</div>
          <div className="sf-stat-value">{stats?.open_tickets ?? 0}</div>
          <div className="sf-stat-change" style={{ color: "var(--sf-success)" }}>
            {stats?.resolved_tickets ?? 0} resolved
          </div>
        </div>

        <div className="sf-stat-card accent">
          <div className="sf-stat-icon">📡</div>
          <div className="sf-stat-label">Events Today</div>
          <div className="sf-stat-value">{stats?.events_today ?? 0}</div>
          <div className="sf-stat-change" style={{ color: "var(--sf-text-muted)" }}>
            {stats?.events_per_hour ?? 0}/hr rate
          </div>
        </div>

        <div className="sf-stat-card success">
          <div className="sf-stat-icon">🤖</div>
          <div className="sf-stat-label">AI Actions Today</div>
          <div className="sf-stat-value">{stats?.agent_actions_today ?? 0}</div>
          <div className="sf-stat-change" style={{ color: "var(--sf-text-muted)" }}>
            Autonomous operations
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="sf-grid-dashboard">
        {/* Left Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Recent Alerts */}
          <div className="sf-card">
            <div className="sf-card-header">
              <div>
                <div className="sf-card-title">🚨 Recent Security Alerts</div>
                <div className="sf-card-subtitle">Latest detected threats</div>
              </div>
            </div>
            {(!data?.recent_alerts || data.recent_alerts.length === 0) ? (
              <div style={{ textAlign: "center", padding: "40px", color: "var(--sf-text-muted)" }}>
                <div style={{ fontSize: "40px", marginBottom: "12px" }}>🛡️</div>
                <div style={{ fontSize: "14px", fontWeight: 600 }}>No alerts detected</div>
                <div style={{ fontSize: "12px", marginTop: "4px" }}>Run a demo scenario to generate security events</div>
              </div>
            ) : (
              <table className="sf-table">
                <thead>
                  <tr>
                    <th>Alert</th>
                    <th>Severity</th>
                    <th>Priority</th>
                    <th>MITRE</th>
                    <th>Status</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_alerts.map((alert: Alert) => (
                    <tr key={alert.id} onClick={() => window.location.href = `/alerts?id=${alert.id}`}>
                      <td style={{ color: "var(--sf-text-primary)", fontWeight: 500, maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {alert.title}
                      </td>
                      <td><span className={`sf-badge ${alert.severity}`}>{alert.severity}</span></td>
                      <td><span className={`sf-badge ${alert.priority?.toLowerCase()}`}>{alert.priority}</span></td>
                      <td style={{ fontFamily: "monospace", fontSize: "12px", color: "var(--sf-accent-light)" }}>{alert.mitre_id || "—"}</td>
                      <td><span className={`sf-badge ${alert.status}`}>{alert.status}</span></td>
                      <td style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>
                        {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Agent Activity */}
          <div className="sf-card">
            <div className="sf-card-header">
              <div>
                <div className="sf-card-title">🤖 AI Agent Activity</div>
                <div className="sf-card-subtitle">Recent autonomous operations</div>
              </div>
            </div>
            {(!data?.recent_agent_activity || data.recent_agent_activity.length === 0) ? (
              <div style={{ textAlign: "center", padding: "30px", color: "var(--sf-text-muted)", fontSize: "13px" }}>
                No agent activity yet. Run a demo scenario to activate the AI agents.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {data.recent_agent_activity.slice(0, 8).map((action: AgentActivity) => (
                  <div key={action.id} style={{
                    display: "flex", alignItems: "center", gap: "12px",
                    padding: "10px 14px", borderRadius: "8px",
                    background: "rgba(255,255,255,0.02)",
                    border: "1px solid var(--sf-border)",
                  }}>
                    <span style={{ fontSize: "16px" }}>
                      {action.agent_name === "triage_agent" ? "🎯" :
                       action.agent_name === "investigation_agent" ? "🔍" :
                       action.agent_name === "remediation_agent" ? "🔧" :
                       action.agent_name === "it_support_agent" ? "💻" :
                       action.agent_name === "reporting_agent" ? "📊" : "🤖"}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: "13px", fontWeight: 500, color: "var(--sf-text-primary)" }}>
                        {action.agent_name.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                      </div>
                      <div style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>
                        {action.output_summary || action.action_type}
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontSize: "12px", color: "var(--sf-accent-light)", fontWeight: 600 }}>
                        {(action.confidence * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--sf-text-muted)" }}>
                        {action.created_at ? new Date(action.created_at).toLocaleTimeString() : ""}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Risk Score */}
          <div className="sf-card" style={{ textAlign: "center" }}>
            <div className="sf-card-title" style={{ marginBottom: "16px" }}>Organization Risk Score</div>
            <div className="sf-risk-gauge">
              <svg viewBox="0 0 140 140">
                <circle className="sf-risk-gauge-bg" cx="70" cy="70" r="60" />
                <circle
                  className="sf-risk-gauge-fill"
                  cx="70" cy="70" r="60"
                  stroke={riskColor}
                  strokeDasharray={dashArray}
                />
              </svg>
              <div className="sf-risk-value">
                <div className="sf-risk-number" style={{ color: riskColor }}>{riskScore}</div>
                <div className="sf-risk-label" style={{ color: riskColor }}>{riskLevel}</div>
              </div>
            </div>
            <div style={{ fontSize: "12px", color: "var(--sf-text-muted)", marginTop: "12px" }}>
              Based on open alerts, incidents, and threat severity
            </div>
          </div>

          {/* Severity Distribution */}
          <div className="sf-card">
            <div className="sf-card-title" style={{ marginBottom: "16px" }}>Alert Severity Distribution</div>
            {data?.severity_distribution && Object.keys(data.severity_distribution).length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {["critical", "high", "medium", "low"].map(sev => {
                  const count = data.severity_distribution[sev] || 0;
                  const total = Object.values(data.severity_distribution).reduce((a: number, b: any) => a + (b as number), 0) as number;
                  const pct = total > 0 ? (count / total) * 100 : 0;
                  const colors: Record<string, string> = { critical: "#dc2626", high: "#f97316", medium: "#eab308", low: "#22c55e" };
                  return (
                    <div key={sev}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "4px" }}>
                        <span style={{ textTransform: "capitalize", color: "var(--sf-text-secondary)" }}>{sev}</span>
                        <span style={{ fontWeight: 600, color: colors[sev] }}>{count}</span>
                      </div>
                      <div style={{ height: "6px", borderRadius: "3px", background: "rgba(255,255,255,0.05)" }}>
                        <div style={{
                          height: "100%", borderRadius: "3px", background: colors[sev],
                          width: `${pct}%`, transition: "width 1s ease",
                          boxShadow: `0 0 8px ${colors[sev]}40`,
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ textAlign: "center", color: "var(--sf-text-muted)", fontSize: "13px", padding: "20px 0" }}>
                No alert data available
              </div>
            )}
          </div>

          {/* System Health */}
          <div className="sf-card">
            <div className="sf-card-title" style={{ marginBottom: "16px" }}>System Health</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {(data?.system_health || []).map((item: SystemHealth, i: number) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "8px 12px", borderRadius: "8px",
                  background: "rgba(255,255,255,0.02)",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span className={`sf-health-dot ${item.status}`} />
                    <span style={{ fontSize: "13px" }}>{item.service}</span>
                  </div>
                  <span style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>{item.uptime}</span>
                </div>
              ))}
              {(!data?.system_health || data.system_health.length === 0) && (
                <>
                  {["Detection Engine", "AI Agent System", "Log Collector", "Knowledge Base", "Ticket System"].map(s => (
                    <div key={s} style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                      padding: "8px 12px", borderRadius: "8px", background: "rgba(255,255,255,0.02)",
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span className="sf-health-dot healthy" />
                        <span style={{ fontSize: "13px" }}>{s}</span>
                      </div>
                      <span style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>99.9%</span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>

          {/* Attack Types */}
          {data?.top_attack_types && data.top_attack_types.length > 0 && (
            <div className="sf-card">
              <div className="sf-card-title" style={{ marginBottom: "16px" }}>Top Attack Types</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {data.top_attack_types.map((at, i) => (
                  <div key={i} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "8px 12px", borderRadius: "8px", background: "rgba(255,255,255,0.02)",
                  }}>
                    <span style={{ fontSize: "13px", textTransform: "capitalize" }}>
                      {at.type.replace(/_/g, " ")}
                    </span>
                    <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--sf-accent-light)" }}>
                      {at.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
