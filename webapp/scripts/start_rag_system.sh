#!/bin/bash

echo "🚀 Starting RAG System..."
echo ""

# Kill any existing backend processes
echo "1. Cleaning up existing processes..."
pkill -9 -f "uvicorn main:app" 2>/dev/null
sleep 1

# Start backend
echo "2. Starting backend on port 8000..."
cd /home/rkpatel/RAG/webapp/backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
sleep 3

# Check if backend is running
if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend started successfully on port 8000"
else
    echo "❌ Backend failed to start. Check /tmp/backend.log"
    exit 1
fi

# Display backend info
echo ""
echo "=== Backend Status ==="
curl -s http://127.0.0.1:8000/api/health | python3 -m json.tool 2>/dev/null || echo "Could not parse health check"

echo ""
echo "=== System Ready ==="
echo "📡 Backend: http://127.0.0.1:8000"
echo "📊 API Health: http://127.0.0.1:8000/api/health"
echo "📝 Backend logs: tail -f /tmp/backend.log"
echo ""
echo "🌐 Frontend: Open your browser to http://localhost:3000"
echo "   (Start with: cd /home/rkpatel/RAG/webapp/frontend && npm start)"
echo ""
echo "📚 To upload HTML documentation:"
echo "   1. Go to http://localhost:3000"
echo "   2. Login to your account"
echo "   3. Navigate to Documents section"
echo "   4. Find '📚 Application Documentation (HTML/HTM)' card"
echo "   5. Upload your AccCheckerHelp.htm file"
echo ""
echo "🛑 To stop: pkill -f 'uvicorn main:app'"
