"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { getGraphVisualization, getGraphStats } from "@/lib/api";

// Dynamically import ForceGraph to avoid SSR issues with canvas
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

export default function GraphExplorer() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const [vizData, statData] = await Promise.all([
        getGraphVisualization(),
        getGraphStats()
      ]);
      
      // Map API edges (source/target) to ForceGraph links
      const formattedData = {
        nodes: vizData.nodes.map((n: any) => ({ ...n, val: 1.5 })),
        links: vizData.edges.map((e: any) => ({
          source: e.source,
          target: e.target,
          label: e.relation
        }))
      };
      
      setGraphData(formattedData);
      setStats(statData);
    } catch (e) {
      console.error("Failed to load graph data", e);
    } finally {
      setLoading(false);
    }
  }

  const getNodeColor = (node: any) => {
    switch (node.type) {
      case "ip": return node.properties?.role === "source" ? "#ef4444" : "#f59e0b"; // red/orange
      case "alert": return "#ef4444"; // red
      case "incident": return "#b91c1c"; // dark red
      case "user": return "#3b82f6"; // blue
      case "device": return "#8b5cf6"; // purple
      case "mitre_technique": return "#10b981"; // green
      default: return "#9ca3af"; // gray
    }
  };

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node);
    
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(8, 1000);
    }
  }, []);

  // Configure physics so nodes spread out safely
  useEffect(() => {
    const timer = setTimeout(() => {
      if (fgRef.current && graphData.nodes.length > 0) {
        const charge = fgRef.current.d3Force('charge');
        const link = fgRef.current.d3Force('link');
        if (charge && link) {
          charge.strength(-400);
          link.distance(80);
          fgRef.current.d3ReheatSimulation();
        }
      }
    }, 500); // Wait for canvas to mount
    return () => clearTimeout(timer);
  }, [graphData]);

  // Custom drawing for nodes to make them look premium
  const drawNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || node.id;
    const fontSize = Math.max(12 / globalScale, 2);
    const radius = 6;
    const color = getNodeColor(node);

    // Inner circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();

    // Outer glow ring
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius + 2, 0, 2 * Math.PI, false);
    ctx.strokeStyle = `${color}40`; // 25% opacity
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Draw label when zoomed in or hovered/selected
    const isSelected = selectedNode?.id === node.id;
    if (globalScale > 1.5 || isSelected) {
      ctx.font = `${isSelected ? 'bold ' : ''}${fontSize}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isSelected ? '#ffffff' : 'rgba(255,255,255,0.8)';
      ctx.fillText(label, node.x, node.y + radius + fontSize + 2);
      
      // Draw selection ring
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius + 5, 0, 2 * Math.PI, false);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 2]);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
  }, [selectedNode]);

  return (
    <div className="sf-animate-in" style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 40px)" }}>
      <div className="sf-page-header" style={{ marginBottom: "16px" }}>
        <div>
          <h1 className="sf-page-title">🕸️ Cyber Relationship Explorer</h1>
          <p className="sf-page-subtitle">Interactive attack path visualization & threat actor mapping</p>
        </div>
        <div>
          <button className="sf-btn sf-btn-outline" onClick={loadData}>
            🔄 Refresh Graph
          </button>
        </div>
      </div>

      <div style={{ display: "flex", flex: 1, gap: "24px", minHeight: 0 }}>
        
        {/* Main Canvas Area */}
        <div 
          ref={containerRef} 
          className="sf-card" 
          style={{ 
            flex: 1, 
            overflow: "hidden", 
            position: "relative", 
            padding: 0,
            background: "radial-gradient(circle at center, #1e1b4b 0%, #0f1115 100%)" // Premium deep space background
          }}
        >
          {loading ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
              <div className="sf-loading-spinner" />
            </div>
          ) : (
            <ForceGraph2D
              ref={fgRef}
              graphData={graphData}
              width={dimensions.width}
              height={dimensions.height}
              nodeRelSize={6}
              linkColor={() => "rgba(255,255,255,0.15)"}
              linkWidth={1.5}
              linkDirectionalParticles={2}
              linkDirectionalParticleWidth={2}
              linkDirectionalParticleSpeed={0.005}
              linkDirectionalParticleColor={() => "rgba(255,255,255,0.8)"}
              onNodeClick={handleNodeClick}
              nodeCanvasObject={drawNode}
              backgroundColor="transparent"
            />
          )}
          
          {/* Overlay grid pattern to look like a tactical map */}
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none',
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
            backgroundSize: '40px 40px'
          }} />

          <div style={{ position: "absolute", bottom: "16px", left: "16px", background: "rgba(0,0,0,0.6)", padding: "12px", borderRadius: "8px", backdropFilter: "blur(4px)" }}>
            <h4 style={{ fontSize: "12px", color: "var(--sf-text-muted)", marginBottom: "8px", textTransform: "uppercase" }}>Legend</h4>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}><span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ef4444" }}></span> Alerts/Malicious IPs</div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}><span style={{ width: 10, height: 10, borderRadius: "50%", background: "#3b82f6" }}></span> Users</div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}><span style={{ width: 10, height: 10, borderRadius: "50%", background: "#8b5cf6" }}></span> Devices</div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}><span style={{ width: 10, height: 10, borderRadius: "50%", background: "#10b981" }}></span> MITRE / Intelligence</div>
            </div>
          </div>
        </div>

        {/* Sidebar Panel */}
        <div style={{ width: "320px", display: "flex", flexDirection: "column", gap: "24px", overflowY: "auto" }}>
          
          {/* Node Inspector */}
          <div className="sf-card" style={{ padding: "20px", flexShrink: 0 }}>
            <h3 style={{ fontSize: "15px", fontWeight: 600, borderBottom: "1px solid var(--sf-border)", paddingBottom: "12px", marginBottom: "16px" }}>
              🔍 Entity Inspector
            </h3>
            
            {selectedNode ? (
              <div className="sf-animate-in">
                <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
                  <div style={{ 
                    width: 40, height: 40, borderRadius: "8px", 
                    background: getNodeColor(selectedNode),
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: "20px"
                  }}>
                    {selectedNode.type === 'user' ? '👤' : 
                     selectedNode.type === 'device' ? '💻' : 
                     selectedNode.type === 'alert' ? '🚨' : '🎯'}
                  </div>
                  <div>
                    <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--sf-text-primary)" }}>{selectedNode.label}</div>
                    <div style={{ fontSize: "12px", color: "var(--sf-text-muted)", textTransform: "uppercase" }}>{selectedNode.type}</div>
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "13px" }}>
                  <div style={{ color: "var(--sf-text-secondary)", marginBottom: "4px" }}>Properties:</div>
                  {Object.entries(selectedNode.properties || {}).map(([k, v]) => (
                    <div key={k} style={{ background: "rgba(0,0,0,0.2)", padding: "8px", borderRadius: "4px" }}>
                      <span style={{ color: "var(--sf-text-muted)", marginRight: "8px", textTransform: "capitalize" }}>{k}:</span>
                      <span style={{ color: "var(--sf-text-primary)", wordBreak: "break-all", fontWeight: 500 }}>{String(v)}</span>
                    </div>
                  ))}
                  
                  {Object.keys(selectedNode.properties || {}).length === 0 && (
                    <div style={{ color: "var(--sf-text-muted)", fontStyle: "italic" }}>No additional properties.</div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{ color: "var(--sf-text-muted)", fontSize: "13px", textAlign: "center", padding: "30px 0" }}>
                <div style={{ fontSize: "32px", opacity: 0.2, marginBottom: "12px" }}>🖱️</div>
                Click any node in the graph to inspect its properties and relationships.
              </div>
            )}
          </div>

          {/* Graph Stats */}
          {stats && (
            <div className="sf-card" style={{ padding: "20px" }}>
              <h3 style={{ fontSize: "15px", fontWeight: 600, borderBottom: "1px solid var(--sf-border)", paddingBottom: "12px", marginBottom: "16px" }}>
                📊 Graph Topology
              </h3>
              
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "13px" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Total Nodes</span>
                  <span style={{ color: "var(--sf-primary)", fontWeight: 600 }}>{stats.total_nodes}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Total Edges</span>
                  <span style={{ color: "var(--sf-primary)", fontWeight: 600 }}>{stats.total_edges}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Graph Engine</span>
                  <span style={{ color: "var(--sf-text-primary)" }}>NetworkX (In-Memory)</span>
                </div>
                
                <div style={{ marginTop: "16px", color: "var(--sf-text-secondary)", fontSize: "12px", lineHeight: 1.5 }}>
                  The graph automatically maps attack paths and blast radius based on ingested alerts and incident data. 
                  Used by the AI agents for contextual investigations.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
