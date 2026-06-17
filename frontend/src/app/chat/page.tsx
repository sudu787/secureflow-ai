"use client";

import { useEffect, useState, useRef } from "react";
import { sendChatMessage, getChatSessions, getChatSession } from "@/lib/api";
import type { ChatMessage, ChatResponse } from "@/lib/types";

/* ── Simple Markdown Renderer ──────────────────────────────────────────────── */
function renderMarkdown(text: string) {
  if (!text) return null;
  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeLines: string[] = [];
  let codeLang = "";

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block toggle
    if (line.trim().startsWith("```")) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${i}`} style={{
            background: "rgba(0,0,0,0.4)", borderRadius: "8px", padding: "12px 16px",
            fontSize: "12px", fontFamily: "'Fira Code', 'Cascadia Code', monospace",
            overflowX: "auto", border: "1px solid var(--sf-border)", margin: "8px 0",
            color: "#e2e8f0", lineHeight: 1.6,
          }}>
            {codeLang && <div style={{ fontSize: "10px", color: "var(--sf-text-muted)", marginBottom: "6px", textTransform: "uppercase" }}>{codeLang}</div>}
            <code>{codeLines.join("\n")}</code>
          </pre>
        );
        codeLines = [];
        codeLang = "";
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
        codeLang = line.trim().slice(3).trim();
      }
      continue;
    }
    if (inCodeBlock) { codeLines.push(line); continue; }

    // Empty line
    if (line.trim() === "") { elements.push(<div key={`br-${i}`} style={{ height: "8px" }} />); continue; }

    // Headings
    if (line.startsWith("### ")) {
      elements.push(<h4 key={i} style={{ fontSize: "13px", fontWeight: 700, color: "var(--sf-text-primary)", margin: "12px 0 4px" }}>{formatInline(line.slice(4))}</h4>);
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(<h3 key={i} style={{ fontSize: "15px", fontWeight: 700, color: "var(--sf-text-primary)", margin: "14px 0 6px" }}>{formatInline(line.slice(3))}</h3>);
      continue;
    }
    if (line.startsWith("# ")) {
      elements.push(<h2 key={i} style={{ fontSize: "17px", fontWeight: 700, color: "var(--sf-text-primary)", margin: "16px 0 8px" }}>{formatInline(line.slice(2))}</h2>);
      continue;
    }

    // Horizontal rule
    if (line.trim() === "---" || line.trim() === "***") {
      elements.push(<hr key={i} style={{ border: "none", borderTop: "1px solid var(--sf-border)", margin: "12px 0" }} />);
      continue;
    }

    // Bullet lists
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      const indent = line.length - line.trimStart().length;
      elements.push(
        <div key={i} style={{ display: "flex", gap: "8px", paddingLeft: `${indent * 4 + 4}px`, margin: "2px 0" }}>
          <span style={{ color: "var(--sf-accent-light)", flexShrink: 0 }}>•</span>
          <span style={{ fontSize: "13px", color: "var(--sf-text-secondary)", lineHeight: 1.6 }}>{formatInline(line.trim().slice(2))}</span>
        </div>
      );
      continue;
    }

    // Numbered lists
    const numMatch = line.trim().match(/^(\d+)\.\s(.+)/);
    if (numMatch) {
      elements.push(
        <div key={i} style={{ display: "flex", gap: "8px", paddingLeft: "4px", margin: "2px 0" }}>
          <span style={{ color: "var(--sf-accent-light)", fontWeight: 600, fontSize: "13px", flexShrink: 0, minWidth: "18px" }}>{numMatch[1]}.</span>
          <span style={{ fontSize: "13px", color: "var(--sf-text-secondary)", lineHeight: 1.6 }}>{formatInline(numMatch[2])}</span>
        </div>
      );
      continue;
    }

    // Regular paragraph
    elements.push(<p key={i} style={{ fontSize: "13px", color: "var(--sf-text-secondary)", lineHeight: 1.6, margin: "2px 0" }}>{formatInline(line)}</p>);
  }

  return <>{elements}</>;
}

/* Format inline: **bold**, *italic*, `code`, [text](url) */
function formatInline(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|\[(.+?)\]\((.+?)\))/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    if (match[2]) parts.push(<strong key={match.index} style={{ fontWeight: 700, color: "var(--sf-text-primary)" }}>{match[2]}</strong>);
    else if (match[3]) parts.push(<em key={match.index} style={{ fontStyle: "italic", color: "var(--sf-accent-light)" }}>{match[3]}</em>);
    else if (match[4]) parts.push(<code key={match.index} style={{ background: "rgba(99,102,241,0.15)", padding: "1px 5px", borderRadius: "4px", fontSize: "12px", fontFamily: "monospace", color: "#c4b5fd" }}>{match[4]}</code>);
    else if (match[5] && match[6]) parts.push(<a key={match.index} href={match[6]} style={{ color: "var(--sf-accent-light)", textDecoration: "underline" }}>{match[5]}</a>);
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts.length === 1 && typeof parts[0] === "string" ? parts[0] : <>{parts}</>;
}

/* ── Chat Page ─────────────────────────────────────────────────────────────── */
export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [sessionType, setSessionType] = useState("general");
  const [sessions, setSessions] = useState<any[]>([]);
  const [blockedIds, setBlockedIds] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { loadSessions(); }, []);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  async function loadSessions() {
    try { setSessions(await getChatSessions()); } catch {}
  }

  async function loadSession(id: number) {
    try {
      const data = await getChatSession(id);
      setMessages(data.messages || []);
      setSessionId(id);
      setSessionType(data.session_type);
    } catch {}
  }

  async function handleSend() {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessage = { role: "user", content: input, timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput("");
    setLoading(true);

    try {
      const res: ChatResponse = await sendChatMessage(currentInput, sessionId || undefined, sessionType);
      setSessionId(res.session_id);
      const msgIndex = messages.length + 1;
      if (res.blocked) {
        setBlockedIds(prev => new Set(prev).add(msgIndex));
      }
      const assistantMsg: ChatMessage = {
        role: "assistant", content: res.response, agent: res.agent_used,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMsg]);
      loadSessions();
    } catch (e: any) {
      setMessages(prev => [...prev, {
        role: "assistant", content: `Error: ${e.message}. Make sure the backend is running.`,
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  }

  function startNewChat() { setMessages([]); setSessionId(null); setBlockedIds(new Set()); }

  const modeIcons: Record<string, string> = { general: "🌐", security: "🔒", it_support: "🔧" };

  return (
    <div className="sf-animate-in">
      <div className="sf-page-header">
        <div>
          <h1 className="sf-page-title">🤖 AI Assistant</h1>
          <p className="sf-page-subtitle">Security operations & IT support • Multi-LLM powered • Prompt injection defense active</p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          {["general", "security", "it_support"].map(t => (
            <button key={t} onClick={() => { setSessionType(t); startNewChat(); }}
              className={`sf-btn sf-btn-sm ${sessionType === t ? "sf-btn-primary" : "sf-btn-secondary"}`}>
              {t === "general" ? "🌐 General" : t === "security" ? "🔒 Security" : "🔧 IT Support"}
            </button>
          ))}
          <button className="sf-btn sf-btn-sm sf-btn-secondary" onClick={startNewChat}>+ New Chat</button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: "20px", height: "calc(100vh - 160px)" }}>
        {/* Session List */}
        <div className="sf-card" style={{ overflow: "auto", padding: "16px" }}>
          <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--sf-text-muted)", marginBottom: "12px", textTransform: "uppercase", letterSpacing: "0.05em" }}>Sessions</div>
          {sessions.length === 0 ? (
            <div style={{ fontSize: "12px", color: "var(--sf-text-muted)", textAlign: "center", padding: "20px 0" }}>No sessions yet</div>
          ) : sessions.map(s => (
            <div key={s.id} onClick={() => loadSession(s.id)} style={{
              padding: "10px 12px", borderRadius: "8px", cursor: "pointer", marginBottom: "4px",
              background: sessionId === s.id ? "rgba(99,102,241,0.1)" : "transparent",
              border: sessionId === s.id ? "1px solid rgba(99,102,241,0.2)" : "1px solid transparent",
              transition: "all 0.2s ease",
            }}>
              <div style={{ fontSize: "13px", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {modeIcons[s.session_type] || "🌐"} {s.title}
              </div>
              <div style={{ fontSize: "11px", color: "var(--sf-text-muted)", marginTop: "2px" }}>{s.message_count} messages</div>
            </div>
          ))}
        </div>

        {/* Chat Area */}
        <div className="sf-card" style={{ display: "flex", flexDirection: "column", padding: "20px" }}>
          {/* Messages */}
          <div style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column", gap: "16px", paddingBottom: "16px" }}>
            {messages.length === 0 && (
              <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: "16px" }}>
                <div style={{ fontSize: "48px" }}>🛡️</div>
                <div style={{ fontSize: "18px", fontWeight: 700 }}>SecureFlow AI Assistant</div>
                <div style={{ fontSize: "13px", color: "var(--sf-text-muted)", textAlign: "center", maxWidth: "400px", lineHeight: 1.6 }}>
                  Ask me about security incidents, threats, IT issues, or try testing the prompt injection defense.
                </div>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "center" }}>
                  {[
                    "Investigate the latest SSH brute force alert",
                    "My VPN keeps disconnecting",
                    "What is the current security status?",
                    "Generate a report on recent incidents",
                  ].map((q, i) => (
                    <button key={i} onClick={() => setInput(q)} className="sf-btn sf-btn-sm sf-btn-secondary" style={{ fontSize: "12px" }}>{q}</button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => {
              const isBlocked = blockedIds.has(i) || (msg.role === "assistant" && msg.content?.includes("Security Alert") && msg.content?.includes("blocked"));
              return (
                <div key={i} className={`sf-chat-bubble ${msg.role} ${isBlocked ? "blocked" : ""}`}>
                  {msg.role === "assistant" && msg.agent && (
                    <div className="sf-chat-agent-tag">
                      <span>{isBlocked ? "🛡️" : "🤖"}</span>
                      <span>{msg.agent.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</span>
                    </div>
                  )}
                  <div className="sf-markdown">{renderMarkdown(msg.content || "")}</div>
                </div>
              );
            })}

            {loading && (
              <div className="sf-chat-bubble assistant">
                <div className="sf-chat-agent-tag"><span>🤖</span><span>Processing...</span></div>
                <div className="sf-loading" style={{ fontSize: "14px" }}>Analyzing your request through the security pipeline...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="sf-chat-input-area">
            <input
              className="sf-chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSend()}
              placeholder={
                sessionType === "security" ? "Ask about threats, alerts, or investigations..." :
                sessionType === "it_support" ? "Describe your IT issue (VPN, email, printer...)" :
                "Ask SecureFlow AI anything..."
              }
              disabled={loading}
            />
            <button className="sf-btn sf-btn-primary" onClick={handleSend} disabled={loading}>
              {loading ? "⏳" : "→"} Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
