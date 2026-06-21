"use client";

import { useEffect, useState } from "react";
import { getRagStats, searchRag } from "@/lib/api";
import { Brain, Zap, Search } from "lucide-react";

interface KnowledgeResult {
  id: string;
  source: string;
  score: number;
  data: any;
}

const SOURCE_COLORS: Record<string, string> = {
  mitre: "#dc2626", cve: "#f97316", nist: "#6366f1",
  cis: "#3b82f6", playbooks: "#10b981", owasp: "#f59e0b",
  cisa_kev: "#ef4444", sans: "#22c55e", owasp_llm: "#06b6d4",
};

export default function KnowledgeExplorer() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [sourceFilter, setSourceFilter] = useState("");
  const [agenticMode, setAgenticMode] = useState(true);
  const [agenticMeta, setAgenticMeta] = useState<any>(null);

  useEffect(() => { loadStats(); }, []);

  async function loadStats() {
    try { setStats(await getRagStats()); } catch {}
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    setAgenticMeta(null);
    try {
      if (agenticMode) {
        const res = await fetch("http://localhost:8000/api/rag/agentic/search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, top_k: 10, include_context: false }),
        });
        const data = await res.json();
        setResults(data.results || []);
        setAgenticMeta({ domain: data.domain, agent: data.agent, confidence: data.confidence, priority_sources: data.priority_sources, sub_queries: data.sub_queries });
      } else {
        const data = await searchRag(query, sourceFilter);
        setResults(data.results || []);
      }
    } catch (e: any) {
      console.error(e);
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">Advanced RAG Explorer</h1>
          <p className="sf-page-subtitle">Hybrid Semantic + BM25 + Agentic retrieval across 9 security knowledge sources</p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Agentic Mode</span>
          <button onClick={() => setAgenticMode(!agenticMode)} style={{
            width: "44px", height: "24px", borderRadius: "12px", border: "none",
            background: agenticMode ? "#6366f1" : "rgba(255,255,255,0.1)", cursor: "pointer", position: "relative", transition: "background 0.2s",
          }}>
            <span style={{ position: "absolute", top: "3px", left: agenticMode ? "22px" : "3px", width: "18px", height: "18px", borderRadius: "50%", background: "white", transition: "left 0.2s" }} />
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: "24px" }}>
        <div>
          <form onSubmit={handleSearch} className="sf-card" style={{ padding: "20px", marginBottom: "16px" }}>
            <div style={{ display: "flex", gap: "12px", marginBottom: "12px" }}>
              <input type="text" className="sf-input" style={{ flex: 1 }}
                placeholder="e.g. CVE-2021-44228, brute force detection, NIST incident response..."
                value={query} onChange={(e) => setQuery(e.target.value)} />
              {!agenticMode && (
                <select className="sf-input" style={{ width: "160px" }} value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
                  <option value="">All Sources</option>
                  <option value="mitre">MITRE ATT&CK</option>
                  <option value="cve">CVE Database</option>
                  <option value="cisa_kev">CISA KEV</option>
                  <option value="nist">NIST CSF</option>
                  <option value="cis">CIS Controls</option>
                  <option value="owasp">OWASP Top 10</option>
                  <option value="owasp_llm">OWASP LLM</option>
                  <option value="sans">SANS</option>
                  <option value="playbooks">IR Playbooks</option>
                </select>
              )}
              <button type="submit" className="sf-btn sf-btn-primary" disabled={isSearching}>
                <Search size={14} /> {isSearching ? "Searching..." : agenticMode ? "Agentic Search" : "Search"}
              </button>
            </div>
            <div style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>
              {agenticMode ? "🤖 Agentic mode: AI routes to the best knowledge agent automatically" : "🔍 Standard hybrid search (Semantic + BM25 + RRF)"}
            </div>
          </form>

          {agenticMeta && (
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "16px", padding: "12px 16px", borderRadius: "8px", background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)" }}>
              <div style={{ fontSize: "12px", display: "flex", gap: "6px", alignItems: "center" }}>
                <Zap size={13} color="#6366f1" />
                <span style={{ color: "var(--sf-text-muted)" }}>Agent:</span>
                <span style={{ color: "#a5b4fc", fontWeight: 600 }}>{agenticMeta.agent?.replace(/_/g, " ")}</span>
              </div>
              <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Domain: <span style={{ color: "#a5b4fc", fontWeight: 600 }}>{agenticMeta.domain}</span></div>
              <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Confidence: <span style={{ color: "#10b981", fontWeight: 600 }}>{(agenticMeta.confidence * 100).toFixed(0)}%</span></div>
              <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Sources: <span style={{ color: "#a5b4fc" }}>{agenticMeta.priority_sources?.join(", ")}</span></div>
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {results.map((result, i) => (
              <div key={i} className="sf-card" style={{ padding: "18px", borderLeft: `4px solid ${SOURCE_COLORS[result.source] || "#6b7280"}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <span style={{ fontSize: "11px", fontWeight: 700, color: SOURCE_COLORS[result.source] || "#6b7280", textTransform: "uppercase", background: `${SOURCE_COLORS[result.source] || "#6b7280"}15`, padding: "2px 8px", borderRadius: "4px" }}>
                      {result.source}
                    </span>
                    <span style={{ color: "var(--sf-text-muted)", fontSize: "11px", fontFamily: "monospace" }}>{result.id}</span>
                  </div>
                  <div style={{ fontSize: "11px", background: "var(--sf-bg-elevated)", padding: "3px 8px", borderRadius: "4px" }}>
                    Score: {result.score.toFixed(3)}
                  </div>
                </div>
                <h3 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "8px" }}>
                  {result.data?.name || result.data?.title || result.data?.control || result.data?.id || "Document"}
                </h3>
                <p style={{ fontSize: "13px", color: "var(--sf-text-secondary)", lineHeight: 1.6, marginBottom: "10px" }}>
                  {(result.data?.description || result.data?.short_description || result.data?.content || "").substring(0, 250)}
                </p>
                <div style={{ display: "grid", gap: "6px", background: "rgba(0,0,0,0.1)", padding: "10px", borderRadius: "6px", fontSize: "12px" }}>
                  {result.data?.cvss && <div><strong style={{ color: "var(--sf-text-primary)" }}>CVSS:</strong> <span style={{ color: "#dc2626", fontWeight: 700 }}>{result.data.cvss}</span></div>}
                  {result.data?.tactic && <div><strong style={{ color: "var(--sf-text-primary)" }}>Tactic:</strong> {result.data.tactic}</div>}
                  {result.data?.due_date && <div><strong style={{ color: "#dc2626" }}>CISA Deadline:</strong> <span style={{ color: "#dc2626" }}>{result.data.due_date}</span></div>}
                  {result.data?.remediation && <div><strong style={{ color: "var(--sf-text-primary)" }}>Remediation:</strong> {String(result.data.remediation).substring(0, 150)}</div>}
                  {result.data?.detection && <div><strong style={{ color: "var(--sf-text-primary)" }}>Detection:</strong> {String(result.data.detection).substring(0, 150)}</div>}
                </div>
              </div>
            ))}
            {results.length === 0 && !isSearching && query && (
              <div style={{ textAlign: "center", padding: "40px", color: "var(--sf-text-muted)" }}>No results for "{query}".</div>
            )}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className="sf-card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "13px", fontWeight: 600, marginBottom: "16px" }}>RAG Engine</h3>
            {stats ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "12px" }}>
                {[
                  { label: "Status", value: stats.loaded ? "Online" : "Offline", color: stats.loaded ? "#10b981" : "#dc2626" },
                  { label: "Documents", value: stats.total_documents },
                  { label: "Embedding", value: "MiniLM-L6-v2" },
                  { label: "Vector Store", value: "ChromaDB" },
                  { label: "Hybrid Search", value: "RRF Enabled" },
                  { label: "Agentic Router", value: "Active" },
                ].map((row) => (
                  <div key={row.label} style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "var(--sf-text-muted)" }}>{row.label}</span>
                    <span style={{ color: (row as any).color || "var(--sf-text-primary)", fontWeight: 600 }}>{row.value}</span>
                  </div>
                ))}
              </div>
            ) : <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Loading...</div>}
          </div>

          <div className="sf-card" style={{ padding: "20px" }}>
            <h3 style={{ fontSize: "13px", fontWeight: 600, marginBottom: "12px" }}>Knowledge Sources (9)</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {Object.entries(SOURCE_COLORS).map(([src, color]) => (
                <div key={src} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px" }}>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: color, flexShrink: 0 }} />
                  <span style={{ color: "var(--sf-text-secondary)", textTransform: "uppercase", fontWeight: 600 }}>{src.replace(/_/g, " ")}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
