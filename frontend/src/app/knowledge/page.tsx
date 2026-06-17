"use client";

import { useEffect, useState } from "react";
import { getRagStats, searchRag } from "@/lib/api";

interface KnowledgeResult {
  id: string;
  source: string;
  score: number;
  data: any;
}

export default function KnowledgeExplorer() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [sourceFilter, setSourceFilter] = useState("");

  useEffect(() => {
    loadStats();
  }, []);

  async function loadStats() {
    try {
      const data = await getRagStats();
      setStats(data);
    } catch (e) {
      console.error("Failed to load RAG stats", e);
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      const data = await searchRag(query, sourceFilter);
      setResults(data.results || []);
    } catch (e: any) {
      alert("Search failed: " + e.message);
    } finally {
      setIsSearching(false);
    }
  }

  const getSourceColor = (source: string) => {
    switch(source) {
      case 'mitre': return 'var(--sf-danger)';
      case 'cve': return 'var(--sf-warning)';
      case 'nist':
      case 'cis': return 'var(--sf-primary)';
      case 'playbooks': return 'var(--sf-success)';
      default: return 'var(--sf-text-secondary)';
    }
  };

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">🧠 Advanced RAG Explorer</h1>
          <p className="sf-page-subtitle">Search the cybersecurity knowledge base using Semantic + BM25 Hybrid Retrieval</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "24px" }}>
        {/* Main Search Area */}
        <div>
          <form onSubmit={handleSearch} className="sf-card" style={{ padding: "24px", marginBottom: "24px" }}>
            <div style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
              <input
                type="text"
                className="sf-input"
                style={{ flex: 1 }}
                placeholder="Search for threats, vulnerabilities, compliance controls..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <select 
                className="sf-input"
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
              >
                <option value="">All Sources</option>
                <option value="mitre">MITRE ATT&CK</option>
                <option value="cve">CVE Database</option>
                <option value="nist">NIST CSF</option>
                <option value="cis">CIS Controls</option>
                <option value="playbooks">IR Playbooks</option>
              </select>
              <button type="submit" className="sf-btn sf-btn-primary" disabled={isSearching}>
                {isSearching ? "Searching..." : "🔍 Search"}
              </button>
            </div>
          </form>

          {/* Results Area */}
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {results.map((result, i) => (
              <div key={i} className="sf-card" style={{ padding: "20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                  <div>
                    <span 
                      style={{ 
                        fontSize: "12px", fontWeight: 700, 
                        color: getSourceColor(result.source), 
                        textTransform: "uppercase",
                        marginRight: "8px"
                      }}
                    >
                      {result.source}
                    </span>
                    <span style={{ color: "var(--sf-text-muted)", fontSize: "13px" }}>ID: {result.id}</span>
                  </div>
                  <div style={{ fontSize: "12px", background: "var(--sf-bg-elevated)", padding: "4px 8px", borderRadius: "4px" }}>
                    Score: {result.score.toFixed(3)}
                  </div>
                </div>

                <h3 style={{ fontSize: "16px", fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: "8px" }}>
                  {result.data.name || result.data.control || result.data.id || "Untitled Document"}
                </h3>
                
                <p style={{ fontSize: "14px", color: "var(--sf-text-secondary)", lineHeight: 1.6, marginBottom: "12px" }}>
                  {result.data.description}
                </p>

                {/* Specific fields based on source */}
                <div style={{ fontSize: "13px", display: "grid", gap: "8px", background: "rgba(0,0,0,0.1)", padding: "12px", borderRadius: "8px" }}>
                  {result.data.cvss && (
                    <div><strong style={{color:"var(--sf-text-primary)"}}>CVSS:</strong> <span style={{color:"var(--sf-danger)"}}>{result.data.cvss}</span></div>
                  )}
                  {result.data.tactic && (
                    <div><strong style={{color:"var(--sf-text-primary)"}}>Tactic:</strong> {result.data.tactic}</div>
                  )}
                  {result.data.remediation && (
                    <div><strong style={{color:"var(--sf-text-primary)"}}>Remediation:</strong> {result.data.remediation}</div>
                  )}
                  {result.data.implementation && (
                    <div><strong style={{color:"var(--sf-text-primary)"}}>Implementation:</strong> {result.data.implementation}</div>
                  )}
                  {result.data.detection && (
                    <div><strong style={{color:"var(--sf-text-primary)"}}>Detection:</strong> {result.data.detection}</div>
                  )}
                </div>
              </div>
            ))}

            {results.length === 0 && !isSearching && query && (
              <div style={{ textAlign: "center", padding: "40px", color: "var(--sf-text-muted)" }}>
                No results found for "{query}". Try different keywords.
              </div>
            )}
          </div>
        </div>

        {/* Sidebar / Engine Stats */}
        <div>
          <div className="sf-card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "var(--sf-text-primary)", marginBottom: "16px" }}>
              RAG Engine Status
            </h3>
            
            {stats ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "13px" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Status</span>
                  <span style={{ color: stats.loaded ? "var(--sf-success)" : "var(--sf-danger)", fontWeight: 600 }}>
                    {stats.loaded ? "🟢 Online" : "🔴 Offline"}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Documents Indexed</span>
                  <span style={{ color: "var(--sf-text-primary)" }}>{stats.total_documents}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Embedding Model</span>
                  <span style={{ color: "var(--sf-text-primary)" }}>{stats.embedding_model}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Vector Store</span>
                  <span style={{ color: "var(--sf-text-primary)" }}>{stats.vector_store}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "var(--sf-text-muted)" }}>Hybrid Search</span>
                  <span style={{ color: "var(--sf-text-primary)" }}>{stats.hybrid_search ? "Enabled" : "Disabled"}</span>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: "13px", color: "var(--sf-text-muted)" }}>Loading stats...</div>
            )}

            <div style={{ marginTop: "24px", paddingTop: "16px", borderTop: "1px solid var(--sf-border)" }}>
              <div style={{ fontSize: "12px", color: "var(--sf-text-secondary)", lineHeight: 1.5 }}>
                <strong style={{ color: "var(--sf-text-primary)", display: "block", marginBottom: "8px" }}>How it works:</strong>
                Queries are encoded using <em>SentenceTransformers</em> and matched against ChromaDB vectors. Simultaneously, a BM25 algorithm performs keyword matching. Results are combined using Reciprocal Rank Fusion.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
