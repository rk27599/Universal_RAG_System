#!/bin/bash
# Backend API Test Script

BASE_URL="http://127.0.0.1:8000"
echo "🧪 Testing Backend API Endpoints..."
echo "=================================="

# Test 1: Health Check
echo -e "\n1️⃣  Health Check"
curl -s "$BASE_URL/api/health" | python3 -m json.tool || echo "Failed"

# Test 2: Login
echo -e "\n2️⃣  Login"
LOGIN_RESPONSE=$(curl -s "$BASE_URL/api/auth/login" -X POST -H "Content-Type: application/json" -d '{"username":"admin","password":"Admin@123"}')
echo "$LOGIN_RESPONSE" | python3 -m json.tool | head -10

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    exit 1
fi
echo "✅ Token received: ${TOKEN:0:30}..."

# Test 3: Get Current User
echo -e "\n3️⃣  Get Current User"
curl -s "$BASE_URL/api/auth/me" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Test 4: Get Conversations
echo -e "\n4️⃣  Get Conversations"
curl -s "$BASE_URL/api/chat/conversations" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Test 5: Get Models
echo -e "\n5️⃣  Get Available Models"
curl -s "$BASE_URL/api/models" | python3 -m json.tool

# Test 6: System Status
echo -e "\n6️⃣  System Status"
curl -s "$BASE_URL/api/system/status" | python3 -m json.tool

echo -e "\n=================================="
echo "✅ All tests completed!"
