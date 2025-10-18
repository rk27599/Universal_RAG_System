# Redis Complete Guide - WebSocket Multi-Worker Support

> **⚠️ REQUIRED FOR PRODUCTION**: Redis is **mandatory** for multi-worker deployments. Without Redis, WebSocket connections will fail with "Invalid session" and "403 Forbidden" errors. Single-worker development can optionally disable Redis, but this is **not recommended** for production.

**Complete documentation for Redis session management in your RAG system**

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Problem & Solution Overview](#problem--solution-overview)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [Testing & Validation](#testing--validation)
6. [Fixing Redis Pub/Sub Errors](#fixing-redis-pubsub-errors)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Performance Tuning](#performance-tuning)
10. [Security Best Practices](#security-best-practices)

---

## Quick Start

### TL;DR - 5 Minute Setup

```bash
# 1. Install Redis
sudo apt-get update && sudo apt-get install -y redis-server
sudo service redis-server start
redis-cli ping  # Should return PONG

# 2. Install Python dependencies
cd /home/rkpatel/RAG/webapp/backend
source ../../venv/bin/activate
pip uninstall aioredis -y  # Remove incompatible package
pip install python-socketio==5.11.0 --upgrade
pip install redis==5.0.1

# 3. Configure backend (add to .env)
echo "REDIS_URL=redis://localhost:6379" >> .env
echo "REDIS_DB=0" >> .env
echo "REDIS_ENABLED=true" >> .env

# 4. Start backend
python main.py

# 5. Verify
curl http://localhost:8000/api/ready | python3 -m json.tool
# Check: "redis": true, "multi_worker_support": true
```

✅ **Done!** Your WebSocket connections are now stable with multi-worker support.

---

## Problem & Solution Overview

### The Original Problem

**What you were experiencing:**
```
ERROR:engineio.server:Invalid session UmFzeXDk6inouaRwAAAA
INFO: connection rejected (403 Forbidden)
INFO: connection closed
✅ WebSocket connected
INFO: connection closed
✅ WebSocket connected
INFO: connection rejected (403 Forbidden)
```

**Constant reconnection loop** - Users couldn't maintain stable chat connections.

### Root Cause

When using multiple Uvicorn workers (default: 4 workers), each worker has its own Socket.IO session store:

```
Request 1 → Worker 1 → Creates Session ABC123 (stored in Worker 1's memory)
Request 2 → Worker 2 → Looks for Session ABC123 → NOT FOUND → 403 Forbidden
Request 3 → Worker 3 → Same problem
Result: Constant disconnection loop ❌
```

### The Solution: Redis

Redis provides a **centralized session store** shared by all workers:

```
Worker 1 ──┐
Worker 2 ──┼──→ Redis (Shared Session Store)
Worker 3 ──┤      ↓
Worker 4 ──┘   All sessions accessible by all workers
```

**Result:**
```
Request 1 → Worker 1 → Creates Session ABC123 → Saves to Redis
Request 2 → Worker 2 → Finds Session ABC123 in Redis → ✅ Connection accepted
Request 3 → Worker 3 → Same session found → ✅ Stable connection
```

---

## Installation & Setup

### Step 1: Install Redis Server

#### Ubuntu / WSL / Debian
```bash
# Update package list
sudo apt-get update

# Install Redis server
sudo apt-get install -y redis-server

# Verify installation
redis-server --version
# Expected: Redis server v=6.0.16 or higher

# Start Redis
sudo service redis-server start

# Enable on boot
sudo systemctl enable redis-server

# Test connectivity
redis-cli ping
# Expected: PONG
```

#### macOS
```bash
# Using Homebrew
brew install redis
brew services start redis
redis-cli ping
```

### Step 2: Install Python Dependencies

**IMPORTANT:** Remove `aioredis` - it's incompatible with newer `python-socketio` versions.

```bash
cd /home/rkpatel/RAG/webapp/backend
source ../../venv/bin/activate

# Remove old incompatible package
pip uninstall aioredis -y

# Install/upgrade correct versions
pip install python-socketio==5.11.0 --upgrade
pip install redis==5.0.1

# Verify installation
pip list | grep -E "redis|socketio"
# Expected:
#   python-socketio  5.11.0
#   redis            5.0.1
```

### Step 3: Configure Backend

**File:** `webapp/backend/.env`

```env
# Redis Configuration (add these lines)
REDIS_URL=redis://localhost:6379
REDIS_DB=0
REDIS_ENABLED=true

# Optional: If you set a password in redis.conf
# REDIS_URL=redis://:your_password@localhost:6379
```

### Step 4: Start Backend

```bash
cd /home/rkpatel/RAG/webapp/backend
python main.py
```

**Expected output:**
```
✅ Redis manager initialized: redis://localhost:6379
INFO:socketio.server:aioredis backend initialized.
✅ WebSocket connected: rpl32 (sid: DgVL3JnIzsS-2GU4AAAF)
```

**NO MORE:**
```
❌ Invalid session errors
❌ 403 Forbidden
❌ Constant reconnection loops
```

---

## Configuration

### Redis Server Configuration

**File:** `/etc/redis/redis.conf`

```conf
# ====================
# Network (Security)
# ====================
bind 127.0.0.1 ::1    # Localhost only
port 6379

# ====================
# Security
# ====================
# Optional but recommended for production
# requirepass your_secure_redis_password

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""

# ====================
# Memory
# ====================
maxmemory 256mb
maxmemory-policy allkeys-lru

# ====================
# Persistence
# ====================
save 900 1
save 300 10
save 60 10000

# ====================
# Logging
# ====================
loglevel notice
logfile /var/log/redis/redis-server.log

# ====================
# Performance
# ====================
tcp-backlog 511
tcp-keepalive 300
```

**Apply configuration:**
```bash
sudo nano /etc/redis/redis.conf
sudo service redis-server restart
```

### Backend Configuration Files

**Already configured!** The following files have been updated:

1. **`core/config.py`** - Redis settings
2. **`api/chat.py`** - Redis manager integration
3. **`main.py`** - Health checks
4. **`requirements.txt`** - Dependencies

---

## Testing & Validation

### Quick Test Script

```bash
cd /home/rkpatel/RAG/webapp/backend
bash scripts/redis_test.sh
```

**Expected output:**
```
================================================================================
🧪 Redis Quick Test Script
================================================================================

📦 Test 1: Checking Redis Installation...
✅ Redis installed: Redis server v=6.0.16

🔌 Test 2: Checking Redis Server Status...
✅ Redis server is running

🔗 Test 3: Testing Redis Connectivity...
✅ Redis connectivity test passed

⚙️  Test 4: Testing Basic Operations...
✅ SET operation successful
✅ GET operation successful
✅ DEL operation successful

🔐 Test 5: Testing Session Storage Pattern...
✅ Session storage successful
✅ Session retrieval successful

⚡ Test 6: Testing Redis Performance...
✅ Average latency: 0.45ms
✅ Latency is excellent (<10ms)

🎉 All tests passed!
```

### Health Check

```bash
# Check backend health
curl http://localhost:8000/api/ready | python3 -m json.tool
```

**Expected response:**
```json
{
  "status": "ready",
  "checks": {
    "database": true,
    "ollama": true,
    "redis": true,
    "storage": true
  },
  "security_validated": true,
  "multi_worker_support": true
}
```

### Comprehensive Tests

```bash
cd /home/rkpatel/RAG/webapp/backend

# Run Redis tests
pytest tests/test_redis_websocket.py -v

# Run integration tests
python tests/test_chat_integration.py
```

---

## Fixing Redis Pub/Sub Errors

### The Error You're Seeing

```
Cannot receive from redis... retrying in 1 secs
ERROR:socketio.server:Cannot receive from redis... retrying in 1 secs
```

**What it means:**
- Redis pub/sub (message broadcasting between workers) has a library compatibility issue
- **BUT** WebSocket connections still work! Messages still send/receive normally.

### Root Cause

`python-socketio==5.10.0` + `aioredis==2.0.1` = **Incompatible combination**

Newer versions of `python-socketio` (5.11.0+) use the `redis` package directly, not `aioredis`.

### The Fix (2 Minutes)

```bash
cd /home/rkpatel/RAG/webapp/backend
source ../../venv/bin/activate

# Step 1: Remove incompatible aioredis
pip uninstall aioredis -y

# Step 2: Upgrade python-socketio
pip install python-socketio==5.11.0 --upgrade

# Step 3: Ensure redis is installed
pip install redis==5.0.1

# Step 4: Verify
pip list | grep -E "redis|socketio"
# Should show:
#   python-socketio  5.11.0
#   redis            5.0.1
# Should NOT show:
#   aioredis         (should be gone)

# Step 5: Restart backend
# Stop with Ctrl+C, then:
python main.py
```

### After the Fix

**Before:**
```
Cannot receive from redis... retrying in 1 secs
ERROR:socketio.server:Cannot receive from redis... retrying in 1 secs
Cannot receive from redis... retrying in 1 secs
ERROR:socketio.server:Cannot receive from redis... retrying in 1 secs
```

**After:**
```
✅ Redis manager initialized: redis://localhost:6379
INFO:socketio.server:aioredis backend initialized.
✅ WebSocket connected: rpl32 (sid: ABC123)
📝 rpl32 joined conversation 16
```

**Clean logs, no errors!** ✅

---

## Monitoring & Maintenance

### Real-Time Health Monitoring

```bash
# Health check script
cd /home/rkpatel/RAG/webapp/backend
python scripts/redis_health.py

# Continuous monitoring (updates every 5 seconds)
python scripts/redis_health.py --watch
```

**Output:**
```
================================================================================
🏥 Redis Health Report
📅 Timestamp: 2025-10-13 21:06:00
================================================================================

📊 Basic Information:
   redis_version: 6.0.16
   uptime_in_seconds: 3600

🔌 Connection Statistics:
   connected_clients: 4
   total_connections_received: 127

💾 Memory Statistics:
   used_memory_human: 1.2M
   used_memory_peak_human: 2.1M

👥 Socket.IO Session Statistics:
   Total Sessions: 3

⚡ Performance Statistics:
   instantaneous_ops_per_sec: 45

⏱️  Latency Measurements:
   ping_ms: 0.42
   get_ms: 0.38
   set_ms: 0.41

================================================================================
✅ Redis Status: HEALTHY
================================================================================
```

### Redis CLI Commands

```bash
# Connect to Redis CLI
redis-cli

# Basic commands
> PING                      # Test connectivity (PONG)
> INFO                      # Server info
> DBSIZE                    # Count keys
> KEYS socketio:session:*   # List Socket.IO sessions
> TTL <key>                 # Check expiration time
> GET <key>                 # Get value
> DEL <key>                 # Delete key
```

### Monitor Active Sessions

```bash
# Count active sessions
redis-cli KEYS "socketio:session:*" | wc -l

# List all sessions
redis-cli KEYS "socketio:session:*"

# Watch in real-time
watch -n 1 'redis-cli KEYS "socketio:session:*" | wc -l'
```

### Log Monitoring

```bash
# Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Backend logs (filter for Redis)
tail -f /home/rkpatel/RAG/webapp/backend/logs/rag_app.log | grep -i redis

# WebSocket connections
tail -f /home/rkpatel/RAG/webapp/backend/logs/rag_app.log | grep -E "WebSocket|session"
```

---

## Troubleshooting

### Issue 1: Redis Not Starting

**Symptoms:**
```bash
$ sudo service redis-server start
Job for redis-server.service failed
```

**Solutions:**
```bash
# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Check if port 6379 is in use
sudo netstat -tlnp | grep 6379

# Kill existing Redis process
sudo pkill redis-server

# Start Redis manually with verbose logging
redis-server /etc/redis/redis.conf --loglevel debug
```

### Issue 2: Connection Refused

**Symptoms:**
```bash
$ redis-cli ping
Could not connect to Redis at 127.0.0.1:6379: Connection refused
```

**Solutions:**
```bash
# Check if Redis is running
ps aux | grep redis-server

# Start Redis
sudo service redis-server start

# Check bind address
sudo grep "^bind" /etc/redis/redis.conf
# Should show: bind 127.0.0.1 ::1

# Check firewall (should allow localhost)
sudo ufw status
```

### Issue 3: Still Seeing Pub/Sub Errors After Update

**Symptoms:**
```
Cannot receive from redis... retrying in 1 secs
```

**Solutions:**
```bash
# 1. Verify aioredis is completely removed
pip list | grep aioredis
# Should return nothing

# 2. Check python-socketio version
pip list | grep python-socketio
# Should show 5.11.0 or higher

# 3. Force reinstall
pip uninstall python-socketio redis -y
pip install python-socketio==5.11.0 redis==5.0.1

# 4. Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null

# 5. Restart backend completely
# Kill all processes
pkill -f "python main.py"
# Start fresh
python main.py
```

### Issue 4: WebSocket Still Disconnecting

**Symptoms:**
- Redis is running
- No pub/sub errors
- But WebSocket still drops

**Solutions:**
```bash
# 1. Check Redis connection from backend
curl http://localhost:8000/api/ready | python3 -m json.tool | grep redis
# Should show: "redis": true

# 2. Monitor Redis during connection
redis-cli MONITOR

# 3. Check session count
redis-cli KEYS "socketio:session:*" | wc -l

# 4. Verify REDIS_ENABLED in .env
grep REDIS /home/rkpatel/RAG/webapp/backend/.env
# Should show: REDIS_ENABLED=true

# 5. Check for firewall blocking
sudo iptables -L | grep 6379
```

### Issue 5: High Memory Usage

**Symptoms:**
```
used_memory_human: 500M+
```

**Solutions:**
```bash
# Set memory limit
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Or edit redis.conf
sudo nano /etc/redis/redis.conf
# Add:
#   maxmemory 256mb
#   maxmemory-policy allkeys-lru

# Restart Redis
sudo service redis-server restart

# Verify
redis-cli INFO memory | grep maxmemory
```

---

## Performance Tuning

### Optimize for WebSocket Sessions

**File:** `/etc/redis/redis.conf`

```conf
# High concurrency support
maxclients 10000
tcp-backlog 511

# Disable persistence for speed (sessions are ephemeral)
save ""
appendonly no

# Memory optimization
maxmemory 256mb
maxmemory-policy allkeys-lru

# Reduce latency
tcp-keepalive 300
timeout 0
```

### Linux Kernel Optimization

```bash
# Increase TCP backlog
sudo sysctl -w net.core.somaxconn=65535

# Disable Transparent Huge Pages
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

# Make persistent
echo "net.core.somaxconn=65535" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Monitor Performance

```bash
# Measure latency
redis-cli --latency

# Latency history
redis-cli --latency-history

# Continuous stats
redis-cli --stat
```

---

## Security Best Practices

### 1. Localhost-Only Binding

```conf
# /etc/redis/redis.conf
bind 127.0.0.1 ::1
```

**Verify:**
```bash
redis-cli CONFIG GET bind
netstat -tlnp | grep 6379
```

### 2. Set Strong Password

```conf
# /etc/redis/redis.conf
requirepass YourVeryStrong!Redis@Password#2024
```

**Update backend .env:**
```env
REDIS_URL=redis://:YourVeryStrong!Redis@Password#2024@localhost:6379
```

### 3. Disable Dangerous Commands

```conf
# /etc/redis/redis.conf
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
rename-command SHUTDOWN ""
```

### 4. Enable Protected Mode

```conf
# /etc/redis/redis.conf
protected-mode yes
```

### 5. Regular Security Audits

```bash
# Check for unauthorized access
sudo tail -f /var/log/redis/redis-server.log | grep -i "connection\|auth"

# Monitor commands
redis-cli MONITOR

# Review configuration
redis-cli CONFIG GET *
```

---

## Success Indicators

### ✅ You'll Know It's Working When:

**1. Backend Logs Show:**
```
✅ Redis manager initialized: redis://localhost:6379
INFO:socketio.server:aioredis backend initialized.
✅ WebSocket connected: rpl32 (sid: DgVL3JnIzsS-2GU4AAAF)
📝 rpl32 joined conversation 16
✅ Message processed for rpl32: 230 chars, 15 sources
```

**2. Health Check Shows:**
```json
{
  "redis": true,
  "multi_worker_support": true
}
```

**3. Users Experience:**
- ✅ Instant connection
- ✅ No disconnections
- ✅ Messages send/receive smoothly
- ✅ Real-time streaming works
- ✅ Multiple users can chat simultaneously

**4. Redis Health Shows:**
```
✅ Redis Status: HEALTHY
ping_ms: <5ms
connected_clients: 4
Total Sessions: 3+
```

---

## Before vs After Comparison

| Metric | Before Redis | After Redis |
|--------|-------------|-------------|
| **Invalid session errors** | ❌ Constant (every 5-10s) | ✅ None |
| **403 Forbidden** | ❌ Frequent | ✅ None |
| **Connection stability** | ❌ Drops constantly | ✅ Rock solid |
| **Multi-user support** | ❌ Broken | ✅ Perfect |
| **Message sending** | ⚠️ Intermittent | ✅ 100% reliable |
| **RAG retrieval** | ⚠️ Sometimes fails | ✅ Always works |
| **Worker count** | ⚠️ Must use 1 | ✅ Can use 4+ |
| **Scalability** | ❌ Limited | ✅ Excellent |
| **User experience** | ❌ Frustrating | ✅ Seamless |

---

## Quick Command Reference

```bash
# === Redis Service ===
sudo service redis-server start      # Start
sudo service redis-server stop       # Stop
sudo service redis-server restart    # Restart
sudo service redis-server status     # Status

# === Testing ===
redis-cli ping                        # Test connectivity (PONG)
bash scripts/redis_test.sh            # Full test suite
python scripts/redis_health.py        # Health check

# === Monitoring ===
redis-cli INFO                        # Server info
redis-cli MONITOR                     # Watch commands
redis-cli KEYS "socketio:session:*"   # List sessions
python scripts/redis_health.py --watch # Continuous monitoring

# === Maintenance ===
redis-cli DBSIZE                      # Count keys
redis-cli SAVE                        # Save to disk
redis-cli CONFIG REWRITE              # Save config

# === Backend ===
python main.py                        # Start backend
curl http://localhost:8000/api/ready  # Health check
```

---

## Summary

✅ **Redis is now configured for production-ready multi-worker WebSocket support**

**What this gives you:**
- ✅ Stable WebSocket connections (no more disconnects)
- ✅ Multi-worker support (4 workers for better performance)
- ✅ Horizontal scalability (add more workers as needed)
- ✅ Shared session state (all workers see same sessions)
- ✅ Production-ready reliability
- ✅ Comprehensive monitoring and health checks

**The original WebSocket connection issues are completely resolved!** 🎉

---

## Additional Resources

- **Quick Start**: [REDIS_DEPLOYMENT_STEPS.md](../webapp/backend/REDIS_DEPLOYMENT_STEPS.md)
- **Network Setup**: [NETWORK_SETUP.md](NETWORK_SETUP.md) - Step 6
- **Test Scripts**: `webapp/backend/scripts/redis_*.py`
- **Integration Tests**: `webapp/backend/tests/test_redis_websocket.py`

For questions or issues, refer to the Troubleshooting section above or check the backend logs.
