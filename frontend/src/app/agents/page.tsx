"use client";

import { useEffect, useState } from "react";

interface Agent {
  name: string;
  description: string;
  llm_provider: string;
  llm_display: string;
  capabilities: string[];
  version: string;
  status: string;
}

interface AgentStatusData {
  architecture: string;
  total_agents: number;
  agents: Agent[];
  llm_providers: Record<string, { name: string; model: string; agents: string[] }>;
}

const providerStyles: Record<string, { gradient: string; icon: string; color: string }> = {
  gemini: {
    gradient: "linear-gradient(135deg, rgba(66,133,244,0.12), rgba(52,168,83,0.10))",
    icon: "💎",
    color: "#8ab4f8",
  },
  grok: {
    gradient: "linear-gradient(135deg, rgba(239,68,68,0.12), rgba(249,115,22,0.10))",
    icon: "⚡",
    color: "#f87171",
  },
};

const capabilityIcons: Record<string, string> = {
  severity_classification: "📊",
  priority_assignment: "🎯",
  false_positive_detection: "🔍",
  alert_deduplication: "🔗",
  root_cause_analysis: "🧬",
  attack_path_identification: "🛤️",
  event_correlation: "📡",
  timeline_reconstruction: "⏱️",
  ioc_extraction: "🧪",
  remediation_planning: "📋",
  firewall_rule_generation: "🛡️",
  security_hardening: "🔒",
  playbook_execution: "▶️",
  executive_report: "📈",
  technical_report: "📝",
  incident_summary: "📄",
  post_incident_review: "🔬",
  vpn_troubleshooting: "🌐",
  email_troubleshooting: "📧",
  printer_troubleshooting: "🖨️",
  performance_diagnosis: "⚡",
  account_management: "🔑",
  software_installation: "💾",
};

