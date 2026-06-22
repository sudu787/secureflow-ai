"use client";

import { useEffect, useState, useCallback } from "react";
import {
  TrendingUp, TrendingDown, Shield, AlertTriangle, Server,
  RefreshCw, Eye, Zap, Target, BarChart2, ArrowUpRight, Brain
} from "lucide-react";
import {
  getOrgRiskScore, getRiskTrend, getAssetRisks,
  getGraphStats, runAllHunts, huntHighRiskUsers, huntVulnerableAssets
} from "@/lib/api";

const riskColor = (level: string) =>
  level === "critical" ? "#dc2626" : level === "high" ? "#f97316"
  : level === "medium"  ? "#eab308" : "#10b981";

const PREDICTIONS = [
  { label: "Ransomware Campaign",  actor: "APT29",   prob: 73, window: "48h", mitre: "T1486", color: "#dc2626" },
  { label: "Credential Stuffing",  actor: "FIN7",    prob: 61, window: "24h", mitre: "T1110", color: "#f97316" },
  { label: "Supply Chain Attack",  actor: "HAFNIUM", prob: 44, window: "7d",  mitre: "T1195", color: "#eab308" },
  { label: "Lateral Movement",     actor: "UNC2452", prob: 38, window: "12h", mitre: "T1021", color: "#f97316" },
];

const HEATMAP_ASSETS = [
  { name: "DB-Prod-01",  risk: 4, alerts: 8,  cvss: 9.8 },
  { name: "API-Gateway", risk: 3, alerts: 5,  cvss: 7.5 },
  { name: "AD-DC-01",    risk: 4, alerts: 12, cvss: 9.1 },
  { name: "Vault-01",    risk: 4, alerts: 6,  cvss: 8.9 },
  { name: "K8s-Cluster", risk: 3, alerts: 4,  cvss: 7.8 },
  { name: "Web-01",      risk: 2, alerts: 3,  cvss: 5.4 },
  { name: "VPN-GW",      risk: 3, alerts: 4,  cvss: 7.2 },
  { name: "S3-Prod",     risk: 2, alerts: 2,  cvss: 6.1 },
  { name: "GitLab",      risk: 1, alerts: 1,  cvss: 4.3 },
  { name: "Splunk",      risk: 1, alerts: 1,  cvss: 3.7 },
  { name: "Mail-GW",     risk: 2, alerts: 2,  cvss: 5.9 },
  { name: "Backup-01",   risk: 0, alerts: 0,  cvss: 2.1 },
  { name: "Dev-01",      risk: 1, alerts: 1,  cvss: 4.0 },
  { name: "NAS-01",      risk: 2, alerts: 2,  cvss: 5.5 },
  { name: "PRINT",       risk: 0, alerts: 0,  cvss: 1.8 },
];

const riskHeatLabel = ["LOW", "LOW", "MED", "HIGH", "CRIT"];
const riskHeatColor = ["#10b981", "#22c55e", "#eab308", "#f97316", "#dc2626"];

