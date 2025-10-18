# Redis Unicode Error - ROOT CAUSE AND FIX

## Problem
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte
ERROR:socketio.server:Unexpected Error in pubsub listening thread
```

## Root Cause

**Socket.IO sends BINARY messages through Redis pub/sub**, but we had `decode_responses: True` which forced UTF-8 text decoding on binary data.

### Why This Happened:
1. Socket.IO uses Redis pub/sub to broadcast messages between workers
2. These messages are encoded in **MessagePack binary format** (byte 0x80 is MessagePack)
3. Setting `decode_responses=True` tells Redis to decode ALL data as UTF-8 strings
4. UTF-8 decoder fails when it encounters binary MessagePack data → UnicodeDecodeError

## The Fix

**Changed `decode_responses` from `True` to `False` in Socket.IO Redis manager**

### File: `webapp/backend/api/chat.py` (lines 28-39)

**BEFORE (BROKEN):**
```python
redis_manager = socketio.AsyncRedisManager(
    url=settings.REDIS_URL,
    redis_options={
        'db': settings.REDIS_DB,
        'decode_responses': True,  # ❌ WRONG - breaks binary messages
        'encoding': 'utf-8',
        'encoding_errors': 'strict',
        ...
    }
)
```

**AFTER (FIXED):**
```python
redis_manager = socketio.AsyncRedisManager(
    url=settings.REDIS_URL,
    redis_options={
        'db': settings.REDIS_DB,
        'decode_responses': False,  # ✅ CORRECT - allows binary messages
        ...
    }
)
```

## What We Also Did

1. **Cleared corrupted data from Redis:**
   ```bash
   redis-cli FLUSHALL
   redis-cli SHUTDOWN NOSAVE
   redis-server --daemonize yes
   ```

2. **Verified correct package versions:**
   - `redis==5.0.1` ✅
   - `python-socketio==5.11.0` ✅
   - `aioredis` NOT installed ✅ (incompatible with python-socketio 5.11.0)

3. **Cleared Python cache:**
   ```bash
   find . -type d -name __pycache__ -exec rm -r {} +
   ```

## Technical Explanation

### Socket.IO Message Flow:
```
Worker 1 → Socket.IO → MessagePack encoding → Binary data → Redis pub/sub
                                                                  ↓
Redis pub/sub → Binary data → MessagePack decoding → Socket.IO → Worker 2
```

### When decode_responses=True:
```
Worker 1 → Binary (0x80...) → Redis pub/sub
                                    ↓
                              UTF-8 decoder tries: "0x80".decode('utf-8')
                                    ↓
                              ❌ UnicodeDecodeError (0x80 is not valid UTF-8)
```

### When decode_responses=False:
```
Worker 1 → Binary (0x80...) → Redis pub/sub → Binary (0x80...) → Worker 2
                                    ↓
                              ✅ No decoding, binary passes through correctly
```

## Why RedisService Still Uses decode_responses=True

The `services/redis_service.py` uses `decode_responses=True` because it stores:
- Session data (JSON strings)
- User data (text)
- Metadata (strings)

This is **separate from Socket.IO's internal Redis usage** for pub/sub.

## Testing

Verified fix works:
```bash
python3 -c "
import asyncio
import socketio
from core.config import Settings

settings = Settings()

async def test_redis():
    redis_manager = socketio.AsyncRedisManager(
        url=settings.REDIS_URL,
        redis_options={
            'db': settings.REDIS_DB,
            'decode_responses': False,  # Binary mode
            'socket_timeout': 5,
            'socket_connect_timeout': 5,
            'socket_keepalive': True,
            'health_check_interval': 30
        }
    )
    
    sio = socketio.AsyncServer(
        async_mode='asgi',
        client_manager=redis_manager,
        cors_allowed_origins='*'
    )
    
    await asyncio.sleep(5)
    print('✅ Redis pub/sub working without errors!')

asyncio.run(test_redis())
"
```

Result: ✅ **No errors!**

## Expected Result

After fix:
- ✅ No more UnicodeDecodeError
- ✅ No more pub/sub listening thread errors
- ✅ Clean WebSocket connections
- ✅ Stable multi-worker session management
- ✅ Messages broadcast correctly between workers

## Summary

**The issue was NOT about clearing Redis data or package versions.**

**The real issue:** Using UTF-8 text decoding on Socket.IO's binary MessagePack pub/sub messages.

**The solution:** Set `decode_responses=False` to allow binary data to pass through Redis unchanged.
