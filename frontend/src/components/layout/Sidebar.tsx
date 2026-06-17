"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { section: "Operations" },
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/alerts", label: "Alerts", icon: "🚨" },
  { href: "/incidents", label: "Incidents", icon: "🔍" },
  { href: "/tickets", label: "Tickets", icon: "🎫" },
  { section: "Intelligence" },
  { href: "/knowledge", label: "Knowledge Base", icon: "🧠" },
  { href: "/graph", label: "Graph Explorer", icon: "🕸️" },
  { href: "/chat", label: "AI Assistant", icon: "🤖" },
  { href: "/logs", label: "Log Viewer", icon: "📋" },
  { section: "System" },
  { href: "/agents", label: "Agent Status", icon: "🧠" },
  { href: "/demo", label: "Demo Center", icon: "🎮" },
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
          <div className="sf-sidebar-logo-badge">v1.0</div>
        </div>
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
            return (
              <Link
                key={item.href}
                href={item.href!}
                className={`sf-sidebar-link ${isActive ? "active" : ""}`}
                style={{ position: "relative" }}
              >
                <span className="sf-sidebar-icon">{item.icon}</span>
                <span>{item.label}</span>
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
        <div style={{ fontSize: "11px", color: "var(--sf-text-muted)" }}>
          SecureFlow AI Platform
        </div>
        <div style={{ fontSize: "10px", color: "var(--sf-text-muted)", marginTop: "4px" }}>
          © 2026 • All systems operational
        </div>
      </div>
    </aside>
  );
}
