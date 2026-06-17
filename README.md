# 🛡️ SecureFlow AI

**Autonomous Security & IT Operations Agent**

A production-grade AI-powered Security Operations Center (SOC) and IT Support Automation platform.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### 1. Start the Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Open the Dashboard

Navigate to **http://localhost:3000**

### 4. Run Demo Scenarios

Go to **Demo Center** → Click **"Run All Scenarios"** to generate simulated attacks and IT issues.

---

## 🏗️ Architecture

```
SecureFlow AI
├── backend/          # FastAPI + Python
│   ├── app/
│   │   ├── agents/       # Multi-Agent AI System (5 agents + orchestrator)
│   │   ├── api/          # REST API endpoints
│   │   ├── detection/    # Threat detection engine (rule-based + behavioral)
│   │   ├── demo/         # Demo scenario simulator
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── security/     # Prompt injection defense & policy engine
│   │   └── services/     # Business logic layer
│   └── requirements.txt
├── frontend/         # Next.js + TypeScript + Tailwind
│   └── src/
│       ├── app/          # Pages (Dashboard, Alerts, Chat, Demo, etc.)
│       ├── components/   # UI components
│       └── lib/          # API client & types
└── docker-compose.yml
```

## 🤖 AI Agents

| Agent | Role |
|-------|------|
| **Triage Agent** | Assigns priority (P1-P4), detects false positives |
| **Investigation Agent** | Root cause analysis, attack path reconstruction |
| **Remediation Agent** | Generates fix plans, firewall rules, hardening steps |
| **IT Support Agent** | Troubleshoots VPN, email, printer, performance issues |
| **Reporting Agent** | Executive & technical report generation |

## 🔒 Security Features

- Prompt injection detection (7 attack categories)
- Input validation & sanitization
- Policy engine (dangerous command blocking)
- Output validation (no hallucinated capabilities)
- Audit logging for compliance
- Evidence-based reasoning enforcement

## 📊 API Documentation

Once the backend is running, visit: **http://localhost:8000/docs**

---

Built with ❤️ for SecureFlow AI
