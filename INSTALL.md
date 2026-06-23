# SecureFlow AI — Installation Guide

## Requirements

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| npm | 9+ | Package management |

> [!WARNING]
> **Windows Users:** Use PowerShell as an Administrator when running the backend commands, and ensure you set the `$env:PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` variable if you are using newer versions of Python to avoid wheel compilation errors with pydantic-core.

## 1. Configure Environment (CRITICAL)

Before starting, you must configure the AI agent API keys.

```bash
cp .env.example .env
```
Edit `.env` and add your API keys:
- `GEMINI_API_KEY=your_key_here` (Powers the Investigation & Reporting Agents)
- `GROK_API_KEY=your_key_here` (Powers the Triage & Autonomous Agents)
- `GROQ_API_KEY=your_key_here` (Powers the IT Support Agent fallback)

## 2. Start the Backend

**For Windows (PowerShell):**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
$env:PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**For macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

## 3. Start the Frontend

Open a **new terminal window/tab**, then run:
```bash
cd frontend
npm install
npm run dev
```

## 4. Test the Platform

Open your browser to:
- **[http://localhost:3000](http://localhost:3000)** - The SecureFlow AI Dashboard
- **[http://localhost:3000/demo](http://localhost:3000/demo)** - The Interactive Demo Launcher
- **[http://localhost:8000/docs](http://localhost:8000/docs)** - The FastAPI Interactive Docs