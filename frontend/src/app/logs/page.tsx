"use client";

import { useEffect, useState } from "react";
import { getEvents } from "@/lib/api";

export default function LogsPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState<any>(null);

  useEffect(() => { loadEvents(); }, []);

  async function loadEvents() {
    try { setEvents(await getEvents({ limit: 100 })); } catch {}
  }

  const filtered = filter === "all" ? events : events.filter(e => e.source_type === filter);
  const sourceIcons: Record<string, string> = {
    linux: "🐧", windows: "🪟", web: "🌐", network: "📡", cloud: "☁️"
  };

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">📋 Log Viewer</h1>
          <p className="sf-page-subtitle">{events.length} events ingested • Normalized & enriched</p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          {["all", "linux", "windows", "network", "web", "cloud"].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={`sf-btn sf-btn-sm ${filter === f ? "sf-btn-primary" : "sf-btn-secondary"}`}>
              {f === "all" ? "All" : `${sourceIcons[f] || ""} ${f}`}
            </button>
          ))}
        </div>
      </div>

      <div className="sf-card" style={{ overflow: "auto", maxHeight: "calc(100vh - 160px)" }}>
        {filtered.length === 0 ? (
          <div style={{ textAlign: "center", padding: "60px", color: "var(--sf-text-muted)" }}>
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>📋</div>
            <div style={{ fontSize: "16px", fontWeight: 600 }}>No log events</div>
            <div style={{ fontSize: "13px", marginTop: "8px" }}>Run demo scenarios to generate log events</div>
          </div>
        ) : (
          <table className="sf-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Action</th>
                <th>Severity</th>
                <th>Source IP</th>
                <th>User</th>
                <th>MITRE</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(e => (
                <tr key={e.id} onClick={() => setSelected(selected?.id === e.id ? null : e)}>
                  <td>
                    <span style={{ marginRight: "6px" }}>{sourceIcons[e.source_type] || "📄"}</span>
                    <span style={{ fontSize: "12px" }}>{e.source_name}</span>
                  </td>
                  <td style={{ fontFamily: "monospace", fontSize: "12px", color: "var(--sf-text-primary)" }}>{e.action || "—"}</td>
                  <td><span className={`sf-badge ${e.severity}`}>{e.severity}</span></td>
                  <td style={{ fontFamily: "monospace", fontSize: "12px" }}>{e.source_ip || "—"}</td>
                  <td style={{ fontSize: "12px" }}>{e.username || "—"}</td>
                  <td style={{ fontFamily: "monospace", fontSize: "11px", color: "var(--sf-accent-light)" }}>{e.mitre_technique || "—"}</td>
                  <td style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>
                    {e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* Raw Log Viewer */}
        {selected && (
          <div className="sf-animate-in" style={{
            marginTop: "16px", padding: "16px", borderRadius: "10px",
            background: "rgba(0,0,0,0.3)", border: "1px solid var(--sf-border)",
          }}>
            <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--sf-accent-light)", marginBottom: "8px" }}>
              Raw Log — Event #{selected.id}
            </div>
            <pre style={{ fontSize: "11px", color: "var(--sf-text-secondary)", whiteSpace: "pre-wrap", wordBreak: "break-all", margin: 0 }}>
              {selected.raw_log}
            </pre>
            {selected.normalized_data && (
              <>
                <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--sf-accent-light)", marginTop: "12px", marginBottom: "8px" }}>
                  Normalized Data
                </div>
                <pre style={{ fontSize: "11px", color: "var(--sf-text-secondary)", margin: 0 }}>
                  {JSON.stringify(selected.normalized_data, null, 2)}
                </pre>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
