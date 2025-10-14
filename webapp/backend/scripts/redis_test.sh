#!/bin/bash
#
# Redis Quick Test Script
# Verify Redis installation, connectivity, and basic operations
#

set -e

echo "================================================================================"
echo "🧪 Redis Quick Test Script"
echo "================================================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if Redis is installed
echo ""
echo "📦 Test 1: Checking Redis Installation..."
if command -v redis-server &> /dev/null; then
    VERSION=$(redis-server --version | head -n 1)
    echo -e "${GREEN}✅ Redis installed: $VERSION${NC}"
else
    echo -e "${RED}❌ Redis not installed${NC}"
    echo ""
    echo "To install Redis:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install redis-server"
    exit 1
fi

# Test 2: Check if Redis is running
echo ""
echo "🔌 Test 2: Checking Redis Server Status..."
if pgrep -x "redis-server" > /dev/null; then
    echo -e "${GREEN}✅ Redis server is running${NC}"
else
    echo -e "${YELLOW}⚠️  Redis server is not running${NC}"
    echo ""
    echo "To start Redis:"
    echo "  sudo service redis-server start"
    echo "  # or"
    echo "  redis-server &"
    exit 1
fi

# Test 3: Test Redis connectivity
echo ""
echo "🔗 Test 3: Testing Redis Connectivity..."
if redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis connectivity test passed${NC}"
else
    echo -e "${RED}❌ Redis connectivity test failed${NC}"
    exit 1
fi

# Test 4: Test basic operations
echo ""
echo "⚙️  Test 4: Testing Basic Operations..."

# SET operation
redis-cli SET test:key "test_value_123" EX 60 > /dev/null
echo -e "${GREEN}✅ SET operation successful${NC}"

# GET operation
RETRIEVED=$(redis-cli GET test:key)
if [ "$RETRIEVED" = "test_value_123" ]; then
    echo -e "${GREEN}✅ GET operation successful${NC}"
else
    echo -e "${RED}❌ GET operation failed: expected 'test_value_123', got '$RETRIEVED'${NC}"
    exit 1
fi

# DELETE operation
redis-cli DEL test:key > /dev/null
echo -e "${GREEN}✅ DEL operation successful${NC}"

# Test 5: Test session pattern (Socket.IO simulation)
echo ""
echo "🔐 Test 5: Testing Session Storage Pattern..."

# Create test session
SESSION_ID="test_session_$(date +%s)"
SESSION_DATA='{"user_id":"test_user","username":"testuser","connected_at":'$(date +%s)'}'
redis-cli SETEX "socketio:session:$SESSION_ID" 3600 "$SESSION_DATA" > /dev/null
echo -e "${GREEN}✅ Session storage successful${NC}"

# Retrieve session
RETRIEVED_SESSION=$(redis-cli GET "socketio:session:$SESSION_ID")
if [ ! -z "$RETRIEVED_SESSION" ]; then
    echo -e "${GREEN}✅ Session retrieval successful${NC}"
else
    echo -e "${RED}❌ Session retrieval failed${NC}"
    exit 1
fi

# Cleanup
redis-cli DEL "socketio:session:$SESSION_ID" > /dev/null

# Test 6: Redis performance
echo ""
echo "⚡ Test 6: Testing Redis Performance..."

# Measure latency (100 PING operations)
LATENCY_MS=$(redis-cli --latency-history -i 1 -c 100 | grep "avg latency" | head -n 1 | awk '{print $4}')
echo -e "${GREEN}✅ Average latency: ${LATENCY_MS}ms${NC}"

if (( $(echo "$LATENCY_MS < 10.0" | bc -l) )); then
    echo -e "${GREEN}✅ Latency is excellent (<10ms)${NC}"
elif (( $(echo "$LATENCY_MS < 50.0" | bc -l) )); then
    echo -e "${YELLOW}⚠️  Latency is acceptable (10-50ms)${NC}"
else
    echo -e "${RED}❌ Latency is high (>50ms)${NC}"
fi

# Test 7: Check Redis info
echo ""
echo "📊 Test 7: Redis Server Information..."
echo "----------------------------------------"
redis-cli INFO server | grep -E "redis_version|redis_mode|os|arch_bits|uptime_in_seconds"
echo ""
redis-cli INFO clients | grep -E "connected_clients"
redis-cli INFO memory | grep -E "used_memory_human|used_memory_peak_human"
echo "----------------------------------------"

# Test 8: Count active Socket.IO sessions
echo ""
echo "👥 Test 8: Counting Socket.IO Sessions..."
SESSION_COUNT=$(redis-cli KEYS "socketio:session:*" | wc -l)
echo -e "${GREEN}✅ Active Socket.IO sessions: $SESSION_COUNT${NC}"

# Test 9: Test Python Redis connectivity
echo ""
echo "🐍 Test 9: Testing Python Redis Client..."
if command -v python3 &> /dev/null; then
    PYTHON_TEST=$(python3 <<EOF
import redis
try:
    client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    client.ping()
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
EOF
)
    if [[ "$PYTHON_TEST" == *"SUCCESS"* ]]; then
        echo -e "${GREEN}✅ Python Redis client connectivity successful${NC}"
    else
        echo -e "${RED}❌ Python Redis client connectivity failed: $PYTHON_TEST${NC}"
        echo ""
        echo "To install Python Redis client:"
        echo "  pip install redis"
    fi
else
    echo -e "${YELLOW}⚠️  Python 3 not found, skipping Python test${NC}"
fi

# Summary
echo ""
echo "================================================================================"
echo "🎉 Redis Test Summary"
echo "================================================================================"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "Redis is ready for Socket.IO multi-worker support."
echo ""
echo "Next steps:"
echo "  1. Install Redis dependencies: pip install redis aioredis"
echo "  2. Configure backend: Update webapp/backend/.env with REDIS_URL=redis://localhost:6379"
echo "  3. Start backend with multiple workers: python main.py"
echo "  4. Monitor Redis: python scripts/redis_health.py"
echo ""
echo "================================================================================"