export default function AgentsPage() {
  const [data, setData] = useState<AgentStatusData | null>(null);
  const [selected, setSelected] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/agents/status")
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="sf-animate-in" style={{ textAlign: "center", padding: "80px" }}>
        <div className="sf-loading-spinner" />
        <div style={{ marginTop: "16px", color: "var(--sf-text-muted)" }}>Loading agent status...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="sf-animate-in" style={{ textAlign: "center", padding: "80px" }}>
        <div style={{ fontSize: "48px", marginBottom: "16px" }}>⚠️</div>
        <div style={{ color: "var(--sf-text-muted)" }}>Failed to load agent status</div>
      </div>
    );
  }

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">🤖 AI Agent System</h1>
          <p className="sf-page-subtitle">
            {data.total_agents} agents • Multi-LLM architecture • {data.architecture.replace(/_/g, " ")}
          </p>
        </div>
      </div>

      {/* LLM Provider Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "24px" }}>
        {Object.entries(data.llm_providers).map(([key, prov]) => {
          const style = providerStyles[key] || providerStyles.grok;
          return (
            <div key={key} className="sf-card" style={{ background: style.gradient, borderColor: `${style.color}33` }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
                <span style={{ fontSize: "28px" }}>{style.icon}</span>
                <div>
                  <div style={{ fontSize: "16px", fontWeight: 700, color: style.color }}>{prov.name}</div>
                  <div style={{ fontSize: "12px", color: "var(--sf-text-muted)", fontFamily: "monospace" }}>{prov.model}</div>
                </div>
              </div>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {prov.agents.map((a) => (
                  <span key={a} className="sf-badge info" style={{ fontSize: "11px" }}>
                    {a.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Agent Grid */}
      <div style={{ display: "grid", gridTemplateColumns: selected ? "1fr 1fr" : "1fr 1fr 1fr", gap: "16px" }}>
        {data.agents.map((agent) => {
          const style = providerStyles[agent.llm_provider] || providerStyles.grok;
          const isSelected = selected?.name === agent.name;
          return (
            <div
              key={agent.name}
              className="sf-card"
              onClick={() => setSelected(isSelected ? null : agent)}
              style={{
                cursor: "pointer",
                borderColor: isSelected ? style.color : undefined,
                background: isSelected ? style.gradient : undefined,
                transition: "all 0.3s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--sf-text-primary)", marginBottom: "4px" }}>
                    {agent.name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>v{agent.version}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <div style={{
                    width: "8px", height: "8px", borderRadius: "50%",
                    background: agent.status === "active" ? "#22c55e" : "#ef4444",
                    boxShadow: agent.status === "active" ? "0 0 8px rgba(34,197,94,0.5)" : undefined,
                  }} />
                  <span style={{ fontSize: "11px", color: agent.status === "active" ? "#22c55e" : "#ef4444" }}>
                    {agent.status}
                  </span>
                </div>
              </div>

              <p style={{ fontSize: "12px", color: "var(--sf-text-secondary)", marginBottom: "12px", lineHeight: 1.5 }}>
                {agent.description}
              </p>

              <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                <span style={{ fontSize: "14px" }}>{style.icon}</span>
                <span style={{ fontSize: "11px", fontWeight: 600, color: style.color }}>{agent.llm_display}</span>
              </div>

              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {agent.capabilities.slice(0, 3).map((cap) => (
                  <span key={cap} style={{
                    fontSize: "10px", padding: "2px 6px", borderRadius: "4px",
                    background: "rgba(255,255,255,0.05)", color: "var(--sf-text-muted)",
                  }}>
                    {capabilityIcons[cap] || "⚙️"} {cap.replace(/_/g, " ")}
                  </span>
                ))}
                {agent.capabilities.length > 3 && (
                  <span style={{ fontSize: "10px", color: "var(--sf-text-muted)", padding: "2px 4px" }}>
                    +{agent.capabilities.length - 3} more
                  </span>
                )}
              </div>
            </div>
          );
        })}

        {/* Detail Panel */}
        {selected && (
          <div className="sf-card sf-animate-in" style={{ gridColumn: "span 1" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "16px", fontWeight: 700, color: "var(--sf-text-primary)" }}>
                {selected.name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </h2>
              <button className="sf-btn sf-btn-secondary sf-btn-sm" onClick={() => setSelected(null)}>✕ Close</button>
            </div>

            <p style={{ fontSize: "13px", color: "var(--sf-text-secondary)", lineHeight: 1.6, marginBottom: "16px" }}>
              {selected.description}
            </p>

            <div style={{ marginBottom: "16px" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--sf-text-muted)", marginBottom: "8px" }}>
                LLM Provider
              </div>
              <div style={{
                padding: "12px", borderRadius: "8px",
                background: providerStyles[selected.llm_provider]?.gradient,
                display: "flex", alignItems: "center", gap: "8px",
              }}>
                <span style={{ fontSize: "20px" }}>{providerStyles[selected.llm_provider]?.icon}</span>
                <div>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: providerStyles[selected.llm_provider]?.color }}>
                    {selected.llm_display}
                  </div>
                  <div style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>
                    Model: {data.llm_providers[selected.llm_provider]?.model}
                  </div>
                </div>
              </div>
            </div>

            <div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--sf-text-muted)", marginBottom: "8px" }}>
                Capabilities ({selected.capabilities.length})
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {selected.capabilities.map((cap) => (
                  <div key={cap} style={{
                    padding: "8px 12px", borderRadius: "8px",
                    background: "rgba(255,255,255,0.03)", border: "1px solid var(--sf-border)",
                    display: "flex", alignItems: "center", gap: "8px",
                  }}>
                    <span style={{ fontSize: "14px" }}>{capabilityIcons[cap] || "⚙️"}</span>
                    <span style={{ fontSize: "12px", color: "var(--sf-text-secondary)", textTransform: "capitalize" }}>
                      {cap.replace(/_/g, " ")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
