"use client";

import { useEffect, useState, useCallback } from "react";
import { searchRag } from "@/lib/api";
import { Shield, Search, ExternalLink, ChevronDown, ChevronRight, RefreshCw } from "lucide-react";

const TACTICS = [
  "Reconnaissance", "Resource Development", "Initial Access", "Execution",
  "Persistence", "Privilege Escalation", "Defense Evasion", "Credential Access",
  "Discovery", "Lateral Movement", "Collection", "Command and Control",
  "Exfiltration", "Impact",
];

const TACTIC_COLORS: Record<string, string> = {
  "Reconnaissance": "#6366f1",
  "Resource Development": "#8b5cf6",
  "Initial Access": "#dc2626",
  "Execution": "#ef4444",
  "Persistence": "#f97316",
  "Privilege Escalation": "#fb923c",
  "Defense Evasion": "#eab308",
  "Credential Access": "#f59e0b",
  "Discovery": "#10b981",
  "Lateral Movement": "#06b6d4",
  "Collection": "#3b82f6",
  "Command and Control": "#6366f1",
  "Exfiltration": "#8b5cf6",
  "Impact": "#dc2626",
};

export default function MITREExplorer() {
  const [selectedTactic, setSelectedTactic] = useState<string | null>(null);
  const [techniques, setTechniques] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTechnique, setSelectedTechnique] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  const loadTactic = useCallback(async (tactic: string) => {
    setLoading(true);
    setSelectedTactic(tactic);
    setSelectedTechnique(null);
    try {
      const data = await searchRag(`MITRE ATT&CK ${tactic} techniques`, "mitre");
      setTechniques(data.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const data = await searchRag(searchQuery, "mitre");
      setSearchResults(data.results || []);
      setSelectedTactic(null);
      setTechniques([]);
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  const displayResults = searchResults.length > 0 ? searchResults : techniques;

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">MITRE ATT&CK Explorer</h1>
          <p className="sf-page-subtitle">Browse 14 tactics • 200+ techniques • Detection & mitigation guidance</p>
        </div>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSearch} style={{ marginBottom: "24px", display: "flex", gap: "12px" }}>
        <input
          className="sf-input"
          style={{ flex: 1 }}
          placeholder="Search techniques, tactics, or threat actors... (e.g. T1190, credential dumping, lateral movement)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button className="sf-btn sf-btn-primary" type="submit" disabled={searching}>
          <Search size={14} /> {searching ? "Searching..." : "Search MITRE"}
        </button>
        {searchResults.length > 0 && (
          <button className="sf-btn sf-btn-secondary" type="button" onClick={() => { setSearchResults([]); setSearchQuery(""); }}>
            Clear
          </button>
        )}
      </form>

      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: "20px" }}>
        {/* Tactic Navigator */}
        <div className="sf-card" style={{ padding: "16px", height: "fit-content" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--sf-text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "12px" }}>
            ATT&CK Tactics
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {TACTICS.map((tactic) => (
              <button
                key={tactic}
                onClick={() => loadTactic(tactic)}
                style={{
                  padding: "8px 10px",
                  borderRadius: "6px",
                  border: "none",
                  background: selectedTactic === tactic ? `${TACTIC_COLORS[tactic]}20` : "transparent",
                  borderLeft: selectedTactic === tactic ? `3px solid ${TACTIC_COLORS[tactic]}` : "3px solid transparent",
                  color: selectedTactic === tactic ? TACTIC_COLORS[tactic] : "var(--sf-text-secondary)",
                  cursor: "pointer",
                  textAlign: "left",
                  fontSize: "12px",
                  fontWeight: selectedTactic === tactic ? 600 : 400,
                  transition: "all 0.15s ease",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: TACTIC_COLORS[tactic], flexShrink: 0 }} />
                {tactic}
              </button>
            ))}
          </div>
        </div>

        {/* Main content */}
        <div>
          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", padding: "60px" }}>
              <div className="sf-loading-spinner" />
            </div>
          ) : selectedTechnique ? (
            /* Technique Detail View */
            <div className="sf-card" style={{ padding: "28px" }}>
              <button
                onClick={() => setSelectedTechnique(null)}
                style={{ background: "none", border: "none", color: "var(--sf-accent)", cursor: "pointer", fontSize: "13px", marginBottom: "20px", display: "flex", alignItems: "center", gap: "6px" }}
              >
                ← Back to techniques
              </button>

              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
                <span style={{
                  padding: "4px 10px", borderRadius: "6px", fontSize: "12px", fontWeight: 700,
                  background: `${TACTIC_COLORS[selectedTechnique.data?.tactic] || "#6366f1"}20`,
                  color: TACTIC_COLORS[selectedTechnique.data?.tactic] || "#6366f1",
                }}>
                  {selectedTechnique.data?.tactic || "ATT&CK"}
                </span>
                <span style={{ fontFamily: "monospace", fontSize: "13px", color: "var(--sf-text-muted)" }}>
                  {selectedTechnique.id?.replace(/^mitre-/, "")}
                </span>
              </div>

              <h2 style={{ fontSize: "20px", fontWeight: 700, marginBottom: "16px" }}>
                {selectedTechnique.data?.name || "Technique"}
              </h2>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
                {[
                  { label: "MITRE ID", value: selectedTechnique.data?.id || selectedTechnique.id?.replace("mitre-", "") },
                  { label: "Tactic", value: selectedTechnique.data?.tactic },
                  { label: "Platforms", value: selectedTechnique.data?.platforms?.join(", ") },
                  { label: "Data Sources", value: selectedTechnique.data?.data_sources?.join(", ") },
                ].filter(f => f.value).map((field) => (
                  <div key={field.label} style={{ background: "rgba(255,255,255,0.03)", borderRadius: "8px", padding: "12px" }}>
                    <div style={{ fontSize: "11px", color: "var(--sf-text-muted)", marginBottom: "4px", textTransform: "uppercase" }}>{field.label}</div>
                    <div style={{ fontSize: "13px", fontWeight: 600 }}>{field.value}</div>
                  </div>
                ))}
              </div>

              {selectedTechnique.data?.description && (
                <div style={{ marginBottom: "20px" }}>
                  <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "8px", color: "var(--sf-text-primary)" }}>Description</div>
                  <p style={{ fontSize: "13px", lineHeight: 1.7, color: "var(--sf-text-secondary)" }}>{selectedTechnique.data.description}</p>
                </div>
              )}

              {selectedTechnique.data?.detection && (
                <div style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)", borderRadius: "8px", padding: "16px", marginBottom: "16px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 700, color: "#10b981", marginBottom: "8px", textTransform: "uppercase" }}>Detection</div>
                  <p style={{ fontSize: "13px", lineHeight: 1.6, color: "var(--sf-text-secondary)" }}>{selectedTechnique.data.detection}</p>
                </div>
              )}

              {selectedTechnique.data?.remediation && (
                <div style={{ background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)", borderRadius: "8px", padding: "16px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 700, color: "#3b82f6", marginBottom: "8px", textTransform: "uppercase" }}>Remediation / Mitigations</div>
                  <p style={{ fontSize: "13px", lineHeight: 1.6, color: "var(--sf-text-secondary)" }}>{selectedTechnique.data.remediation}</p>
                </div>
              )}
            </div>
          ) : displayResults.length > 0 ? (
            /* Results Grid */
            <div>
              <div style={{ fontSize: "13px", color: "var(--sf-text-muted)", marginBottom: "16px" }}>
                {searchResults.length > 0
                  ? `${searchResults.length} results for "${searchQuery}"`
                  : `${techniques.length} techniques in ${selectedTactic}`
                }
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px" }}>
                {displayResults.map((result: any, i: number) => (
                  <div
                    key={i}
                    className="sf-card"
                    onClick={() => setSelectedTechnique(result)}
                    style={{ padding: "16px", cursor: "pointer", transition: "all 0.15s ease", borderColor: "var(--sf-border)" }}
                    onMouseEnter={(e) => (e.currentTarget.style.borderColor = TACTIC_COLORS[result.data?.tactic] || "#6366f1")}
                    onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--sf-border)")}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
                      <span style={{ fontFamily: "monospace", fontSize: "11px", color: "var(--sf-text-muted)" }}>
                        {result.data?.id || result.id?.replace("mitre-", "")}
                      </span>
                      <span style={{ fontSize: "10px", fontWeight: 600, color: "var(--sf-accent)", background: "rgba(99,102,241,0.1)", padding: "2px 6px", borderRadius: "4px" }}>
                        Score: {result.score?.toFixed(3)}
                      </span>
                    </div>
                    <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "6px" }}>
                      {result.data?.name || "Technique"}
                    </div>
                    {result.data?.tactic && (
                      <div style={{ fontSize: "11px", color: TACTIC_COLORS[result.data.tactic] || "var(--sf-text-muted)", fontWeight: 600 }}>
                        {result.data.tactic}
                      </div>
                    )}
                    <p style={{ fontSize: "11px", color: "var(--sf-text-muted)", marginTop: "8px", lineHeight: 1.5 }}>
                      {String(result.data?.description || "").substring(0, 100)}...
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Empty State */
            <div style={{ textAlign: "center", padding: "80px", color: "var(--sf-text-muted)" }}>
              <Shield size={48} style={{ opacity: 0.2, margin: "0 auto 16px" }} />
              <div style={{ fontSize: "16px", fontWeight: 600, marginBottom: "8px" }}>Select a Tactic</div>
              <div style={{ fontSize: "13px" }}>Choose a tactic from the left to explore ATT&CK techniques, or use the search bar above.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
