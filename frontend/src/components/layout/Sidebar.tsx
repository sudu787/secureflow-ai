"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, BellRing, Target, Ticket, Brain, Network,
  MessageSquare, FileText, Bot, Gamepad2, ShieldCheck, Zap,
  TrendingUp, Swords, Globe, Crosshair, Database, SearchCode,
  Crown, Activity, BarChart2
} from "lucide-react";

const navItems = [
  // ── Executive ────────────────────────────────────────
  { section: "Executive" },
  { href: "/executive", label: "Command Center", Icon: Crown,       badge: "EXEC" },

  // ── Real-Time Ops ─────────────────────────────────────
  { section: "Operations" },
  { href: "/",          label: "War Room",       Icon: LayoutDashboard },
  { href: "/alerts",    label: "Alerts",          Icon: BellRing },
  { href: "/incidents", label: "Incidents",        Icon: Target },
  { href: "/tickets",   label: "Tickets",          Icon: Ticket },

  // ── Intelligence ──────────────────────────────────────
  { section: "Intelligence" },
  { href: "/investigate",    label: "AI Investigation", Icon: Crosshair },
  { href: "/graph",          label: "Graph Explorer",   Icon: Network },
  { href: "/threat-hunting", label: "Threat Hunting",   Icon: SearchCode },
  { href: "/memory",         label: "Memory Center",    Icon: Database },
  { href: "/threat-intel",   label: "Threat Intel",     Icon: Globe },
  { href: "/mitre",          label: "MITRE ATT&CK",     Icon: Swords },
  { href: "/knowledge",      label: "RAG Explorer",     Icon: Brain },

  // ── Security ──────────────────────────────────────────
  { section: "Security" },
  { href: "/risk",        label: "Risk Prediction", Icon: TrendingUp },
  { href: "/compliance",  label: "Compliance",       Icon: ShieldCheck },
  { href: "/autonomous",  label: "Auto Response",    Icon: Zap },

  // ── System ────────────────────────────────────────────
  { section: "System" },
  { href: "/agents",  label: "Agent Status", Icon: Bot },
  { href: "/chat",    label: "AI Assistant", Icon: MessageSquare },
  { href: "/logs",    label: "Event Logs",   Icon: FileText },
  { href: "/demo",    label: "Demo Center",  Icon: Gamepad2, badge: "DEMO" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sf-sidebar">
      {/* Logo */}
      <div className="sf-sidebar-logo">
        <div className="sf-sidebar-logo-icon">🛡️</div>
        <div>
          <div className="sf-sidebar-logo-text">SecureFlow AI</div>
          <div className="sf-sidebar-logo-badge">AUTONOMOUS SOC</div>
        </div>
      </div>

      {/* Live status pill */}
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        margin: "-16px 0 16px", padding: "6px 12px",
        background: "rgba(16,185,129,0.08)",
        border: "1px solid rgba(16,185,129,0.15)",
        borderRadius: 8, fontSize: 11,
      }}>
        <span style={{
          width: 6, height: 6, borderRadius: "50%", background: "#10b981",
          animation: "pulse 2s ease-in-out infinite", boxShadow: "0 0 8px rgba(16,185,129,0.6)",
          flexShrink: 0,
        }} />
        <span style={{ color: "#6ee7b7", fontWeight: 600 }}>All Systems Active</span>
        <span style={{ marginLeft: "auto", color: "var(--sf-text-muted)" }}>5 Agents</span>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1 }}>
        {navItems.map((item, i) => {
          if ("section" in item && !("href" in item)) {
            return (
              <div key={i} className="sf-sidebar-section">
                {item.section}
              </div>
            );
          }
          if ("href" in item) {
            const isActive = pathname === item.href;
            const IconComp = (item as any).Icon;
            const badge = (item as any).badge;
            return (
              <Link
                key={item.href}
                href={item.href!}
                className={`sf-sidebar-link ${isActive ? "active" : ""}`}
                style={{ position: "relative" }}
              >
                <span className="sf-sidebar-icon">
                  {IconComp && <IconComp size={15} />}
                </span>
                <span style={{ flex: 1 }}>{item.label}</span>
                {badge && (
                  <span style={{
                    fontSize: 9, fontWeight: 800, padding: "2px 5px",
                    borderRadius: 4, letterSpacing: "0.05em",
                    background: badge === "EXEC"
                      ? "rgba(245,158,11,0.2)"
                      : "rgba(99,102,241,0.2)",
                    color: badge === "EXEC" ? "#fde68a" : "#a5b4fc",
                    border: badge === "EXEC"
                      ? "1px solid rgba(245,158,11,0.3)"
                      : "1px solid rgba(99,102,241,0.3)",
                  }}>
                    {badge}
                  </span>
                )}
              </Link>
            );
          }
          return null;
        })}
      </nav>

      {/* Footer */}
      <div style={{
        padding: "16px 12px",
        borderTop: "1px solid var(--sf-border)",
        marginTop: "auto",
      }}>
        <div style={{ fontSize: 11, color: "var(--sf-text-muted)", fontWeight: 600 }}>
          SecureFlow AI Platform
        </div>
        <div style={{ fontSize: 10, color: "var(--sf-text-muted)", marginTop: 4, display: "flex", justifyContent: "space-between" }}>
          <span>Part 7 · v2.0</span>
          <span style={{ color: "#10b981" }}>● Operational</span>
        </div>
      </div>
    </aside>
  );
}
