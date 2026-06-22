#!/bin/bash
# SecureFlow AI - One-Command Setup Script for Judges
# This script installs all dependencies and starts the application.

echo "========================================"
echo "🛡️  SecureFlow AI Setup Script"
echo "========================================"

# 1. Backend Setup
echo "\n[1/3] Setting up Backend API..."
cd backend
python -m venv venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
pip install -r requirements.txt
echo "✅ Backend setup complete."

# 2. Frontend Setup
echo "\n[2/3] Setting up Frontend UI..."
cd ../frontend
npm install
echo "✅ Frontend setup complete."

# 3. Launch
echo "\n[3/3] Launching SecureFlow AI..."
echo "Starting Backend on port 8000..."
cd ../backend
# Run uvicorn in background
nohup uvicorn app.main:app --reload --port 8000 > backend.log 2>&1 &

echo "Starting Frontend on port 3000..."
cd ../frontend
# Run npm in background
nohup npm run dev > frontend.log 2>&1 &

echo "\n========================================"
echo "🚀 SYSTEM ONLINE"
echo "========================================"
echo "Backend API Docs: http://localhost:8000/docs"
echo "Frontend War Room: http://localhost:3000"
echo "Demo Launcher: http://localhost:3000/demo"
echo "\nTo stop the system, run 'pkill -f uvicorn' and 'pkill -f next'"
