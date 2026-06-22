"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Search, Activity, Shield, AlertTriangle, Users, Server,
  ChevronRight, RefreshCw, Wifi, Target, Eye
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchHunt(endpoint: string) {
  const res = await fetch(`${API_BASE}${endpoint}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

const HUNT_TYPES = [
  {
    id: "all",
    label: "Full Threat Hunt",
    icon: "🔍",
    desc: "Run all hunting queries at once",
    color: "#6366f1",
    endpoint: "/api/knowledge-graph/hunt/all",
  },
  {
    id: "lateral",
    label: "Lateral Movement",
    icon: "↗",
    desc: "Detect pivot paths between assets",
    color: "#ef4444",
    endpoint: "/api/knowledge-graph/hunt/lateral-movement",
  },
  {
    id: "malicious",
    label: "Malicious Comms",
    icon: "🌐",
    desc: "Devices talking to known bad IPs",
    color: "#f97316",
    endpoint: "/api/knowledge-graph/hunt/malicious-comms",
  },
  {
    id: "users",
    label: "High-Risk Users",
    icon: "👤",
    desc: "Users tied to multiple incidents",
    color: "#f59e0b",
    endpoint: "/api/knowledge-graph/hunt/high-risk-users",
  },
  {
    id: "vulns",
    label: "Vulnerable Assets",
    icon: "⚠️",
    desc: "Exposed assets connected to critical infra",
    color: "#10b981",
    endpoint: "/api/knowledge-graph/hunt/vulnerable-assets",
  },
];

function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    critical: "#ef4444", high: "#f97316", medium: "#f59e0b", low: "#10b981"
  };
  return (
    <span style={{
      padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 700,
      background: `${colors[level] || "#9ca3af"}22`,
      color: colors[level] || "#9ca3af",
      border: `1px solid ${colors[level] || "#9ca3af"}44`,
      textTransform: "uppercase",
    }}>
      {level}
    </span>
  );
}

function EntityTag({ label, type }: { label: string; type?: string }) {
  const typeColors: Record<string, string> = {
    user: "#3b82f6", device: "#8b5cf6", asset: "#f59e0b",
    ioc: "#ec4899", malware: "#7c3aed", ip: "#ef4444",
  };
  const color = typeColors[type || ""] || "#64748b";
  return (
    <span style={{
      display: "inline-block", padding: "2px 8px", borderRadius: 4,
      background: `${color}18`, color, fontSize: 11, fontWeight: 600,
      border: `1px solid ${color}33`, marginRight: 4, marginBottom: 4,
    }}>
      {type && <span style={{ opacity: 0.7 }}>{type}: </span>}
      {label.replace(/^[^:]+:/, "")}
    </span>
  );
}

function LateralMovementCard({ chains }: { chains: any[] }) {
  if (!chains?.length) return (
    <div style={{ textAlign: "center", padding: "40px 0", color: "var(--sf-text-muted)" }}>
      <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
      No lateral movement chains detected
    </div>
  );
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {chains.map((chain, i) => (
        <div key={i} style={{
          background: "rgba(239,68,68,0.06)", border: "1px solid rgba(239,68,68,0.2)",
          borderRadius: 8, padding: "14px 16px",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <EntityTag label={chain.from_entity} type={chain.from_type} />
            <span style={{ color: "#ef4444", fontWeight: 700, fontSize: 18 }}>→</span>
            <span style={{ fontSize: 11, color: "#f97316", background: "rgba(249,115,22,0.1)",
              padding: "1px 6px", borderRadius: 4, border: "1px solid rgba(249,115,22,0.3)" }}>
              lateral_move_to
            </span>
            <span style={{ color: "#ef4444", fontWeight: 700, fontSize: 18 }}>→</span>
            <EntityTag label={chain.to_entity} type={chain.to_type} />
            <RiskBadge level={chain.risk || "high"} />
          </div>
          {chain.to_props?.criticality && (
            <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 6 }}>
              Target criticality: <strong style={{ color: "#f97316" }}>{chain.to_props.criticality}</strong>
              {chain.to_props.os && ` • OS: ${chain.to_props.os}`}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function MaliciousCommsCard({ hits }: { hits: any[] }) {
  if (!hits?.length) return (
    <div style={{ textAlign: "center", padding: "40px 0", color: "var(--sf-text-muted)" }}>
      <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
      No malicious communications detected
    </div>
  );
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {hits.map((h, i) => (
        <div key={i} style={{
          background: "rgba(249,115,22,0.06)", border: "1px solid rgba(249,115,22,0.2)",
          borderRadius: 8, padding: "12px 16px",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <EntityTag label={h.entity} type={h.type} />
            <span style={{ color: "var(--sf-text-muted)", fontSize: 12 }}>↔ [{h.relation}] ↔</span>
            <EntityTag label={h.malicious_ioc} type="ioc" />
            <RiskBadge level="high" />
          </div>
          {h.properties?.reputation && (
            <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 4 }}>
              IOC reputation: <strong style={{ color: "#ef4444" }}>{h.properties.reputation}</strong>
              {h.properties.source && ` • Source: ${h.properties.source}`}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function UsersCard({ users }: { users: any[] }) {
  if (!users?.length) return (
    <div style={{ textAlign: "center", padding: "40px 0", color: "var(--sf-text-muted)" }}>
      <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
      No high-risk users found
    </div>
  );
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {users.map((u, i) => (
        <div key={i} style={{
          background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.2)",
          borderRadius: 8, padding: "14px 16px",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 20 }}>👤</span>
              <span style={{ fontWeight: 600 }}>{u.user}</span>
              <RiskBadge level={u.risk_score > 0.6 ? "critical" : "high"} />
            </div>
            <span style={{ fontSize: 12, color: "#f59e0b", fontWeight: 600 }}>
              {u.incident_count} incidents
            </span>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {u.incidents?.map((inc: string, j: number) => (
              <span key={j} style={{
                fontSize: 11, padding: "2px 6px", borderRadius: 4,
                background: "rgba(239,68,68,0.1)", color: "#ef4444",
                border: "1px solid rgba(239,68,68,0.2)",
              }}>{inc.replace("incident:", "")}</span>
            ))}
          </div>
          {u.properties?.role && (
            <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 6 }}>
              Role: {u.properties.role} • Dept: {u.properties.department}
              {u.properties.mfa === false && (
                <span style={{ color: "#ef4444", marginLeft: 8 }}>⚠ No MFA</span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function VulnAssetsCard({ vulns }: { vulns: any[] }) {
  if (!vulns?.length) return (
    <div style={{ textAlign: "center", padding: "40px 0", color: "var(--sf-text-muted)" }}>
      <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
      No vulnerable connected assets found
    </div>
  );
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {vulns.map((v, i) => (
        <div key={i} style={{
          background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.2)",
          borderRadius: 8, padding: "14px 16px",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <EntityTag label={v.entity} type={v.type} />
              <RiskBadge level={v.risk || "high"} />
            </div>
            <span style={{ fontSize: 11, color: "var(--sf-text-muted)" }}>
              {v.properties?.criticality && `criticality: ${v.properties.criticality}`}
            </span>
          </div>
          <div style={{ fontSize: 12, color: "var(--sf-text-secondary)", marginBottom: 6 }}>
            <span style={{ color: "#f97316", fontWeight: 600 }}>CVEs: </span>
            {v.cves?.join(", ")}
          </div>
          <div style={{ fontSize: 11, color: "var(--sf-text-muted)" }}>
            Connected to: {v.connected_assets?.join(", ")}
          </div>
        </div>
      ))}
    </div>
  );
}

function SummaryCard({ summary, mitreCov }: { summary: any; mitreCov: any }) {
  if (!summary) return null;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 24 }}>
      {[
        { label: "Total Findings", value: summary.total_findings, icon: "🔍", color: "#6366f1" },
        { label: "Lateral Movement", value: summary.lateral_movement_chains, icon: "↗", color: "#ef4444" },
        { label: "Malicious Comms", value: summary.malicious_communications, icon: "🌐", color: "#f97316" },
        { label: "High-Risk Users", value: summary.high_risk_users, icon: "👤", color: "#f59e0b" },
        { label: "Vulnerable Assets", value: summary.vulnerable_assets, icon: "⚠️", color: "#10b981" },
        { label: "MITRE Coverage", value: `${mitreCov?.coverage_pct || 0}%`, icon: "🎯", color: "#06b6d4" },
      ].map((stat) => (
        <div key={stat.label} className="sf-card" style={{ padding: "16px", textAlign: "center" }}>
          <div style={{ fontSize: 24, marginBottom: 4 }}>{stat.icon}</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: stat.color }}>{stat.value}</div>
          <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 2 }}>{stat.label}</div>
        </div>
      ))}
    </div>
  );
}

export default function ThreatHuntingPage() {
  const [activeHunt, setActiveHunt] = useState("all");
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runHunt = useCallback(async (huntId: string) => {
    const hunt = HUNT_TYPES.find(h => h.id === huntId);
    if (!hunt) return;
    setActiveHunt(huntId);
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHunt(hunt.endpoint);
      setResults({ id: huntId, data });
    } catch (e: any) {
      setError(e.message || "Hunt failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    runHunt("all");
  }, []);

  const allData = results?.id === "all" ? results.data : null;
  const singleData = results?.id !== "all" ? results?.data : null;

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 className="sf-page-title">🕵️ Threat Hunting Center</h1>
          <p className="sf-page-subtitle">
            Graph-powered hunting — lateral movement · malicious comms · vulnerable assets · high-risk users
          </p>
        </div>
        <button
          className="sf-btn sf-btn-outline"
          onClick={() => runHunt(activeHunt)}
          disabled={loading}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          <RefreshCw size={14} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
          Re-run Hunt
        </button>
      </div>

      {/* Hunt Type Selector */}
      <div style={{ display: "flex", gap: 10, marginBottom: 24, flexWrap: "wrap" }}>
        {HUNT_TYPES.map(hunt => (
          <button
            key={hunt.id}
            onClick={() => runHunt(hunt.id)}
            style={{
              padding: "10px 16px", borderRadius: 8, cursor: "pointer",
              border: `1px solid ${activeHunt === hunt.id ? hunt.color : "var(--sf-border)"}`,
              background: activeHunt === hunt.id ? `${hunt.color}18` : "var(--sf-card-bg)",
              color: activeHunt === hunt.id ? hunt.color : "var(--sf-text-secondary)",
              fontWeight: activeHunt === hunt.id ? 700 : 400,
              fontSize: 13, transition: "all 0.15s ease",
              display: "flex", alignItems: "center", gap: 6,
            }}
          >
            <span>{hunt.icon}</span>
            {hunt.label}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div style={{
          background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)",
          borderRadius: 8, padding: "12px 16px", marginBottom: 16, color: "#ef4444", fontSize: 13,
        }}>
          ⚠ {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ display: "flex", justifyContent: "center", padding: "60px 0" }}>
          <div className="sf-loading-spinner" />
        </div>
      )}

      {/* Results */}
      {!loading && results && (
        <>
          {/* Full hunt summary */}
          {allData && (
            <>
              <SummaryCard summary={allData.summary} mitreCov={allData.mitre_coverage} />

              {allData.summary?.total_findings === 0 ? (
                <div className="sf-card" style={{ padding: 32, textAlign: "center" }}>
                  <div style={{ fontSize: 48, marginBottom: 12 }}>🛡️</div>
                  <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>No Threats Found</div>
                  <div style={{ color: "var(--sf-text-muted)", fontSize: 13 }}>
                    Knowledge graph analysis complete — no active threat patterns detected.
                  </div>
                </div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                  {/* Lateral Movement */}
                  <div className="sf-card" style={{ padding: 20 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ color: "#ef4444" }}>↗</span> Lateral Movement Chains
                      <span style={{ marginLeft: "auto", background: "rgba(239,68,68,0.1)", color: "#ef4444",
                        padding: "2px 8px", borderRadius: 10, fontSize: 12 }}>
                        {allData.lateral_movement?.length || 0}
                      </span>
                    </h3>
                    <LateralMovementCard chains={allData.lateral_movement} />
                  </div>

                  {/* Malicious Comms */}
                  <div className="sf-card" style={{ padding: 20 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ color: "#f97316" }}>🌐</span> Malicious Communications
                      <span style={{ marginLeft: "auto", background: "rgba(249,115,22,0.1)", color: "#f97316",
                        padding: "2px 8px", borderRadius: 10, fontSize: 12 }}>
                        {allData.malicious_communications?.length || 0}
                      </span>
                    </h3>
                    <MaliciousCommsCard hits={allData.malicious_communications} />
                  </div>

                  {/* High-Risk Users */}
                  <div className="sf-card" style={{ padding: 20 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ color: "#f59e0b" }}>👤</span> High-Risk Users
                      <span style={{ marginLeft: "auto", background: "rgba(245,158,11,0.1)", color: "#f59e0b",
                        padding: "2px 8px", borderRadius: 10, fontSize: 12 }}>
                        {allData.high_risk_users?.length || 0}
                      </span>
                    </h3>
                    <UsersCard users={allData.high_risk_users} />
                  </div>

                  {/* Vulnerable Assets */}
                  <div className="sf-card" style={{ padding: 20 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ color: "#10b981" }}>⚠️</span> Vulnerable Connected Assets
                      <span style={{ marginLeft: "auto", background: "rgba(16,185,129,0.1)", color: "#10b981",
                        padding: "2px 8px", borderRadius: 10, fontSize: 12 }}>
                        {allData.vulnerable_assets?.length || 0}
                      </span>
                    </h3>
                    <VulnAssetsCard vulns={allData.vulnerable_assets} />
                  </div>
                </div>
              )}

              {/* MITRE Coverage */}
              {allData.mitre_coverage && (
                <div className="sf-card" style={{ padding: 20, marginTop: 20 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>🎯 MITRE ATT&CK Coverage Analysis</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12, marginBottom: 16 }}>
                    {[
                      { label: "Techniques in Use", value: allData.mitre_coverage.total_techniques, color: "#ef4444" },
                      { label: "Covered by Controls", value: allData.mitre_coverage.covered, color: "#10b981" },
                      { label: "Coverage %", value: `${allData.mitre_coverage.coverage_pct}%`, color: "#06b6d4" },
                      { label: "Uncovered", value: allData.mitre_coverage.uncovered_count, color: "#f97316" },
                    ].map(s => (
                      <div key={s.label} style={{ background: "rgba(0,0,0,0.2)", borderRadius: 8, padding: "12px 16px", textAlign: "center" }}>
                        <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
                        <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginTop: 2 }}>{s.label}</div>
                      </div>
                    ))}
                  </div>
                  {allData.mitre_coverage.uncovered_techniques?.length > 0 && (
                    <div>
                      <div style={{ fontSize: 12, color: "var(--sf-text-muted)", marginBottom: 8 }}>
                        Uncovered techniques (no security control mitigates):
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                        {allData.mitre_coverage.uncovered_techniques.map((t: string) => (
                          <span key={t} style={{
                            padding: "3px 8px", borderRadius: 4, fontSize: 12,
                            background: "rgba(249,115,22,0.1)", color: "#f97316",
                            border: "1px solid rgba(249,115,22,0.3)", fontFamily: "monospace",
                          }}>{t}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* Single hunt result */}
          {singleData && !allData && (
            <div className="sf-card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>
                {HUNT_TYPES.find(h => h.id === results.id)?.icon} {HUNT_TYPES.find(h => h.id === results.id)?.label}
                <span style={{ marginLeft: 12, fontSize: 12, color: "var(--sf-text-muted)", fontWeight: 400 }}>
                  {singleData.count} finding{singleData.count !== 1 ? "s" : ""}
                </span>
              </h3>
              {results.id === "lateral" && <LateralMovementCard chains={singleData.results} />}
              {results.id === "malicious" && <MaliciousCommsCard hits={singleData.results} />}
              {results.id === "users" && <UsersCard users={singleData.results} />}
              {results.id === "vulns" && <VulnAssetsCard vulns={singleData.results} />}
            </div>
          )}
        </>
      )}
    </div>
  );
}
