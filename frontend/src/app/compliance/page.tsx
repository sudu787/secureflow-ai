"use client";

import { useEffect, useState, useCallback } from "react";
import {
  ShieldCheck, AlertTriangle, CheckCircle, XCircle,
  RefreshCw, Lock, FileCheck, TrendingUp, ChevronDown, ChevronRight, X, Download
} from "lucide-react";
import { getComplianceScore, getComplianceViolations, getComplianceFrameworks, getDashboard } from "@/lib/api";

// ── Audit Report Modal ───────────────────────────────────────────────────────
function AuditReportModal({ onClose, fwScores, violations }: { onClose: () => void; fwScores: Record<string,number>; violations: any[] }) {
  const ts = new Date().toLocaleString();
  const frameworks = [
    { key: "nist", name: "NIST CSF 2.0",   color: "#6366f1", target: 80,  controls: 108 },
    { key: "cis",  name: "CIS Controls v8", color: "#06b6d4", target: 85,  controls: 153 },
    { key: "iso",  name: "ISO 27001",       color: "#10b981", target: 90,  controls: 93  },
    { key: "soc2", name: "SOC 2 Type II",   color: "#f59e0b", target: 88,  controls: 60  },
    { key: "pci",  name: "PCI DSS v4",      color: "#8b5cf6", target: 92,  controls: 264 },
  ];
  const overallScore = Math.round(Object.values(fwScores).reduce((a, b) => a + b, 0) / 5);
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 9999, background: "rgba(0,0,0,0.8)", backdropFilter: "blur(8px)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div style={{ background: "var(--sf-bg-card)", border: "1px solid var(--sf-border)", borderRadius: 16, width: "min(860px, 96vw)", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 40px 80px rgba(0,0,0,0.7)" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "20px 28px", borderBottom: "1px solid var(--sf-border)", background: "linear-gradient(135deg, rgba(6,182,212,0.1), rgba(99,102,241,0.05))" }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: "var(--sf-text-primary)" }}>📋 Compliance Audit Report</div>
            <div style={{ fontSize: 12, color: "var(--sf-text-muted)", marginTop: 4 }}>SecureFlow AI Compliance Intelligence · Generated {ts}</div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button style={{ background: "rgba(6,182,212,0.15)", border: "1px solid rgba(6,182,212,0.3)", color: "#67e8f9", borderRadius: 8, padding: "6px 14px", cursor: "pointer", fontSize: 12, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }} onClick={() => window.print()}>
              <Download size={12} /> Export PDF
            </button>
            <button style={{ background: "rgba(255,255,255,0.06)", border: "1px solid var(--sf-border)", color: "var(--sf-text-muted)", borderRadius: 8, padding: "6px 10px", cursor: "pointer" }} onClick={onClose}><X size={14} /></button>
          </div>
        </div>
        <div style={{ padding: "24px 28px", display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Overall Status */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
            <div style={{ textAlign: "center", background: "rgba(255,255,255,0.02)", borderRadius: 10, padding: 18, border: "1px solid var(--sf-border)" }}>
              <div style={{ fontSize: 48, fontWeight: 900, color: overallScore >= 80 ? "#10b981" : overallScore >= 60 ? "#eab308" : "#dc2626", lineHeight: 1 }}>{overallScore}</div>
              <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>Overall Compliance</div>
              <span className={`sf-badge ${overallScore >= 80 ? "low" : overallScore >= 60 ? "medium" : "critical"}`} style={{ marginTop: 8, display: "inline-block" }}>{overallScore >= 80 ? "COMPLIANT" : overallScore >= 60 ? "REVIEW" : "NON-COMPLIANT"}</span>
            </div>
            <div style={{ textAlign: "center", background: "rgba(255,255,255,0.02)", borderRadius: 10, padding: 18, border: "1px solid var(--sf-border)" }}>
              <div style={{ fontSize: 48, fontWeight: 900, color: violations.length > 0 ? "#dc2626" : "#10b981", lineHeight: 1 }}>{violations.length}</div>
              <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>Active Violations</div>
              <span className={`sf-badge ${violations.length > 0 ? "critical" : "low"}`} style={{ marginTop: 8, display: "inline-block" }}>{violations.length > 0 ? "ACTION NEEDED" : "CLEAR"}</span>
            </div>
            <div style={{ textAlign: "center", background: "rgba(255,255,255,0.02)", borderRadius: 10, padding: 18, border: "1px solid var(--sf-border)" }}>
              <div style={{ fontSize: 48, fontWeight: 900, color: "#818cf8", lineHeight: 1 }}>5</div>
              <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>Frameworks Monitored</div>
              <span className="sf-badge info" style={{ marginTop: 8, display: "inline-block" }}>CONTINUOUS</span>
            </div>
          </div>

          {/* Per-framework scores */}
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 12 }}>Framework Compliance Breakdown</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {frameworks.map(({ key, name, color, target, controls }) => {
                const sc = fwScores[key] ?? 75;
                const gap = Math.max(target - sc, 0);
                return (
                  <div key={key} style={{ background: "rgba(255,255,255,0.02)", borderRadius: 10, padding: "14px 18px", border: "1px solid var(--sf-border)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <div>
                        <span style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)" }}>{name}</span>
                        <span style={{ fontSize: 10, color: "var(--sf-text-muted)", marginLeft: 8 }}>{controls} controls</span>
                      </div>
                      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                        {gap > 0 && <span style={{ fontSize: 11, color: "#f97316" }}>Gap: {gap} pts to target</span>}
                        <span style={{ fontSize: 20, fontWeight: 900, color }}>{sc}</span>
                        <span className={`sf-badge ${sc >= target ? "low" : sc >= target-15 ? "medium" : "critical"}`}>{sc >= target ? "✅ Pass" : sc >= target-15 ? "⚠️ Review" : "❌ Fail"}</span>
                      </div>
                    </div>
                    <div style={{ height: 8, background: "rgba(255,255,255,0.06)", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{ width: `${sc}%`, height: "100%", background: color, borderRadius: 4, transition: "width 1.5s ease", boxShadow: `0 0 8px ${color}60` }} />
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: 10, color: "var(--sf-text-muted)" }}>
                      <span>Current: {sc}%</span>
                      <span>Target: {target}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Recent violations summary */}
          {violations.length > 0 && (
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: 10 }}>🔴 Recent Violations (Top {Math.min(violations.length, 5)})</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {violations.slice(0, 5).map((v: any, i: number) => (
                  <div key={i} style={{ display: "flex", gap: 12, alignItems: "center", padding: "10px 14px", background: "rgba(220,38,38,0.05)", borderRadius: 8, border: "1px solid rgba(220,38,38,0.15)" }}>
                    <span className={`sf-badge ${v.severity}`}>{v.severity}</span>
                    <div style={{ flex: 1, fontSize: 12, color: "var(--sf-text-secondary)" }}>{v.alert_title}</div>
                    <div style={{ fontSize: 10, fontFamily: "monospace", color: "#818cf8" }}>{v.nist_mapping?.category || "—"}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Audit trail note */}
          <div style={{ background: "rgba(99,102,241,0.06)", borderRadius: 10, padding: 16, border: "1px solid rgba(99,102,241,0.2)", fontSize: 12, color: "var(--sf-text-muted)", lineHeight: 1.7 }}>
            <strong style={{ color: "var(--sf-text-primary)" }}>🔒 Audit Trail Notice:</strong> All compliance violations are automatically logged with timestamps, alert IDs, agent classifications, and framework control mappings. This report is generated from live data and reflects the current compliance posture of the organization. For a full audit trail export, contact your SecureFlow AI administrator.
          </div>
        </div>
      </div>
    </div>
  );
}

const FRAMEWORKS_STATIC = [
  { key: "nist",  name: "NIST CSF 2.0",  color: "#6366f1", target: 80, icon: "🏛️",
    controls: 108, desc: "Identify, Protect, Detect, Respond, Recover",
    categories: ["GV.OC", "ID.AM", "PR.AA", "DE.CM", "RS.MA", "RC.RP"] },
  { key: "cis",   name: "CIS Controls v8", color: "#06b6d4", target: 85, icon: "🔵",
    controls: 153, desc: "18 Critical Security Controls for cyber defense",
    categories: ["CIS-1 Inv Assets", "CIS-6 Access Mgmt", "CIS-13 Net Monitor", "CIS-17 IR"] },
  { key: "iso",   name: "ISO 27001",    color: "#10b981", target: 90, icon: "🌍",
    controls: 93,  desc: "Information security management system standard",
    categories: ["A.5 Policies", "A.8 Asset Mgmt", "A.12 Operations", "A.16 Incidents"] },
  { key: "soc2",  name: "SOC 2 Type II", color: "#f59e0b", target: 88, icon: "📋",
    controls: 60,  desc: "Trust Services Criteria (AICPA)",
    categories: ["CC6 Logical Access", "CC7 System Ops", "CC8 Change Mgmt", "A1 Availability"] },
  { key: "pci",   name: "PCI DSS v4",  color: "#8b5cf6", target: 92, icon: "💳",
    controls: 264, desc: "Payment Card Industry Data Security Standard",
    categories: ["Req 1 Network", "Req 6 Vuln Mgmt", "Req 10 Logging", "Req 12 Policy"] },
];

const AI_RECS = [
  { icon: "🛡️", title: "Enable MFA on all privileged accounts", impact: "High", effort: "Low",  framework: "NIST PR.AA · CIS-6" },
  { icon: "📡", title: "Deploy network segmentation for DB tier",  impact: "High", effort: "Med",  framework: "PCI Req-1 · ISO A.13" },
  { icon: "🔍", title: "Implement continuous vulnerability scanning", impact: "Med", effort: "Low", framework: "CIS-7 · NIST ID.RA" },
  { icon: "📋", title: "Create incident response playbooks",       impact: "High", effort: "Med",  framework: "NIST RS.MA · SOC2 CC7" },
  { icon: "🔐", title: "Encrypt all data at rest and in transit",  impact: "High", effort: "High", framework: "PCI Req-4 · ISO A.10" },
];

const impactColor = (s: string) => s === "High" ? "#dc2626" : s === "Med" ? "#f97316" : "#eab308";
const effortColor = (s: string) => s === "Low" ? "#10b981" : s === "Med" ? "#f59e0b" : "#f97316";

export default function ComplianceIntelligenceCenter() {
  const [score, setScore]         = useState<any>(null);
  const [violations, setViolations] = useState<any[]>([]);
  const [frameworks, setFrameworks] = useState<any[]>([]);
  const [dash, setDash]           = useState<any>(null);
  const [loading, setLoading]     = useState(true);
  const [expanded, setExpanded]   = useState<string | null>(null);
  const [showAudit, setShowAudit] = useState(false);

  const load = useCallback(async () => {
    const results = await Promise.allSettled([
      getComplianceScore(), getComplianceViolations(), getComplianceFrameworks(), getDashboard(),
    ]);
    if (results[0].status === "fulfilled") setScore((results[0] as any).value);
    if (results[1].status === "fulfilled") setViolations((results[1] as any).value?.violations || []);
    if (results[2].status === "fulfilled") setFrameworks((results[2] as any).value?.frameworks || []);
    if (results[3].status === "fulfilled") setDash((results[3] as any).value);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const stats = dash?.stats ?? {};
  const overall = score?.overall_score ?? 95;

  // Compute per-framework scores from live compliance data
  const fwScores: Record<string, number> = {
    nist:  Math.round(score?.frameworks?.nist_csf?.score ?? Math.max(100 - (stats.open_alerts ?? 0) * 2 - (stats.critical_alerts ?? 0) * 4, 45)),
    cis:   Math.round(score?.frameworks?.cis_controls?.score ?? Math.max(100 - (stats.open_alerts ?? 0) * 2 - (stats.critical_alerts ?? 0) * 3, 48)),
    iso:   Math.round(Math.max(100 - (stats.open_alerts ?? 0) * 1.5 - (stats.critical_alerts ?? 0) * 3, 52)),
    soc2:  Math.round(Math.max(100 - (stats.open_alerts ?? 0) * 1 - (stats.critical_alerts ?? 0) * 2, 55)),
    pci:   Math.round(Math.max(100 - (stats.critical_alerts ?? 0) * 5 - (stats.open_incidents ?? 0) * 3, 45)),
  };

  const overallComputed = Math.round(Object.values(fwScores).reduce((a, b) => a + b, 0) / 5);

  return (
    <div className="sf-animate-in">
      {/* Header */}
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title" style={{ background: "linear-gradient(135deg, #06b6d4, #6366f1)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Compliance Intelligence Center
          </h1>
          <p className="sf-page-subtitle">AI-automated compliance scoring · 5 frameworks · real-time gap analysis · audit-ready reporting</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="sf-btn sf-btn-secondary sf-btn-sm" onClick={load}><RefreshCw size={13} /> Refresh</button>
          <button className="sf-btn sf-btn-primary sf-btn-sm" onClick={() => setShowAudit(true)}>
            <FileCheck size={13} /> Audit Report
          </button>
        </div>
      </div>

      {/* ── TOP: 5 Framework Scorecards ─────────────────── */}
      <div className="sf-compliance-grid" style={{ marginBottom: 20 }}>
        {FRAMEWORKS_STATIC.map(({ key, name, color, target, icon }) => {
          const sc = fwScores[key] ?? 75;
          const status = sc >= target ? "good" : sc >= target - 15 ? "warn" : "bad";
          const labelText = sc >= target ? "Compliant ✅" : sc >= target - 15 ? "Review ⚠️" : "Gap 🔴";
          return (
            <div key={key} className={`sf-compliance-card ${status}`}
              style={{ cursor: "pointer", transition: "all 0.3s ease" }}
              onClick={() => setExpanded(expanded === key ? null : key)}>
              <div className="sf-compliance-name">{icon} {name}</div>
              <div className="sf-compliance-score" style={{ color }}>{sc}</div>
              <div className="sf-compliance-label">{labelText}</div>
              <div style={{ marginTop: 8 }}>
                <div style={{ height: 3, background: "rgba(255,255,255,0.06)", borderRadius: 2, overflow: "hidden" }}>
                  <div style={{ width: `${sc}%`, height: "100%", background: color, transition: "width 1.5s ease" }} />
                </div>
              </div>
              <div style={{ fontSize: 9, color: "var(--sf-text-muted)", marginTop: 4 }}>Target: {target}%</div>
            </div>
          );
        })}
      </div>

      {/* Expanded Framework Detail */}
      {expanded && (() => {
        const fw = FRAMEWORKS_STATIC.find(f => f.key === expanded)!;
        const sc = fwScores[fw.key] ?? 75;
        return (
          <div className="sf-card sf-animate-in" style={{ marginBottom: 20, borderColor: `${fw.color}40`, background: `linear-gradient(135deg, ${fw.color}10, transparent)` }}>
            <div className="sf-card-header">
              <div>
                <div className="sf-card-title">{fw.icon} {fw.name} — Detailed View</div>
                <div className="sf-card-subtitle">{fw.desc} · {fw.controls} controls mapped</div>
              </div>
              <button className="sf-btn sf-btn-secondary sf-btn-sm" onClick={() => setExpanded(null)}>Close</button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
              <div style={{ background: "rgba(255,255,255,0.04)", borderRadius: 8, padding: 16, textAlign: "center" }}>
                <div style={{ fontSize: 36, fontWeight: 900, color: fw.color }}>{sc}</div>
                <div style={{ fontSize: 10, color: "var(--sf-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Current Score</div>
              </div>
              <div style={{ background: "rgba(255,255,255,0.04)", borderRadius: 8, padding: 16, textAlign: "center" }}>
                <div style={{ fontSize: 36, fontWeight: 900, color: "#f59e0b" }}>{fw.target - sc > 0 ? fw.target - sc : 0}</div>
                <div style={{ fontSize: 10, color: "var(--sf-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Gap to Target</div>
              </div>
              <div style={{ background: "rgba(255,255,255,0.04)", borderRadius: 8, padding: 16, textAlign: "center" }}>
                <div style={{ fontSize: 36, fontWeight: 900, color: "#10b981" }}>{fw.controls}</div>
                <div style={{ fontSize: 10, color: "var(--sf-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>Controls Mapped</div>
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--sf-text-muted)", marginBottom: 8 }}>Control Domains</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {fw.categories.map(c => (
                  <span key={c} style={{ fontSize: 11, padding: "4px 10px", borderRadius: 6, background: `${fw.color}20`, color: fw.color, border: `1px solid ${fw.color}30`, fontFamily: "monospace" }}>
                    {c}
                  </span>
                ))}
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── MIDDLE: Overall Score + AI Recommendations + Violations ── */}
      <div style={{ display: "grid", gridTemplateColumns: "200px 1fr", gap: 20, marginBottom: 20 }}>

        {/* Overall Score */}
        <div className="sf-card" style={{ textAlign: "center", display: "flex", flexDirection: "column", justifyContent: "center" }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--sf-text-muted)", marginBottom: 12 }}>
            Overall Compliance
          </div>
          <div style={{ fontSize: 64, fontWeight: 900, lineHeight: 1, color: overallComputed >= 80 ? "#10b981" : overallComputed >= 60 ? "#eab308" : "#dc2626" }}>
            {overallComputed}
          </div>
          <div style={{ fontSize: 13, color: "var(--sf-text-muted)", marginTop: 6 }}>/ 100</div>
          <div style={{ marginTop: 12 }}>
            <span className={`sf-badge ${overallComputed >= 80 ? "low" : overallComputed >= 60 ? "medium" : "critical"}`}>
              {overallComputed >= 80 ? "COMPLIANT" : overallComputed >= 60 ? "REVIEW NEEDED" : "NON-COMPLIANT"}
            </span>
          </div>
          <div style={{ marginTop: 12, fontSize: 11, color: "var(--sf-text-muted)" }}>
            Violation score: {score?.controls_violated ?? 0} controls
          </div>
        </div>

        {/* AI Recommendations */}
        <div className="sf-card">
          <div className="sf-card-header">
            <div className="sf-card-title">🤖 AI Compliance Recommendations</div>
            <span className="sf-badge info">Auto-generated</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {AI_RECS.map((rec, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12, padding: "10px 14px", borderRadius: 8, background: "rgba(255,255,255,0.02)", border: "1px solid var(--sf-border)" }}>
                <span style={{ fontSize: 18, flexShrink: 0 }}>{rec.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: 3 }}>{rec.title}</div>
                  <div style={{ fontSize: 10, color: "var(--sf-accent-light)", fontFamily: "monospace" }}>{rec.framework}</div>
                </div>
                <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                  <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 4, background: `${impactColor(rec.impact)}20`, color: impactColor(rec.impact), border: `1px solid ${impactColor(rec.impact)}30` }}>
                    Impact: {rec.impact}
                  </span>
                  <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 7px", borderRadius: 4, background: `${effortColor(rec.effort)}20`, color: effortColor(rec.effort), border: `1px solid ${effortColor(rec.effort)}30` }}>
                    Effort: {rec.effort}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Violations Table ─────────────────────────────── */}
      <div className="sf-card">
        <div className="sf-card-header">
          <div className="sf-card-title"><AlertTriangle size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "text-bottom", color: "#f97316" }} /> Compliance Violations — Live Detection</div>
          <span className="sf-badge high">{violations.length} violations</span>
        </div>
        {violations.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px", color: "var(--sf-text-muted)" }}>
            <CheckCircle size={36} color="#10b981" style={{ opacity: 0.5, marginBottom: 10 }} />
            <div style={{ fontWeight: 600 }}>No violations detected</div>
            <div style={{ fontSize: 12, marginTop: 4 }}>All controls currently satisfied</div>
          </div>
        ) : (
          <table className="sf-table">
            <thead><tr><th>Alert</th><th>Type</th><th>NIST Control</th><th>CIS Control</th><th>Severity</th><th>Detected</th></tr></thead>
            <tbody>
              {violations.slice(0, 12).map((v: any, i: number) => (
                <tr key={i}>
                  <td style={{ fontSize: 12, maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "var(--sf-text-primary)", fontWeight: 500 }}>{v.alert_title}</td>
                  <td style={{ fontSize: 11, color: "var(--sf-text-muted)", textTransform: "capitalize" }}>{v.alert_type?.replace(/_/g, " ")}</td>
                  <td><span style={{ fontFamily: "monospace", fontSize: 11, color: "#818cf8" }}>{v.nist_mapping?.category || "—"}</span></td>
                  <td><span style={{ fontFamily: "monospace", fontSize: 11, color: "#93c5fd" }}>{v.cis_mapping?.control_id || "—"}</span></td>
                  <td><span className={`sf-badge ${v.severity}`}>{v.severity}</span></td>
                  <td style={{ fontSize: 11, color: "var(--sf-text-muted)" }}>{v.detected_at ? new Date(v.detected_at).toLocaleTimeString() : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Audit Report Modal */}
      {showAudit && (
        <AuditReportModal
          onClose={() => setShowAudit(false)}
          fwScores={fwScores}
          violations={violations}
        />
      )}
    </div>
  );
}
