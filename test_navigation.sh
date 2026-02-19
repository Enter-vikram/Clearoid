#!/bin/bash

echo "🧪 Testing Clearoid Navigation..."
echo ""

# Check if all HTML files exist
echo "✅ Checking files..."
files=(
    "frontend/index.html"
    "frontend/pages/dashboard.html"
    "frontend/pages/signin.html"
    "frontend/pages/upload.html"
    "frontend/pages/history.html"
    "frontend/pages/export.html"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file exists"
    else
        echo "  ✗ $file missing"
    fi
done

echo ""
echo "✅ Checking navigation links..."

# Check if Dashboard link exists in all pages
for file in "${files[@]}"; do
    if grep -q "dashboard.html" "$file" || grep -q "Dashboard" "$file"; then
        echo "  ✓ Dashboard link found in $file"
    else
        echo "  ⚠ Dashboard link missing in $file"
    fi
done

echo ""
echo "✅ All checks complete!"
echo ""
echo "🚀 To start the server, run:"
echo "   cd backend && uvicorn main:app --reload"
echo ""
echo "📱 Then open in browser:"
echo "   http://localhost:8000/index.html"
echo "   http://localhost:8000/pages/dashboard.html"
echo "   http://localhost:8000/pages/signin.html"
echo "   http://localhost:8000/pages/upload.html"
echo "   http://localhost:8000/pages/history.html"
echo "   http://localhost:8000/pages/export.html"
