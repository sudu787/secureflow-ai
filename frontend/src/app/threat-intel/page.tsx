"use client";

import { useEffect, useState, useCallback } from "react";
import { searchRag } from "@/lib/api";
import { Search, AlertTriangle, ShieldAlert, ExternalLink, RefreshCw, Zap } from "lucide-react";

const SOURCE_CONFIG: Record<string, { label: string; color: string; description: string }> = {
  cisa_kev: { label: "CISA KEV", color: "#dc2626", description: "Known Exploited Vulnerabilities" },
  cve: { label: "CVE Database", color: "#f97316", description: "Common Vulnerabilities" },
  mitre: { label: "MITRE ATT&CK", color: "#8b5cf6", description: "Threat Techniques" },
  owasp: { label: "OWASP Top 10", color: "#3b82f6", description: "Web Security" },
  owasp_llm: { label: "OWASP LLM", color: "#06b6d4", description: "AI Security" },
  sans: { label: "SANS", color: "#10b981", description: "Security Guidance" },
  nist: { label: "NIST", color: "#6366f1", description: "Compliance Framework" },
  cis: { label: "CIS Controls", color: "#f59e0b", description: "Security Controls" },
  playbooks: { label: "Playbooks", color: "#84cc16", description: "IR Procedures" },
};

const QUICK_SEARCHES = [
  { label: "Log4Shell CVE-2021-44228", query: "CVE-2021-44228 Log4Shell exploitation" },
  { label: "Ransomware response", query: "ransomware containment incident response playbook" },
  { label: "Prompt Injection", query: "LLM prompt injection attack defense OWASP" },
  { label: "CISA Active Exploits", query: "CISA known exploited vulnerability 2024" },
  { label: "Lateral Movement", query: "lateral movement detection MITRE ATT&CK" },
  { label: "Brute Force defense", query: "brute force attack detection prevention" },
];

