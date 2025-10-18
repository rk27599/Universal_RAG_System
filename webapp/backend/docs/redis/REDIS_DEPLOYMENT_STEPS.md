# Redis Deployment Steps - Quick Start Guide

## ✅ What's Already Done

All code has been implemented and configured:
- ✅ Redis service module created
- ✅ Socket.IO integrated with Redis
- ✅ Backend configuration updated
- ✅ Frontend WebSocket settings optimized
- ✅ Comprehensive tests created
- ✅ Monitoring scripts created
- ✅ Documentation complete

## 🚀 What You Need to Do Now

### Step 1: Install Redis Server

```bash
# Update package list
sudo apt-get update

# Install Redis
sudo apt-get install -y redis-server

# Start Redis
sudo service redis-server start

# Verify installation
redis-cli ping
# Expected output: PONG ✅
```

### Step 2: Install Python Redis Dependencies

```bash
# Activate your venv
cd /home/rkpatel/RAG
source venv/bin/activate

# Install Redis Python packages
cd webapp/backend
pip install redis==5.0.1 aioredis==2.0.1
```

### Step 3: Configure Backend Environment

**Edit file:** `webapp/backend/.env`

**Add these lines:**
```env
# Redis Configuration (add at the end of file)
REDIS_URL=redis://localhost:6379
REDIS_DB=0
REDIS_ENABLED=true
```

### Step 4: Run Tests to Verify

```bash
# Make sure you're in venv
cd /home/rkpatel/RAG/webapp/backend

# Run Redis connectivity tests (should pass immediately)
pytest tests/test_redis_websocket.py::TestRedisConnectivity -v

# Run all Redis tests (needs backend running)
pytest tests/test_redis_websocket.py -v

# Expected output:
# TestRedisConnectivity: 4 tests PASSED ✅
# TestWebSocketRedisIntegration: 4 tests (need backend running)
# TestRedisPerformance: 2 tests PASSED ✅
```

### Step 5: Quick Redis Test Script

```bash
# Run automated test script
cd /home/rkpatel/RAG/webapp/backend
bash scripts/redis_test.sh

# Expected output:
# ✅ Redis installed
# ✅ Redis server is running
# ✅ Redis connectivity test passed
# ✅ All tests passed!
```

### Step 6: Start Backend with Multi-Worker Support

```bash
# Make sure Redis is running
redis-cli ping

# Start backend
cd /home/rkpatel/RAG/webapp/backend
python main.py

# Backend will now use 4 workers with Redis session management
```

### Step 7: Verify WebSocket Stability

**Open a new terminal and test:**

```bash
# Check health endpoint
curl http://localhost:8000/api/ready

# Look for these in the response:
# "redis": true ✅
# "multi_worker_support": true ✅
```

**Monitor Redis sessions in real-time:**

```bash
# Terminal 1: Monitor Redis
redis-cli MONITOR

# Terminal 2: Watch health metrics
cd /home/rkpatel/RAG/webapp/backend
python scripts/redis_health.py --watch

# Terminal 3: Count active sessions
watch -n 1 'redis-cli KEYS "socketio:session:*" | wc -l'
```

### Step 8: Test WebSocket Connections

**Open your frontend and test chat:**

1. Login to the application
2. Start a chat conversation
3. Send multiple messages
4. **Verify in backend logs:**
   - ✅ No `Invalid session` errors
   - ✅ No `403 Forbidden` errors
   - ✅ No constant reconnection loops
   - ✅ Stable WebSocket connection

**Monitor backend logs:**
```bash
tail -f /home/rkpatel/RAG/webapp/backend/logs/rag_app.log | grep -i "websocket\|redis\|session"
```

---

## 🔧 Quick Troubleshooting

### Issue: Redis not starting

```bash
# Check if Redis is installed
redis-server --version

# Check if Redis is running
ps aux | grep redis-server

# Start Redis
sudo service redis-server start

# Check logs
sudo tail -f /var/log/redis/redis-server.log
```

### Issue: Backend shows "Redis connection failed"

```bash
# Test Redis connectivity
redis-cli ping

# Check Redis port
sudo netstat -tlnp | grep 6379

# Restart Redis
sudo service redis-server restart
```

