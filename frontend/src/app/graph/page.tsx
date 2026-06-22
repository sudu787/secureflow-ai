"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { getGraphVisualization, getGraphStats } from "@/lib/api";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const ENTITY_COLORS: Record<string, string> = {
  ip:                 "#ef4444",
  user:               "#3b82f6",
  device:             "#8b5cf6",
  asset:              "#f59e0b",
  application:        "#06b6d4",
  alert:              "#ef4444",
  incident:           "#b91c1c",
  vulnerability:      "#f97316",
  cve:                "#f97316",
  threat_actor:       "#dc2626",
  malware:            "#7c3aed",
  ioc:                "#ec4899",
  mitre_technique:    "#10b981",
  mitre_tactic:       "#059669",
  security_control:   "#0ea5e9",
  compliance_control: "#64748b",
  software:           "#84cc16",
};

const ENTITY_ICONS: Record<string, string> = {
  ip: "🌐", user: "👤", device: "💻", asset: "🖥️", application: "📱",
  alert: "🚨", incident: "🔥", vulnerability: "⚠️", cve: "⚠️",
  threat_actor: "☠️", malware: "🦠", ioc: "📍", mitre_technique: "🎯",
  mitre_tactic: "🗺️", security_control: "🛡️", compliance_control: "📋",
  software: "📦",
};

const VIEWS = [
  { id: "all",      label: "All Entities",       icon: "🌐" },
  { id: "attack",   label: "Attack Surface",      icon: "⚔️" },
  { id: "threat",   label: "Threat Actors",       icon: "☠️" },
  { id: "vuln",     label: "Vulnerability Intel", icon: "⚠️" },
  { id: "mitre",    label: "MITRE ATT&CK",        icon: "🎯" },
  { id: "risk",     label: "Risk Propagation",    icon: "🔥" },
];

const VIEW_TYPES: Record<string, string[]> = {
  all:    [],
  attack: ["alert", "incident", "ip", "ioc", "user", "device", "asset"],
  threat: ["threat_actor", "malware", "ioc", "mitre_technique", "mitre_tactic", "cve"],
  vuln:   ["cve", "software", "asset", "device", "security_control"],
  mitre:  ["mitre_technique", "mitre_tactic", "threat_actor", "malware", "incident"],
  risk:   ["user", "device", "asset", "application", "incident", "alert"],
};

