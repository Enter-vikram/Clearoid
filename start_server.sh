#!/bin/bash

echo "🚀 Starting Clearoid Backend Server..."
echo ""

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
    exit 1
fi

source venv/bin/activate

echo "✅ Virtual environment activated"
echo "✅ Starting server on http://localhost:8000"
echo ""
echo "📱 Access URLs:"
echo "   Dashboard: http://localhost:8000/pages/dashboard.html"
echo "   Sign In:   http://localhost:8000/pages/signin.html"
echo "   Upload:    http://localhost:8000/pages/upload.html"
echo "   API Docs:  http://localhost:8000/docs"
echo ""

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