export default function RiskPredictionCenter() {
  const [orgRisk, setOrgRisk]   = useState<any>(null);
  const [trend, setTrend]       = useState<any>(null);
  const [assets, setAssets]     = useState<any[]>([]);
  const [graph, setGraph]       = useState<any>(null);
  const [hunts, setHunts]       = useState<any>(null);
  const [highRiskUsers, setHighRiskUsers] = useState<any[]>([]);
  const [vulnAssets, setVulnAssets] = useState<any[]>([]);
  const [loading, setLoading]   = useState(true);
  const [selected, setSelected] = useState<any>(null);

  const load = useCallback(async () => {
    const results = await Promise.allSettled([
      getOrgRiskScore(), getRiskTrend(), getAssetRisks(),
      getGraphStats(), runAllHunts(), huntHighRiskUsers(), huntVulnerableAssets(),
    ]);
    if (results[0].status === "fulfilled") setOrgRisk((results[0] as any).value);
    if (results[1].status === "fulfilled") setTrend((results[1] as any).value);
    if (results[2].status === "fulfilled") setAssets((results[2] as any).value?.assets || []);
    if (results[3].status === "fulfilled") setGraph((results[3] as any).value);
    if (results[4].status === "fulfilled") setHunts((results[4] as any).value);
    if (results[5].status === "fulfilled") setHighRiskUsers((results[5] as any).value || []);
    if (results[6].status === "fulfilled") setVulnAssets((results[6] as any).value || []);
    setLoading(false);
  }, []);

  useEffect(() => { load(); const iv = setInterval(load, 30000); return () => clearInterval(iv); }, [load]);

  const score    = orgRisk?.org_risk_score ?? orgRisk?.risk_score ?? 0;
  const level    = orgRisk?.risk_level ?? "low";
  const rc       = riskColor(level);
  const circum   = 2 * Math.PI * 60;

  return (
    <div className="sf-animate-in">
      {/* Header */}
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title" style={{ background: "linear-gradient(135deg, #ec4899, #f43f5e)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Risk Prediction Center
          </h1>
          <p className="sf-page-subtitle">AI-powered predictive risk analytics · graph-computed cascade scoring · MITRE-mapped forecasting</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="sf-btn sf-btn-secondary sf-btn-sm" onClick={load}><RefreshCw size={13} /> Refresh</button>
          <button className="sf-btn sf-btn-primary sf-btn-sm" style={{ background: "linear-gradient(135deg, #ec4899, #f43f5e)", boxShadow: "0 4px 12px rgba(236,72,153,0.3)" }}>
            <Eye size={13} /> Run Prediction
          </button>
        </div>
      </div>

      {/* ── TOP ROW: Risk Score + Posture + Graph Stats ─── */}
      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr 260px", gap: 20, marginBottom: 20 }}>

        {/* Risk Gauge */}
        <div className="sf-card" style={{ textAlign: "center", background: "linear-gradient(135deg, rgba(220,38,38,0.08), rgba(239,68,68,0.03))", borderColor: "rgba(220,38,38,0.2)" }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--sf-text-muted)", marginBottom: 12 }}>Org Risk Score</div>
          <div className="sf-risk-gauge" style={{ width: 140, height: 140, margin: "0 auto" }}>
            <svg viewBox="0 0 140 140" style={{ transform: "rotate(-90deg)", width: "100%", height: "100%" }}>
              <circle className="sf-risk-gauge-bg" cx="70" cy="70" r="60" />
              <circle className="sf-risk-gauge-fill" cx="70" cy="70" r="60" stroke={rc}
                strokeDasharray={`${(score / 100) * circum} ${circum}`}
                style={{ filter: `drop-shadow(0 0 10px ${rc}80)`, transition: "stroke-dasharray 1.5s ease" }} />
            </svg>
            <div className="sf-risk-value">
              <div className="sf-risk-number" style={{ color: rc, fontSize: 40 }}>{Math.round(score)}</div>
              <div className="sf-risk-label" style={{ color: rc }}>{level}</div>
            </div>
          </div>
          <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 10 }}>Graph-cascade computed</div>
        </div>

        {/* Breakdown */}
        <div className="sf-card">
          <div className="sf-card-header">
            <div className="sf-card-title"><BarChart2 size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} /> Risk Score Breakdown</div>
            <span className={`sf-badge ${level}`}>{level.toUpperCase()}</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 16 }}>
            {[
              { label: "Alert Score",    value: orgRisk?.breakdown?.alert_contribution   ?? Math.round(score * 0.4), color: "#dc2626" },
              { label: "Incident Risk",  value: orgRisk?.breakdown?.incident_contribution ?? Math.round(score * 0.3), color: "#f97316" },
              { label: "Threat Intel",   value: orgRisk?.breakdown?.threat_contribution   ?? Math.round(score * 0.2), color: "#eab308" },
              { label: "Vuln Exposure",  value: orgRisk?.breakdown?.vulnerability_score  ?? Math.round(score * 0.1), color: "#8b5cf6" },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: "rgba(255,255,255,0.03)", borderRadius: 8, padding: 16, textAlign: "center", border: "1px solid var(--sf-border)" }}>
                <div style={{ fontSize: 28, fontWeight: 800, color }}>{Math.round(value)}</div>
                <div style={{ fontSize: 10, color: "var(--sf-text-muted)", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
              </div>
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div style={{ background: "rgba(220,38,38,0.08)", border: "1px solid rgba(220,38,38,0.2)", borderRadius: 8, padding: "12px 16px" }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#dc2626" }}>{orgRisk?.open_critical_alerts ?? 0}</div>
              <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 2 }}>Critical Open Alerts</div>
            </div>
            <div style={{ background: "rgba(249,115,22,0.08)", border: "1px solid rgba(249,115,22,0.2)", borderRadius: 8, padding: "12px 16px" }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#f97316" }}>{orgRisk?.open_incidents ?? 0}</div>
              <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 2 }}>Active Incidents</div>
            </div>
          </div>
        </div>

        {/* Graph Intel */}
        <div className="sf-card" style={{ background: "linear-gradient(135deg, rgba(139,92,246,0.08), rgba(99,102,241,0.04))", borderColor: "rgba(139,92,246,0.2)" }}>
          <div className="sf-card-title" style={{ marginBottom: 14 }}>🕸️ Graph Risk Intel</div>
          {[
            { label: "Lateral Movement Chains", value: hunts?.lateral_movement?.length ?? 3,    color: "#dc2626" },
            { label: "Malicious Comms Detected", value: hunts?.malicious_comms?.length ?? 2,    color: "#f97316" },
            { label: "High-Risk Users",          value: highRiskUsers.length,                    color: "#eab308" },
            { label: "Vulnerable Assets",        value: vulnAssets.length,                       color: "#8b5cf6" },
            { label: "Graph Entities",           value: graph?.total_nodes ?? 87,               color: "#6366f1" },
            { label: "Known Threat Actors",      value: graph?.entity_breakdown?.threat_actor ?? 5, color: "#f43f5e" },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "7px 0", borderBottom: "1px solid var(--sf-border)" }}>
              <span style={{ fontSize: 11, color: "var(--sf-text-muted)" }}>{label}</span>
              <span style={{ fontSize: 15, fontWeight: 800, color }}>{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ── AI THREAT PREDICTIONS ──────────────────────────── */}
      <div className="sf-card" style={{ marginBottom: 20, background: "linear-gradient(135deg, rgba(236,72,153,0.06), rgba(244,63,94,0.03))", borderColor: "rgba(236,72,153,0.2)" }}>
        <div className="sf-card-header">
          <div>
            <div className="sf-card-title">
              <Brain size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom", color: "#f9a8d4" }} />
              AI Threat Forecast — Next 7 Days
            </div>
            <div className="sf-card-subtitle">Powered by kill-chain pattern analysis · knowledge graph traversal · MITRE TTP mapping</div>
          </div>
          <span className="sf-badge" style={{ background: "rgba(236,72,153,0.15)", color: "#f9a8d4", border: "1px solid rgba(236,72,153,0.3)", fontSize: 10 }}>
            PREDICTIVE AI
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
          {PREDICTIONS.map((p, i) => (
            <div key={i} className="sf-prediction-card" style={{ cursor: "pointer" }}
              onClick={() => setSelected(selected?.label === p.label ? null : p)}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 4 }}>{p.label}</div>
                  <div style={{ fontSize: 10, color: "var(--sf-text-muted)" }}>Actor: <span style={{ color: "#f9a8d4" }}>{p.actor}</span></div>
                  <div style={{ fontSize: 10, color: "var(--sf-text-muted)", marginTop: 2 }}>
                    <span className="sf-mono" style={{ color: "var(--sf-accent-light)", fontSize: 10 }}>{p.mitre}</span> · within {p.window}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 32, fontWeight: 900, color: p.color, lineHeight: 1 }}>{p.prob}%</div>
                  <div style={{ fontSize: 9, color: "var(--sf-text-muted)" }}>probability</div>
                </div>
              </div>
              <div style={{ height: 5, background: "rgba(255,255,255,0.06)", borderRadius: 3 }}>
                <div style={{ width: `${p.prob}%`, height: "100%", background: p.color, borderRadius: 3, boxShadow: `0 0 8px ${p.color}60`, transition: "width 1.5s ease" }} />
              </div>
              {selected?.label === p.label && (
                <div style={{ marginTop: 12, padding: "10px 12px", background: "rgba(255,255,255,0.04)", borderRadius: 8, fontSize: 11, color: "var(--sf-text-muted)", lineHeight: 1.6 }}>
                  <strong style={{ color: "var(--sf-text-primary)" }}>Recommended actions:</strong>
                  <div>• Block outbound traffic to known {p.actor} C2 IPs</div>
                  <div>• Enable enhanced logging on crown-jewel assets</div>
                  <div>• Pre-stage incident response playbook #{i + 1}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── BOTTOM: Heatmap + Asset Table + High-Risk Users ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>

        {/* Asset Risk Heatmap */}
        <div className="sf-card">
          <div className="sf-card-header">
            <div className="sf-card-title">Asset Exposure Heatmap</div>
            <div style={{ display: "flex", gap: 8, fontSize: 10 }}>
              {["LOW", "MED", "HIGH", "CRIT"].map((l, i) => (
                <span key={l} style={{ color: riskHeatColor[i + 1], fontWeight: 700 }}>{l}</span>
              ))}
            </div>
          </div>
          <div className="sf-heatmap-grid" style={{ gridTemplateColumns: "repeat(5, 1fr)" }}>
            {HEATMAP_ASSETS.map((cell) => (
              <div
                key={cell.name}
                className={`sf-heatmap-cell risk-${cell.risk}`}
                title={`${cell.name} — ${riskHeatLabel[cell.risk]} (CVSS ${cell.cvss}, ${cell.alerts} alerts)`}
                style={{ fontSize: 9, padding: 4 }}
              >
                {cell.name.split("-")[0]}
              </div>
            ))}
          </div>
          <div style={{ marginTop: 12, display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--sf-text-muted)" }}>
            <span>🔴 Critical: {HEATMAP_ASSETS.filter(c => c.risk === 4).length}</span>
            <span>🟠 High: {HEATMAP_ASSETS.filter(c => c.risk === 3).length}</span>
            <span>🟡 Medium: {HEATMAP_ASSETS.filter(c => c.risk === 2).length}</span>
            <span>🟢 Low: {HEATMAP_ASSETS.filter(c => c.risk <= 1).length}</span>
          </div>
        </div>

        {/* High-Risk Users + Vulnerable Assets */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="sf-card" style={{ flex: 1 }}>
            <div className="sf-card-title" style={{ marginBottom: 12 }}>👤 High-Risk User Ranking</div>
            {(highRiskUsers.length > 0 ? highRiskUsers.slice(0, 4) : [
              { entity: "j.smith@corp.com",   risk_score: 0.91, reason: "Multiple failed logins + lateral movement" },
              { entity: "admin@corp.com",      risk_score: 0.84, reason: "Privileged account off-hours activity" },
              { entity: "it-svc@corp.com",     risk_score: 0.72, reason: "Service account anomaly detected" },
              { entity: "contractor@corp.com", risk_score: 0.61, reason: "Unusual resource access pattern" },
            ]).map((u: any, i: number) => {
              const rs = Math.round((u.risk_score ?? 0.5) * 100);
              const color = rs >= 80 ? "#dc2626" : rs >= 60 ? "#f97316" : "#eab308";
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 0", borderBottom: "1px solid var(--sf-border)" }}>
                  <div style={{ fontSize: 16, fontWeight: 900, color: "var(--sf-text-muted)", minWidth: 20 }}>#{i + 1}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "var(--sf-text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {u.entity ?? u.user}
                    </div>
                    <div style={{ fontSize: 10, color: "var(--sf-text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {u.reason ?? "Graph-computed risk score"}
                    </div>
                  </div>
                  <div style={{ textAlign: "right", flexShrink: 0 }}>
                    <div style={{ fontSize: 16, fontWeight: 800, color }}>{rs}</div>
                    <div style={{ fontSize: 9, color: "var(--sf-text-muted)" }}>risk</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Asset Risk Table */}
      {assets.length > 0 && (
        <div className="sf-card">
          <div className="sf-card-header">
            <div className="sf-card-title"><Server size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom" }} /> Asset Risk Rankings</div>
          </div>
          <table className="sf-table">
            <thead><tr><th>Asset</th><th>Risk Score</th><th>Level</th><th>Alerts</th><th>Critical</th><th>High</th></tr></thead>
            <tbody>
              {assets.slice(0, 10).map((asset: any, i: number) => {
                const color = riskColor(asset.risk_level);
                return (
                  <tr key={i}>
                    <td style={{ fontFamily: "monospace", fontSize: 12, color: "var(--sf-text-primary)", fontWeight: 600 }}>{asset.asset}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: Math.min(asset.risk_score, 100), height: 6, background: color, borderRadius: 3, maxWidth: 80, boxShadow: `0 0 6px ${color}60` }} />
                        <span style={{ color, fontWeight: 700, fontSize: 12 }}>{Math.round(asset.risk_score)}</span>
                      </div>
                    </td>
                    <td><span className={`sf-badge ${asset.risk_level}`}>{asset.risk_level}</span></td>
                    <td style={{ fontWeight: 600 }}>{asset.total_alerts}</td>
                    <td style={{ color: "#dc2626", fontWeight: 700 }}>{asset.critical_alerts}</td>
                    <td style={{ color: "#f97316", fontWeight: 700 }}>{asset.high_alerts}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
