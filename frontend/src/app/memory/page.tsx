"use client";

import { useState, useEffect } from "react";
import { BrainCircuit, Search, Database, RefreshCw, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";

export default function MemoryCenter() {
  const [memories, setMemories] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [consolidating, setConsolidating] = useState(false);

  useEffect(() => {
    fetchMemories();
  }, []);

  const fetchMemories = async () => {
    try {
      const data = await api.get("/memory/recent?limit=10");
      setMemories(data || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery) return;
    setLoading(true);
    try {
      const data = await api.get(`/memory/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchResults(data.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleConsolidate = async () => {
    setConsolidating(true);
    try {
      // Hardcode an alert ID that likely exists, e.g., 1
      await api.post("/memory/consolidate", { alert_id: 1 });
      await fetchMemories();
      alert("Nightly consolidation complete. Alert #1 processed into Incident Memory.");
    } catch (e) {
      alert("Failed to consolidate memory. Note: Alert #1 might not exist in your local DB yet.");
      console.error(e);
    } finally {
      setConsolidating(false);
    }
  };

  return (
    <div className="sf-container">
      <div className="sf-header">
        <div>
          <h1 className="sf-title" style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <BrainCircuit size={28} style={{ color: "var(--sf-accent)" }} />
            Cyber Memory Center
          </h1>
          <p className="sf-subtitle">Long-term organizational cyber intelligence and incident memory</p>
        </div>
        <button 
          className="sf-button" 
          onClick={handleConsolidate} 
          disabled={consolidating}
        >
          {consolidating ? <RefreshCw size={16} className="spin" /> : <Database size={16} />}
          Simulate Nightly Consolidation
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        
        {/* Left Col: Memory Explorer */}
        <div className="sf-card">
          <h2 style={{ fontSize: "16px", marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Search size={18} /> Memory Explorer (Semantic Recall)
          </h2>
          
          <form onSubmit={handleSearch} style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
            <input 
              type="text" 
              className="sf-input" 
              style={{ flex: 1 }} 
              placeholder="E.g., 'Ransomware mitigation', 'Suspicious login'" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button className="sf-button sf-button-primary" type="submit" disabled={loading}>
              Search Brain
            </button>
          </form>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {searchResults.map((res, i) => (
              <div key={i} style={{ padding: "16px", background: "var(--sf-surface-hover)", borderRadius: "8px", borderLeft: "4px solid var(--sf-accent)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <h3 style={{ fontSize: "14px", fontWeight: 600 }}>{res.data.title || res.id}</h3>
                  <span className="sf-badge sf-badge-info">Match: {(res.score * 100).toFixed(1)}%</span>
                </div>
                <p style={{ fontSize: "12px", color: "var(--sf-text-secondary)", marginBottom: "8px", lineHeight: 1.5 }}>
                  {res.data.content}
                </p>
                {res.data.original_alert_id && (
                  <div style={{ fontSize: "11px", color: "var(--sf-text-muted)", display: "flex", gap: "12px" }}>
                    <span>Alert ID: #{res.data.original_alert_id}</span>
                  </div>
                )}
              </div>
            ))}
            {searchResults.length === 0 && !loading && (
              <div style={{ textAlign: "center", padding: "40px", color: "var(--sf-text-muted)" }}>
                <BrainCircuit size={40} style={{ opacity: 0.2, margin: "0 auto 12px auto" }} />
                <p>Search the AI's long-term memory.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Recent Consolidations */}
        <div className="sf-card">
          <h2 style={{ fontSize: "16px", marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Database size={18} /> Recent Consolidations (Incident Memory)
          </h2>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {memories.map((m, i) => (
              <div key={m.id} style={{ padding: "16px", border: "1px solid var(--sf-border)", borderRadius: "8px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--sf-text-primary)" }}>
                    {m.title}
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>
                    {new Date(m.created_at).toLocaleString()}
                  </div>
                </div>
                <div style={{ fontSize: "13px", color: "var(--sf-text-secondary)", marginBottom: "12px" }}>
                  <strong>Root Cause:</strong> {m.root_cause_summary}
                </div>
                <div style={{ fontSize: "13px", color: "var(--sf-text-secondary)", marginBottom: "12px" }}>
                  <strong>Mitigation:</strong> {m.mitigation_applied}
                </div>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  <span className="sf-badge" style={{ background: "var(--sf-surface)", border: "1px solid var(--sf-border)" }}>
                    Vector ID: {m.vector_id.substring(0, 20)}...
                  </span>
                  <span className="sf-badge" style={{ background: "var(--sf-surface)", border: "1px solid var(--sf-border)" }}>
                    Source Alert: #{m.original_alert_id}
                  </span>
                </div>
              </div>
            ))}
            {memories.length === 0 && (
              <div style={{ padding: "20px", textAlign: "center", color: "var(--sf-text-muted)", border: "1px dashed var(--sf-border)", borderRadius: "8px" }}>
                No recent memories. Click "Simulate Nightly Consolidation" to generate memories from past alerts.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