export default function ThreatIntelPortal() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [sourceFilter, setSourceFilter] = useState("");
  const [agenticMode, setAgenticMode] = useState(true);
  const [agenticMeta, setAgenticMeta] = useState<any>(null);

  const doSearch = useCallback(async (q: string, src: string = "") => {
    if (!q.trim()) return;
    setSearching(true);
    setAgenticMeta(null);
    try {
      if (agenticMode) {
        // Use Agentic RAG router
        const res = await fetch("http://localhost:8000/api/rag/agentic/search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q, top_k: 10, include_context: false }),
        });
        const data = await res.json();
        setResults(data.results || []);
        setAgenticMeta({
          domain: data.domain,
          agent: data.agent,
          confidence: data.confidence,
          priority_sources: data.priority_sources,
          sub_queries: data.sub_queries,
        });
      } else {
        const data = await searchRag(q, src || undefined);
        setResults(data.results || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  }, [agenticMode]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    doSearch(query, sourceFilter);
  };

  const handleQuick = (q: string) => {
    setQuery(q);
    doSearch(q, "");
  };

  const getSourceCfg = (source: string) =>
    SOURCE_CONFIG[source] || { label: source?.toUpperCase(), color: "#6b7280", description: "" };

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">Threat Intelligence Portal</h1>
          <p className="sf-page-subtitle">Unified search across MITRE ATT&CK • CISA KEV • OWASP • SANS • NIST • CVE</p>
        </div>
        {/* Agentic Mode Toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>Agentic RAG</span>
          <button
            onClick={() => setAgenticMode(!agenticMode)}
            style={{
              width: "44px", height: "24px", borderRadius: "12px", border: "none",
              background: agenticMode ? "#6366f1" : "rgba(255,255,255,0.1)",
              cursor: "pointer", position: "relative", transition: "background 0.2s",
            }}
          >
            <span style={{
              position: "absolute", top: "3px",
              left: agenticMode ? "22px" : "3px",
              width: "18px", height: "18px", borderRadius: "50%",
              background: "white", transition: "left 0.2s",
            }} />
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="sf-card" style={{ padding: "20px", marginBottom: "20px" }}>
        <div style={{ display: "flex", gap: "12px", marginBottom: "12px" }}>
          <input
            className="sf-input"
            style={{ flex: 1 }}
            placeholder="Search CVEs, techniques, compliance controls, threat actors..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {!agenticMode && (
            <select className="sf-input" style={{ width: "160px" }} value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
              <option value="">All Sources</option>
              {Object.entries(SOURCE_CONFIG).map(([id, cfg]) => (
                <option key={id} value={id}>{cfg.label}</option>
              ))}
            </select>
          )}
          <button className="sf-btn sf-btn-primary" type="submit" disabled={searching}>
            <Search size={14} /> {searching ? "Searching..." : agenticMode ? "Agentic Search" : "Search"}
          </button>
        </div>

        {/* Quick searches */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
          <span style={{ fontSize: "11px", color: "var(--sf-text-muted)", alignSelf: "center" }}>Quick:</span>
          {QUICK_SEARCHES.map((qs) => (
            <button
              key={qs.label} type="button"
              onClick={() => handleQuick(qs.query)}
              style={{
                padding: "4px 10px", borderRadius: "20px", fontSize: "11px", cursor: "pointer",
                background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)",
                color: "#a5b4fc", transition: "all 0.15s",
              }}
            >
              {qs.label}
            </button>
          ))}
        </div>
      </form>

      {/* Agentic Metadata Badge */}
      {agenticMeta && (
        <div style={{
          display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "16px",
          padding: "12px 16px", borderRadius: "8px",
          background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px" }}>
            <Zap size={14} color="#6366f1" />
            <span style={{ color: "var(--sf-text-muted)" }}>Agent:</span>
            <span style={{ color: "#a5b4fc", fontWeight: 600 }}>{agenticMeta.agent?.replace(/_/g, " ")}</span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>
            Domain: <span style={{ color: "#a5b4fc", fontWeight: 600 }}>{agenticMeta.domain}</span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>
            Confidence: <span style={{ color: "#10b981", fontWeight: 600 }}>{(agenticMeta.confidence * 100).toFixed(0)}%</span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>
            Sources: <span style={{ color: "#a5b4fc" }}>{agenticMeta.priority_sources?.join(", ")}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {searching ? (
        <div style={{ textAlign: "center", padding: "60px" }}>
          <div className="sf-loading-spinner" style={{ margin: "0 auto" }} />
          <div style={{ marginTop: "16px", fontSize: "13px", color: "var(--sf-text-muted)" }}>
            {agenticMode ? "Agentic RAG routing and retrieving..." : "Searching knowledge base..."}
          </div>
        </div>
      ) : results.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ fontSize: "12px", color: "var(--sf-text-muted)" }}>{results.length} results</div>
          {results.map((result: any, i: number) => {
            const cfg = getSourceCfg(result.source);
            const data = result.data || {};
            return (
              <div key={i} className="sf-card" style={{ padding: "20px", borderLeft: `4px solid ${cfg.color}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
                  <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                    <span style={{
                      fontSize: "11px", fontWeight: 700, textTransform: "uppercase",
                      color: cfg.color, background: `${cfg.color}15`,
                      padding: "2px 8px", borderRadius: "4px",
                    }}>
                      {cfg.label}
                    </span>
                    <span style={{ fontSize: "11px", fontFamily: "monospace", color: "var(--sf-text-muted)" }}>
                      {data.id || data.cve_id || result.id?.split("-").slice(1).join("-")}
                    </span>
                    {data.known_ransomware === true && (
                      <span style={{ fontSize: "10px", fontWeight: 700, color: "#dc2626", background: "rgba(220,38,38,0.1)", padding: "2px 8px", borderRadius: "4px" }}>
                        RANSOMWARE
                      </span>
                    )}
                    {data.cvss >= 9 && (
                      <span style={{ fontSize: "10px", fontWeight: 700, color: "#dc2626", background: "rgba(220,38,38,0.1)", padding: "2px 8px", borderRadius: "4px" }}>
                        CVSS {data.cvss}
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>
                    Relevance: {(result.score * 100).toFixed(1)}%
                  </span>
                </div>

                <h3 style={{ fontSize: "15px", fontWeight: 700, marginBottom: "8px" }}>
                  {data.name || data.title || data.control || "Document"}
                </h3>

                <p style={{ fontSize: "13px", color: "var(--sf-text-secondary)", lineHeight: 1.6, marginBottom: "12px" }}>
                  {(data.description || data.short_description || data.content || "").substring(0, 300)}
                  {(data.description || data.content || "").length > 300 ? "..." : ""}
                </p>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "8px" }}>
                  {data.remediation && (
                    <div style={{ background: "rgba(16,185,129,0.06)", borderRadius: "6px", padding: "10px" }}>
                      <div style={{ fontSize: "10px", fontWeight: 700, color: "#10b981", marginBottom: "4px", textTransform: "uppercase" }}>Remediation</div>
                      <div style={{ fontSize: "12px", color: "var(--sf-text-secondary)" }}>{String(data.remediation).substring(0, 150)}</div>
                    </div>
                  )}
                  {data.detection && (
                    <div style={{ background: "rgba(59,130,246,0.06)", borderRadius: "6px", padding: "10px" }}>
                      <div style={{ fontSize: "10px", fontWeight: 700, color: "#3b82f6", marginBottom: "4px", textTransform: "uppercase" }}>Detection</div>
                      <div style={{ fontSize: "12px", color: "var(--sf-text-secondary)" }}>{String(data.detection).substring(0, 150)}</div>
                    </div>
                  )}
                  {data.due_date && (
                    <div style={{ background: "rgba(220,38,38,0.06)", borderRadius: "6px", padding: "10px" }}>
                      <div style={{ fontSize: "10px", fontWeight: 700, color: "#dc2626", marginBottom: "4px", textTransform: "uppercase" }}>CISA Patch Deadline</div>
                      <div style={{ fontSize: "12px", color: "#dc2626", fontWeight: 600 }}>{data.due_date}</div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : query ? (
        <div style={{ textAlign: "center", padding: "60px", color: "var(--sf-text-muted)" }}>
          <ShieldAlert size={48} style={{ opacity: 0.2, margin: "0 auto 16px" }} />
          <p>No results found. Try different keywords.</p>
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: "80px", color: "var(--sf-text-muted)" }}>
          <Search size={48} style={{ opacity: 0.15, margin: "0 auto 16px" }} />
          <div style={{ fontSize: "16px", fontWeight: 600, marginBottom: "8px" }}>Unified Threat Intelligence Search</div>
          <div style={{ fontSize: "13px", maxWidth: "500px", margin: "0 auto", lineHeight: 1.6 }}>
            Search across 9 security knowledge sources. In Agentic mode, the AI automatically routes your query to the most relevant intelligence agent.
          </div>
        </div>
      )}
    </div>
  );
}