export default function GraphExplorer() {
  const [graphData, setGraphData]       = useState<any>({ nodes: [], links: [] });
  const [filteredData, setFilteredData] = useState<any>({ nodes: [], links: [] });
  const [stats, setStats]               = useState<any>(null);
  const [loading, setLoading]           = useState(true);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [activeView, setActiveView]     = useState("all");
  const [searchTerm, setSearchTerm]     = useState("");
  const [dimensions, setDimensions]     = useState({ width: 800, height: 600 });
  const [riskData, setRiskData]         = useState<any>(null);
  const [riskLoading, setRiskLoading]   = useState(false);
  const [entityContext, setEntityContext] = useState<any>(null);

  const fgRef        = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Responsive canvas
  useEffect(() => {
    if (!containerRef.current) return;
    const ob = new ResizeObserver(entries => {
      for (const e of entries) {
        setDimensions({ width: e.contentRect.width, height: e.contentRect.height });
      }
    });
    ob.observe(containerRef.current);
    return () => ob.disconnect();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [vizData, statData] = await Promise.all([
        getGraphVisualization(),
        getGraphStats(),
      ]);
      const formatted = {
        nodes: vizData.nodes.map((n: any) => ({ ...n, val: getNodeSize(n) })),
        links: vizData.edges.map((e: any) => ({
          source: e.source, target: e.target, label: e.relation
        })),
      };
      setGraphData(formatted);
      setStats(statData);
    } catch (e) {
      console.error("Failed to load graph data", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  // Apply view filter + search
  useEffect(() => {
    const allowedTypes = VIEW_TYPES[activeView];
    let nodes = graphData.nodes;

    if (allowedTypes.length > 0) {
      nodes = nodes.filter((n: any) => allowedTypes.includes(n.type));
    }
    if (searchTerm) {
      const s = searchTerm.toLowerCase();
      nodes = nodes.filter((n: any) =>
        (n.label || "").toLowerCase().includes(s) ||
        (n.type || "").toLowerCase().includes(s) ||
        JSON.stringify(n.properties || {}).toLowerCase().includes(s)
      );
    }
    const nodeIds = new Set(nodes.map((n: any) => n.id));
    const links = graphData.links.filter(
      (l: any) => nodeIds.has(l.source?.id || l.source) && nodeIds.has(l.target?.id || l.target)
    );
    setFilteredData({ nodes, links });
  }, [graphData, activeView, searchTerm]);

  function getNodeSize(node: any): number {
    const type = node.type || "";
    if (["incident", "threat_actor"].includes(type)) return 3.5;
    if (["malware", "cve", "ioc"].includes(type)) return 2.5;
    if (["asset", "user"].includes(type)) return 2;
    return 1.5;
  }

  const getNodeColor = useCallback((node: any): string => {
    if (riskData && activeView === "risk") {
      const affected = riskData.affected_entities || [];
      const hit = affected.find((e: any) => e.entity === node.id);
      if (hit) {
        if (hit.risk_level === "critical") return "#ef4444";
        if (hit.risk_level === "high") return "#f97316";
        if (hit.risk_level === "medium") return "#f59e0b";
        return "#10b981";
      }
    }
    return ENTITY_COLORS[node.type] || "#9ca3af";
  }, [riskData, activeView]);

  const handleNodeClick = useCallback(async (node: any) => {
    setSelectedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(7, 1000);
    }
    // Load entity context from graph API
    try {
      const res = await fetch(`${API_BASE}/api/knowledge-graph/entity/${node.type}/${encodeURIComponent(node.label || node.id)}`);
      if (res.ok) setEntityContext(await res.json());
    } catch { setEntityContext(null); }
  }, []);

  const runRiskPropagation = async () => {
    if (!selectedNode) return;
    setRiskLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/knowledge-graph/risk/propagate/${selectedNode.type}/${encodeURIComponent(selectedNode.label || selectedNode.id)}`);
      if (res.ok) {
        const data = await res.json();
        setRiskData(data);
        setActiveView("risk");
      }
    } catch (e) {
      console.error(e);
    } finally {
      setRiskLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      if (fgRef.current && filteredData.nodes.length > 0) {
        const charge = fgRef.current.d3Force("charge");
        const link   = fgRef.current.d3Force("link");
        if (charge && link) {
          charge.strength(-350);
          link.distance(90);
          fgRef.current.d3ReheatSimulation();
        }
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [filteredData]);

  const drawNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label    = node.label || node.id;
    const fontSize = Math.max(12 / globalScale, 2);
    const radius   = node.val ? Math.max(node.val * 2.8, 5) : 8;
    const color    = getNodeColor(node);

    ctx.shadowColor = color;
    ctx.shadowBlur  = 15;
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    // Risk ring for propagation view
    if (riskData && activeView === "risk") {
      const affected = (riskData.affected_entities || []).find((e: any) => e.entity === node.id);
      if (affected) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5 / globalScale;
        ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    ctx.shadowBlur = 0;
    ctx.fillStyle  = "#ffffff";
    ctx.textAlign  = "center";
    ctx.textBaseline = "middle";
    ctx.font = `${radius * 0.85}px Arial`;
    ctx.fillText(ENTITY_ICONS[node.type] || "•", node.x, node.y);

    const isSelected = selectedNode?.id === node.id;
    if (globalScale > 1.1 || isSelected) {
      ctx.font = `${isSelected ? "bold " : ""}${fontSize}px Sans-Serif`;
      ctx.fillStyle = isSelected ? "#ffffff" : "rgba(255,255,255,0.75)";
      ctx.fillText(label, node.x, node.y + radius + fontSize + 3);
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius + 7, 0, 2 * Math.PI);
        ctx.strokeStyle = "#6366f1";
        ctx.lineWidth   = 2 / globalScale;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
  }, [selectedNode, getNodeColor, riskData, activeView]);

  const paintHitArea = useCallback((node: any, color: string, ctx: CanvasRenderingContext2D) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(node.x, node.y, 14, 0, 2 * Math.PI);
    ctx.fill();
  }, []);

  const getLinkColor = useCallback((link: any): string => {
    const rel = link.label || "";
    if (["lateral_move_to", "triggered", "exploits"].includes(rel)) return "rgba(239,68,68,0.5)";
    if (["uses", "implements", "c2_communicates_with"].includes(rel)) return "rgba(124,58,237,0.4)";
    if (["vulnerable_to", "affects"].includes(rel)) return "rgba(249,115,22,0.4)";
    if (["mitigates", "prevents", "detects"].includes(rel)) return "rgba(16,185,129,0.4)";
    if (["belongs_to", "part_of", "maps_to"].includes(rel)) return "rgba(6,182,212,0.3)";
    return "rgba(255,255,255,0.12)";
  }, []);

  return (
    <div className="sf-animate-in" style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 40px)" }}>
      <div className="sf-page-header" style={{ marginBottom: 12 }}>
        <div>
          <h1 className="sf-page-title">🕸️ Cyber Relationship Explorer</h1>
          <p className="sf-page-subtitle">
            Security Knowledge Graph — {stats?.total_nodes || 0} nodes · {stats?.total_edges || 0} edges
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            placeholder="Search entities…"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="sf-input"
            style={{ width: 200, fontSize: 13 }}
          />
          <button className="sf-btn sf-btn-outline" onClick={loadData}>🔄 Refresh</button>
        </div>
      </div>

      {/* View Selector */}
      <div style={{ display: "flex", gap: 6, marginBottom: 12, flexWrap: "wrap" }}>
        {VIEWS.map(v => (
          <button
            key={v.id}
            onClick={() => { setActiveView(v.id); if (v.id !== "risk") setRiskData(null); }}
            style={{
              padding: "6px 12px", borderRadius: 6, cursor: "pointer", fontSize: 12,
              border: `1px solid ${activeView === v.id ? "#6366f1" : "var(--sf-border)"}`,
              background: activeView === v.id ? "rgba(99,102,241,0.15)" : "var(--sf-card-bg)",
              color: activeView === v.id ? "#6366f1" : "var(--sf-text-secondary)",
              fontWeight: activeView === v.id ? 700 : 400, transition: "all 0.15s ease",
            }}
          >
            {v.icon} {v.label}
          </button>
        ))}
        <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--sf-text-muted)", padding: "6px 0" }}>
          Showing {filteredData.nodes.length} nodes · {filteredData.links.length} edges
        </span>
      </div>

      <div style={{ display: "flex", flex: 1, gap: 16, minHeight: 0 }}>
        {/* Canvas */}
        <div
          ref={containerRef}
          className="sf-card"
          style={{
            flex: 1, overflow: "hidden", position: "relative", padding: 0,
            background: "radial-gradient(circle at 30% 30%, #1e1b4b 0%, #0a0e1a 70%, #0f1115 100%)",
          }}
        >
          {loading ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
              <div className="sf-loading-spinner" />
            </div>
          ) : (
            <ForceGraph2D
              ref={fgRef}
              graphData={filteredData}
              width={dimensions.width}
              height={dimensions.height}
              linkColor={getLinkColor}
              linkWidth={1.5}
              linkDirectionalParticles={3}
              linkDirectionalParticleWidth={2}
              linkDirectionalParticleSpeed={0.005}
              linkDirectionalParticleColor={getLinkColor}
              onNodeClick={handleNodeClick}
              nodeCanvasObject={drawNode}
              nodePointerAreaPaint={paintHitArea}
              backgroundColor="transparent"
            />
          )}

          {/* Grid overlay */}
          <div style={{
            position: "absolute", top: 0, left: 0, right: 0, bottom: 0, pointerEvents: "none",
            backgroundImage: "linear-gradient(rgba(255,255,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.02) 1px,transparent 1px)",
            backgroundSize: "40px 40px",
          }} />

          {/* Legend */}
          <div style={{
            position: "absolute", bottom: 12, left: 12,
            background: "rgba(0,0,0,0.65)", padding: "10px 14px",
            borderRadius: 8, backdropFilter: "blur(8px)", maxWidth: 340,
          }}>
            <div style={{ fontSize: 10, color: "var(--sf-text-muted)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Entity Legend
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "4px 12px" }}>
              {Object.entries(ENTITY_COLORS).slice(0, 12).map(([type, color]) => (
                <div key={type} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11 }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
                  <span style={{ color: "var(--sf-text-secondary)", textTransform: "capitalize" }}>{type.replace("_", " ")}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Risk propagation overlay */}
          {activeView === "risk" && riskData && (
            <div style={{
              position: "absolute", top: 12, left: 12,
              background: "rgba(0,0,0,0.75)", padding: "12px 16px",
              borderRadius: 8, backdropFilter: "blur(8px)",
              border: "1px solid rgba(239,68,68,0.3)",
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#ef4444", marginBottom: 8 }}>
                🔥 Risk Propagation from {riskData.source}
              </div>
              {Object.entries(riskData.blast_radius || {}).map(([level, count]) => (
                <div key={level} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, gap: 16 }}>
                  <span style={{ color: { critical: "#ef4444", high: "#f97316", medium: "#f59e0b", low: "#10b981" }[level] || "#fff", textTransform: "capitalize" }}>{level}</span>
                  <span style={{ fontWeight: 700 }}>{count as number} entities</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div style={{ width: 300, display: "flex", flexDirection: "column", gap: 12, overflowY: "auto" }}>
          {/* Entity Inspector */}
          <div className="sf-card" style={{ padding: 16, flexShrink: 0 }}>
            <h3 style={{ fontSize: 13, fontWeight: 700, borderBottom: "1px solid var(--sf-border)", paddingBottom: 10, marginBottom: 12 }}>
              🔍 Entity Inspector
            </h3>
            {selectedNode ? (
              <div className="sf-animate-in">
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: 8,
                    background: getNodeColor(selectedNode),
                    display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18,
                  }}>
                    {ENTITY_ICONS[selectedNode.type] || "•"}
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{selectedNode.label}</div>
                    <div style={{ fontSize: 11, color: "var(--sf-text-muted)", textTransform: "uppercase" }}>{selectedNode.type}</div>
                  </div>
                </div>

                {Object.entries(selectedNode.properties || {}).slice(0, 8).map(([k, v]) => (
                  <div key={k} style={{ background: "rgba(0,0,0,0.2)", padding: "6px 8px", borderRadius: 4, marginBottom: 4, fontSize: 12 }}>
                    <span style={{ color: "var(--sf-text-muted)", marginRight: 6, textTransform: "capitalize" }}>{k}:</span>
                    <span style={{ color: "var(--sf-text-primary)", fontWeight: 500, wordBreak: "break-all" }}>{String(v)}</span>
                  </div>
                ))}

                {/* Entity graph relationships */}
                {entityContext?.related_count > 0 && (
                  <div style={{ marginTop: 10 }}>
                    <div style={{ fontSize: 11, color: "var(--sf-text-muted)", marginBottom: 6, textTransform: "uppercase" }}>
                      {entityContext.related_count} connected entities
                    </div>
                    {entityContext.related.slice(0, 5).map((r: any, i: number) => (
                      <div key={i} style={{ fontSize: 11, padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.05)", display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ color: r.direction === "outgoing" ? "#10b981" : "#f97316", fontSize: 10 }}>
                          {r.direction === "outgoing" ? "→" : "←"}
                        </span>
                        <span style={{ color: "var(--sf-text-muted)", fontSize: 10 }}>[{r.relation}]</span>
                        <span style={{ color: ENTITY_COLORS[r.type] || "#9ca3af", fontWeight: 600 }}>
                          {r.entity.split(":")[1]}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Risk Propagation Button */}
                <button
                  className="sf-btn sf-btn-primary"
                  onClick={runRiskPropagation}
                  disabled={riskLoading}
                  style={{ width: "100%", marginTop: 12, fontSize: 12 }}
                >
                  {riskLoading ? "Computing…" : "🔥 Propagate Risk"}
                </button>
              </div>
            ) : (
              <div style={{ color: "var(--sf-text-muted)", fontSize: 12, textAlign: "center", padding: "24px 0" }}>
                <div style={{ fontSize: 28, opacity: 0.2, marginBottom: 8 }}>🖱️</div>
                Click any node to inspect
              </div>
            )}
          </div>

          {/* Graph Stats */}
          {stats && (
            <div className="sf-card" style={{ padding: 16 }}>
              <h3 style={{ fontSize: 13, fontWeight: 700, borderBottom: "1px solid var(--sf-border)", paddingBottom: 10, marginBottom: 12 }}>
                📊 Graph Topology
              </h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 12 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Total Nodes</span>
                  <span style={{ color: "var(--sf-primary)", fontWeight: 700 }}>{stats.total_nodes}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Total Edges</span>
                  <span style={{ color: "var(--sf-primary)", fontWeight: 700 }}>{stats.total_edges}</span>
                </div>

                {stats.node_types && Object.entries(stats.node_types).slice(0, 8).map(([type, count]) => (
                  <div key={type} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ width: 7, height: 7, borderRadius: "50%", background: ENTITY_COLORS[type] || "#9ca3af", display: "inline-block" }} />
                      <span style={{ color: "var(--sf-text-secondary)", textTransform: "capitalize" }}>{type.replace("_", " ")}</span>
                    </div>
                    <span style={{ color: "var(--sf-text-primary)", fontWeight: 600 }}>{count as number}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk Summary */}
          {riskData && (
            <div className="sf-card" style={{ padding: 16 }}>
              <h3 style={{ fontSize: 13, fontWeight: 700, marginBottom: 12, color: "#ef4444" }}>
                🔥 Blast Radius Analysis
              </h3>
              <div style={{ fontSize: 12, marginBottom: 8, color: "var(--sf-text-muted)" }}>
                Source: <strong style={{ color: "#ef4444" }}>{riskData.source}</strong>
              </div>
              <div style={{ fontSize: 12, marginBottom: 12 }}>
                {riskData.total_affected} entities affected
              </div>
              {riskData.affected_entities?.slice(0, 8).map((e: any, i: number) => (
                <div key={i} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.04)", fontSize: 11,
                }}>
                  <span style={{ color: "var(--sf-text-secondary)" }}>{e.entity.split(":")[1]}</span>
                  <span style={{
                    padding: "1px 6px", borderRadius: 4, fontWeight: 700,
                    background: ({ critical: "rgba(239,68,68,0.15)", high: "rgba(249,115,22,0.15)", medium: "rgba(245,158,11,0.15)", low: "rgba(16,185,129,0.15)" })[e.risk_level] || "transparent",
                    color: ({ critical: "#ef4444", high: "#f97316", medium: "#f59e0b", low: "#10b981" })[e.risk_level] || "#fff",
                  }}>
                    {(e.risk_score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
