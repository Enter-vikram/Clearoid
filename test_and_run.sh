#!/bin/bash

# ============================================================
# Clearoid - Complete System Test & Startup
# ============================================================

echo "🔍 Testing Clearoid System..."
echo ""

# Test 1: Check Python version
echo "1️⃣ Checking Python version..."
python3 --version
echo ""

# Test 2: Check virtual environment
echo "2️⃣ Checking virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
else
    echo "⚠️  Creating virtual environment..."
    python3 -m venv venv
fi
echo ""

# Test 3: Activate and check packages
echo "3️⃣ Checking installed packages..."
source venv/bin/activate
pip list | grep -E "(fastapi|uvicorn|pandas|sentence-transformers|xlrd|openpyxl)" || echo "⚠️  Some packages missing"
echo ""

# Test 4: Run connection test
echo "4️⃣ Running connection test..."
python3 test_connections.py
echo ""

# Test 5: Check database
echo "5️⃣ Checking database content..."
python3 -c "
import sys
sys.path.insert(0, '.')
from database.connection import SessionLocal
from database.models import Title

db = SessionLocal()
count = db.query(Title).count()
unique = db.query(Title).filter(Title.is_duplicate == 0).count()
duplicates = db.query(Title).filter(Title.is_duplicate == 1).count()
print(f'📊 Database Stats:')
print(f'   Total: {count}')
print(f'   Unique: {unique}')
print(f'   Duplicates: {duplicates}')
db.close()
"
echo ""

# Test 6: Check directories
echo "6️⃣ Checking directories..."
[ -d "temp/uploads" ] && echo "✅ temp/uploads exists" || echo "❌ temp/uploads missing"
[ -d "database" ] && echo "✅ database exists" || echo "❌ database missing"
[ -d "backend" ] && echo "✅ backend exists" || echo "❌ backend missing"
[ -d "frontend" ] && echo "✅ frontend exists" || echo "❌ frontend missing"
echo ""

# Test 7: Check .env file
echo "7️⃣ Checking environment configuration..."
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    grep -q "DATABASE_URL" .env && echo "✅ DATABASE_URL configured"
else
    echo "❌ .env file missing"
fi
echo ""

echo "============================================================"
echo "✅ All tests complete!"
echo "============================================================"
echo ""
echo "🚀 Ready to start server!"
echo ""
echo "Run this command:"
echo "  cd backend && uvicorn main:app --reload"
echo ""
echo "Then open in browser:"
echo "  📊 Data Viewer: http://localhost:8000/data.html"
echo "  📤 Upload: http://localhost:8000/upload.html"
echo "  📋 Dashboard: http://localhost:8000/Dashboard.html"
echo "  📖 API Docs: http://localhost:8000/docs"
echo ""
echo "============================================================"
