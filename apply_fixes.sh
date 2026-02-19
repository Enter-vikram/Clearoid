#!/bin/bash

echo "🔧 Applying comprehensive fixes..."

cd /Users/santhoshkumar/Downloads/Testing-files--main

# Fix 1: Update index.html sign in button to open modal
cat > frontend/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Clearoid - AI Duplicate Detection</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; }
    .sticky-top {
      position: sticky; top: 0; z-index: 1000;
      background: rgba(0,0,0,0.92); backdrop-filter: blur(16px);
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }
  </style>
</head>
<body class="bg-gray-50 dark:bg-black min-h-screen">
  <header class="sticky-top">
    <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
      <div class="text-3xl font-bold text-white">Clearoid</div>
      <div class="flex items-center gap-6" id="navLinks">
        <a href="/index.html" class="text-white hover:text-gray-300">Home</a>
        <a href="/pages/upload.html" class="text-white hover:text-gray-300">Upload</a>
        <a href="/pages/history.html" class="text-white hover:text-gray-300">History</a>
        <a href="/pages/export.html" class="text-white hover:text-gray-300">Export</a>
        <button onclick="checkAuthAndRedirect()" class="bg-white text-black px-6 py-2 rounded-full font-medium hover:bg-gray-200">Sign in</button>
      </div>
    </div>
  </header>

  <main class="flex-grow flex items-center justify-center p-6">
    <div class="w-full max-w-2xl text-center">
      <h1 class="text-6xl font-bold text-gray-900 dark:text-white mb-4">Clearoid</h1>
      <p class="text-xl text-gray-600 dark:text-gray-400 mb-12">AI-Powered Duplicate Detection</p>
      
      <div class="bg-white dark:bg-gray-900 rounded-3xl shadow-2xl p-10">
        <input type="text" id="titleInput" placeholder="Enter project title" class="w-full px-6 py-4 border-2 rounded-xl text-lg mb-6">
        
        <div class="flex gap-4 mb-6">
          <button onclick="submitTitle()" class="flex-1 bg-black text-white py-4 rounded-xl font-semibold hover:opacity-90">Submit Title</button>
          <button onclick="checkDuplicate()" class="flex-1 bg-gray-200 text-black py-4 rounded-xl font-semibold hover:bg-gray-300">Check Duplicate</button>
        </div>
        
        <div class="text-gray-500 my-6">or</div>
        
        <a href="/pages/upload.html" class="block w-full bg-blue-600 text-white py-6 rounded-xl text-xl font-bold hover:bg-blue-700">Upload Excel File (Bulk)</a>
        
        <div id="response" class="hidden mt-6 p-4 rounded-xl"></div>
        
        <a href="/pages/history.html" class="block mt-6 text-blue-600 hover:underline">View all submissions →</a>
      </div>
    </div>
  </main>

  <script>
    function checkAuthAndRedirect() {
      if (localStorage.getItem('clearoid_user')) {
        window.location.href = '/pages/dashboard.html';
      } else {
        window.location.href = '/pages/signin.html';
      }
    }

    async function submitTitle() {
      const title = document.getElementById('titleInput').value.trim();
      if (!title) return alert('Please enter a title');
      
      try {
        const res = await fetch('/api/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title })
        });
        const data = await res.json();
        showMessage(res.ok ? `✅ Saved - ID: ${data.id}` : '❌ Error', res.ok);
      } catch {
        showMessage('❌ Network error', false);
      }
    }

    async function checkDuplicate() {
      const title = document.getElementById('titleInput').value.trim();
      if (!title) return alert('Please enter a title');
      
      try {
        const res = await fetch('/api/check-duplicate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title })
        });
        const data = await res.json();
        showMessage(data.duplicate ? `⚠️ Duplicate found - ID: ${data.match_id}` : '✅ Unique title', !data.duplicate);
      } catch {
        showMessage('❌ Network error', false);
      }
    }

    function showMessage(msg, success) {
      const div = document.getElementById('response');
      div.textContent = msg;
      div.className = `block p-4 rounded-xl ${success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`;
    }

    // Check if logged in and update nav
    if (localStorage.getItem('clearoid_user')) {
      const nav = document.getElementById('navLinks');
      nav.innerHTML = `
        <a href="/index.html" class="text-white hover:text-gray-300">Home</a>
        <a href="/pages/dashboard.html" class="text-white hover:text-gray-300">Dashboard</a>
        <a href="/pages/upload.html" class="text-white hover:text-gray-300">Upload</a>
        <a href="/pages/history.html" class="text-white hover:text-gray-300">History</a>
        <a href="/pages/export.html" class="text-white hover:text-gray-300">Export</a>
        <button onclick="logout()" class="bg-red-600 text-white px-6 py-2 rounded-full font-medium hover:bg-red-700">Logout</button>
      `;
    }

    function logout() {
      localStorage.removeItem('clearoid_user');
      window.location.reload();
    }
  </script>
</body>
</html>
EOF

echo "✅ Fixed index.html"
echo "✅ All fixes applied!"
echo ""
echo "🚀 Restart server:"
echo "cd /Users/santhoshkumar/Downloads/Testing-files--main"
echo "source venv/bin/activate"
echo "uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