### Issue: WebSocket still disconnecting

```bash
# 1. Verify Redis is enabled
cat webapp/backend/.env | grep REDIS

# 2. Check backend sees Redis
curl http://localhost:8000/api/ready | python3 -m json.tool | grep redis

# 3. Monitor Redis sessions
redis-cli KEYS "socketio:session:*"

# 4. Watch Redis commands in real-time
redis-cli MONITOR
```

---

## 📊 Success Indicators

You'll know it's working when you see:

### ✅ Redis Health Check
```bash
$ python scripts/redis_health.py
================================================================================
🏥 Redis Health Report
================================================================================
✅ Redis Status: HEALTHY
   ping_ms: 0.42
   Total Sessions: 3
   connected_clients: 4
```

### ✅ Backend Health Check
```bash
$ curl http://localhost:8000/api/ready | python3 -m json.tool
{
  "status": "ready",
  "checks": {
    "database": true,
    "ollama": true,
    "redis": true,
    "storage": true
  },
  "multi_worker_support": true
}
```

### ✅ Stable WebSocket Logs
```
✅ WebSocket connected: rpl32 (sid: ABC123)
INFO:     connection open
✅ Message sent successfully
INFO:     connection stable
```

**No more:**
```
❌ ERROR:engineio.server:Invalid session ABC123
❌ INFO: connection rejected (403 Forbidden)
❌ INFO: connection closed
```

---

## 📚 Additional Resources

- **Full Redis Setup Guide**: [docs/REDIS_SETUP.md](../docs/REDIS_SETUP.md)
- **Network Setup Guide**: [docs/NETWORK_SETUP.md](../docs/NETWORK_SETUP.md) - Step 6
- **Redis Health Script**: `scripts/redis_health.py`
- **Redis Test Script**: `scripts/redis_test.sh`
- **Comprehensive Tests**: `tests/test_redis_websocket.py`

---

## 🎯 Expected Results

### Before Redis:
```
User sends message → WebSocket connects to Worker 1
Next request → Goes to Worker 2 → Session not found → 403 Error
Connection drops → Reconnects → Random worker → Same problem
Result: Constant disconnection loop ❌
```

### After Redis:
```
User sends message → WebSocket connects to Worker 1 → Session saved in Redis
Next request → Goes to Worker 2 → Finds session in Redis → Connection accepted
Connection stays stable → All workers share same sessions
Result: Stable, persistent connection ✅
```

---

## 🚦 Quick Status Check

Run this command to see everything at a glance:

```bash
echo "=== Redis Status ==="
redis-cli ping 2>/dev/null && echo "✅ Redis running" || echo "❌ Redis not running"

echo ""
echo "=== Backend Status ==="
curl -s http://localhost:8000/api/health 2>/dev/null | python3 -m json.tool | grep status || echo "❌ Backend not running"

echo ""
echo "=== Active Sessions ==="
redis-cli KEYS "socketio:session:*" 2>/dev/null | wc -l | xargs echo "Sessions:"

echo ""
echo "=== Redis Health ==="
python3 scripts/redis_health.py 2>/dev/null | grep "Redis Status" || echo "Run: python scripts/redis_health.py"
```

---

## 💡 Pro Tips

1. **Keep Redis Running**: Add Redis to startup services:
   ```bash
   sudo systemctl enable redis-server
   ```

2. **Monitor Performance**: Use the watch mode for real-time monitoring:
   ```bash
   python scripts/redis_health.py --watch
   ```

3. **Clean Up Old Sessions**: Redis automatically handles session expiration (TTL: 1 hour)

4. **Check Logs**: If issues occur, check both:
   - Backend logs: `tail -f logs/rag_app.log`
   - Redis logs: `sudo tail -f /var/log/redis/redis-server.log`

5. **Verify Multi-Worker**: Check that workers=4 in main.py (line 226):
   ```python
   workers=1 if settings.DEBUG else 4,  # 4 workers with Redis
   ```

---

**You're ready to deploy!** 🚀

Once you complete these steps, your WebSocket connections will be stable and you can use 4 workers for better performance.
