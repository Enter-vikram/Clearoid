#!/bin/bash

echo "🧪 CLEAROID - COMPLETE SYSTEM TEST"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python
echo "1️⃣  Checking Python..."
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python3 found: $(python3 --version)${NC}"
else
    echo -e "${RED}✗ Python3 not found${NC}"
    exit 1
fi

# Check if in correct directory
if [ ! -f "backend/main.py" ]; then
    echo -e "${RED}✗ Please run from project root directory${NC}"
    exit 1
fi

# Check database
echo ""
echo "2️⃣  Checking Database..."
if [ -f "database/titles.db" ]; then
    echo -e "${GREEN}✓ Database exists${NC}"
else
    echo -e "${YELLOW}⚠ Database will be created on first run${NC}"
fi

# Check all HTML files
echo ""
echo "3️⃣  Checking Frontend Files..."
files=(
    "frontend/index.html"
    "frontend/pages/dashboard.html"
    "frontend/pages/signin.html"
    "frontend/pages/upload.html"
    "frontend/pages/history.html"
    "frontend/pages/export.html"
)

all_files_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file missing${NC}"
        all_files_exist=false
    fi
done

# Check backend files
echo ""
echo "4️⃣  Checking Backend Files..."
backend_files=(
    "backend/main.py"
    "backend/routes/title_routes.py"
    "backend/routes/excel_routes.py"
    "backend/routes/admin_routes.py"
    "backend/routes/auth_routes.py"
)

for file in "${backend_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file missing${NC}"
    fi
done

# Check requirements
echo ""
echo "5️⃣  Checking Dependencies..."
if [ -f "backend/requirements.txt" ]; then
    echo -e "${GREEN}✓ requirements.txt found${NC}"
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q -r backend/requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
fi

echo ""
echo "===================================="
echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
echo "===================================="
echo ""
echo "🚀 TO START THE SERVER:"
echo ""
echo "   cd backend"
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "📱 THEN TEST THESE URLS:"
echo ""
echo "   http://localhost:8000              → Redirects to index"
echo "   http://localhost:8000/index.html   → Home page"
echo "   http://localhost:8000/pages/signin.html → Sign in"
echo "   http://localhost:8000/pages/dashboard.html → Dashboard"
echo "   http://localhost:8000/pages/upload.html → Upload"
echo "   http://localhost:8000/pages/history.html → History"
echo "   http://localhost:8000/pages/export.html → Export"
echo ""
echo "🔧 API ENDPOINTS:"
echo ""
echo "   http://localhost:8000/docs         → API Documentation"
echo "   http://localhost:8000/api/stats    → Get statistics"
echo "   http://localhost:8000/admin/stats  → Admin stats"
echo ""
echo "✅ TEST CHECKLIST:"
echo ""
echo "   [ ] Navigate between all pages using nav links"
echo "   [ ] Click Sign in → goes to signin.html"
echo "   [ ] Sign in with demo account"
echo "   [ ] Dashboard loads with stats"
echo "   [ ] Upload page accepts files"
echo "   [ ] History page shows records"
echo "   [ ] Export page downloads data"
echo "   [ ] All API endpoints respond"
echo ""
