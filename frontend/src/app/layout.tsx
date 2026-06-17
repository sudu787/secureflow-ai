import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "SecureFlow AI — Autonomous Security & IT Operations",
  description: "AI-powered Security Operations Center and IT Support Automation platform. Detect threats, investigate incidents, and automate IT support with multi-agent AI.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="sf-bg-animated" />
        <div className="sf-layout">
          <Sidebar />
          <main className="sf-main">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
