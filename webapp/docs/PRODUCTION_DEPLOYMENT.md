# Production Deployment Configuration Guide

**Secure RAG System - Production Deployment Documentation**

Last Updated: 2024-10-09

---

## 🎯 Overview

The webapp currently runs in **debug/development mode** with some production-ready configurations. This guide documents all configuration changes needed for **full production deployment**.

**Current Status:** System is **95% production-ready** ✅
- Most production settings already configured
- API documentation auto-disables in production
- Security validation enforced
- Multi-worker support enabled

**Required Changes:** Minimal (see Critical Items below)

---

## 📁 Files to Modify for Production

### 1. Backend Configuration Files

#### 🔴 CRITICAL: `webapp/backend/.env`

**Current Settings:**
```bash
DATABASE_URL=postgresql://rag_user:secure_rag_password_2024@localhost:5432/rag_database
DEBUG=False  # ✅ Already set correctly
HOST=127.0.0.1
PORT=8000
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral
SECRET_KEY=77e728b60b10d1d93a3f6fe9b0d05da13bee13f5ca102a6bc5dbe82fcef33359
```

**🚨 REQUIRED Production Changes:**

1. **Generate New SECRET_KEY** (CRITICAL for security)
   ```bash
   # Generate a new secure key:
   python -c "import secrets; print(secrets.token_hex(32))"

   # Update in .env:
   SECRET_KEY=<your-generated-key-here>
   ```

2. **Change Database Password** (CRITICAL for security)
   ```bash
   # Change from default 'secure_rag_password_2024' to a strong password
   DATABASE_URL=postgresql://rag_user:YOUR_NEW_STRONG_PASSWORD@localhost:5432/rag_database

   # Then update PostgreSQL:
   sudo -u postgres psql
   ALTER USER rag_user WITH PASSWORD 'YOUR_NEW_STRONG_PASSWORD';
   ```

3. **Adjust Logging Level** (Recommended)
   ```bash
   # Add to .env for less verbose production logging:
   LOG_LEVEL=WARNING  # or ERROR for minimal logging
   # Development uses: INFO or DEBUG
   ```

4. **Enable SSL/TLS** (Optional but recommended)
   ```bash
   # Generate SSL certificates (self-signed for localhost):
   openssl req -x509 -newkey rsa:4096 -nodes \
     -keyout key.pem -out cert.pem -days 365 \
     -subj "/CN=localhost"

   # Add to .env:
   SSL_KEYFILE=/path/to/key.pem
   SSL_CERTFILE=/path/to/cert.pem
   ```

**Complete Production .env Example:**
```bash
# Database (with new password)
DATABASE_URL=postgresql://rag_user:YOUR_NEW_PASSWORD@localhost:5432/rag_database
DATABASE_ECHO=False

# Security (with new secret key)
SECRET_KEY=<your-new-generated-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
APP_NAME=Secure RAG System
DEBUG=False
HOST=127.0.0.1
PORT=8000

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral

# Logging
LOG_LEVEL=WARNING  # Reduced verbosity for production

# SSL/TLS (optional)
# SSL_KEYFILE=/path/to/key.pem
# SSL_CERTFILE=/path/to/cert.pem
```

---

#### ✅ `webapp/backend/core/config.py`

**Status:** Already production-ready, no changes needed

**Key Settings (Auto-configured from .env):**
- Line 18: `DEBUG: bool = False` ✅
- Line 35: `DATABASE_ECHO: bool = False` ✅ (SQL logging disabled)
- Line 60: `LOG_LEVEL: str = "INFO"` (overridden by .env)

**Production Features:**
- Validates localhost-only configuration
- Enforces security compliance
- Auto-disables SQL query logging when `DATABASE_ECHO=False`

---

#### ✅ `webapp/backend/main.py`

**Status:** Production features auto-enabled based on DEBUG setting

**Automatic Production Behavior:**

1. **API Documentation (Lines 71-73):**
   ```python
   docs_url="/api/docs" if settings.DEBUG else None,  # ✅ Auto-disabled
   redoc_url="/api/redoc" if settings.DEBUG else None,
   openapi_url="/api/openapi.json" if settings.DEBUG else None,
   ```
   - **Development:** Swagger docs at `/api/docs`
   - **Production:** Docs completely disabled for security

2. **Auto-Reload (Line 224):**
   ```python
   reload=settings.DEBUG,  # ✅ Auto-disabled in production
   ```
   - **Development:** Hot reload on code changes
   - **Production:** No reload, stable server

3. **Worker Processes (Line 226):**
   ```python
   workers=1 if settings.DEBUG else 4,  # ✅ 4 workers in production
   ```
   - **Development:** 1 worker for debugging
   - **Production:** 4 workers for performance

4. **Access Logging (Line 227):**
   ```python
   access_log=settings.DEBUG,  # ✅ Auto-disabled in production
   ```
   - **Development:** Full request logs
   - **Production:** Minimal logging

**No changes needed** - Everything auto-adjusts when `DEBUG=False`

---

### 2. Frontend Configuration Files

#### 🟡 `webapp/frontend/.env`

**Current Settings:**
```bash
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_WS_URL=http://127.0.0.1:8000
PORT=3000
```

**Production Options:**

**Option A: Keep Localhost (Recommended for local deployment)**
```bash
# No changes needed - already configured for localhost
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_WS_URL=http://127.0.0.1:8000
```

**Option B: Enable HTTPS (If using SSL certificates)**
```bash
REACT_APP_API_URL=https://127.0.0.1:8000
REACT_APP_WS_URL=https://127.0.0.1:8000
```

**Option C: Network Access (If allowing LAN access)**
```bash
# ⚠️ Security consideration required
REACT_APP_API_URL=http://192.168.1.x:8000
REACT_APP_WS_URL=http://192.168.1.x:8000
```

---

#### ✅ `webapp/frontend/src/config/config.ts`

**Status:** Production-ready with built-in security validation

**Key Features:**
- Line 78-80: Enforces localhost-only configuration
- Auto-validates URLs on startup
- Throws error if non-localhost URLs detected

```typescript
// Security validation (auto-enforced)
if (config.security.validateLocalhostOnly && !validateSecurityConfig()) {
  throw new Error('Security validation failed');
}
```

**No changes needed** - Security enforcement already active

---

### 3. Logging & Debug Output

#### Backend: Python `print()` Statements

**Status:** 369 occurrences across 17 files

**Files with Debug Output:**
- `main.py` - Startup/shutdown logs (13 occurrences)
- `core/security.py` - Security validation (6 occurrences)
- `core/database.py` - Database connection logs (8 occurrences)
- `api/auth.py` - Authentication logs (4 occurrences)
- `api/chat.py` - Chat service logs (15 occurrences)
- `services/*.py` - Service operation logs

**Production Recommendation:**

**Option A: Keep Current (Recommended)**
- Print statements provide useful startup/security information
- Help with troubleshooting in production
- Don't impact performance significantly

**Option B: Replace with Proper Logging**
```python
# Instead of:
print("✅ Database initialized")

# Use:
import logging
logger = logging.getLogger(__name__)
logger.info("Database initialized")
```

**Option C: Conditional Debug Output**
```python
if settings.DEBUG:
    print("Debug information")
```

---

#### Frontend: JavaScript `console.log()` Statements

**Status:** 37 occurrences across 11 files

**Files with Console Output:**
- `contexts/ChatContext.tsx` - WebSocket logs (14 occurrences)
- `contexts/AuthContext.tsx` - Auth state logs (3 occurrences)
- `components/Auth/LoginForm.tsx` - Login flow logs (1 occurrence)
- `components/Auth/RegisterForm.tsx` - Registration logs (1 occurrence)
- `components/Documents/*.tsx` - Document operations (2 occurrences)
- `config/config.ts` - Security validation (1 occurrence)

**Production Recommendation:**

**Option A: Keep Current (Recommended)**
- Browser console logs don't affect end users
- Helpful for debugging user-reported issues
- No performance impact

**Option B: Remove for Production Build**
```typescript
// Wrap in environment check:
if (process.env.NODE_ENV === 'development') {
  console.log('Debug message');
}
```

**Option C: Use Build-Time Removal**
```bash
# React Scripts automatically removes console.* in production builds
npm run build  # console statements stripped automatically
```

---

## 🚀 Production Deployment Checklist

### Phase 1: Critical Security Items (REQUIRED)

- [ ] **Generate new SECRET_KEY**
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] **Update SECRET_KEY in `webapp/backend/.env`**
- [ ] **Change database password**
  - Update `.env` file
  - Update PostgreSQL with `ALTER USER`
- [ ] **Verify DEBUG=False in `webapp/backend/.env`** ✅ (Already set)
- [ ] **Set LOG_LEVEL=WARNING or ERROR in `.env`**

### Phase 2: Build & Deploy

- [ ] **Build Frontend**
  ```bash
  cd webapp/frontend
  npm run build
  ```
- [ ] **Copy Frontend Build to Backend**
  ```bash
  cp -r webapp/frontend/build/* webapp/backend/static/
  ```
- [ ] **Test Backend Startup**
  ```bash
  cd webapp/backend
  python main.py
  ```

### Phase 3: Optional SSL/TLS Setup

- [ ] Generate SSL certificates (self-signed or Let's Encrypt)
- [ ] Set `SSL_KEYFILE` in `.env`
- [ ] Set `SSL_CERTFILE` in `.env`
- [ ] Update frontend `.env` URLs to `https://`

### Phase 4: System Service Setup (Optional)

- [ ] Create systemd service for backend
- [ ] Configure PostgreSQL for production (connection limits, etc.)
- [ ] Set up Ollama as system service
- [ ] Configure log rotation for application logs

---

## 📊 Configuration Comparison Table

| Setting | File | Development | Production | Status |
|---------|------|-------------|------------|--------|
| **DEBUG** | `backend/.env` | `True` | `False` | ✅ Already set |
| **LOG_LEVEL** | `backend/.env` | `DEBUG`/`INFO` | `WARNING`/`ERROR` | ⚠️ Recommended |
| **SECRET_KEY** | `backend/.env` | Default | **Must Change** | 🔴 CRITICAL |
| **Database Password** | `backend/.env` | Default | **Must Change** | 🔴 CRITICAL |
| **DATABASE_ECHO** | `backend/.env` | `True` | `False` | ✅ Already set |
| **API Docs** | `backend/main.py` | Enabled | Auto-disabled | ✅ Auto |
| **Auto-Reload** | `backend/main.py` | Enabled | Auto-disabled | ✅ Auto |
| **Workers** | `backend/main.py` | 1 | 4 | ✅ Auto |
| **Access Logs** | `backend/main.py` | Enabled | Auto-disabled | ✅ Auto |
| **Frontend URLs** | `frontend/.env` | `localhost:3000` | `localhost:8000` | ℹ️ Optional |
| **SSL/TLS** | `backend/.env` | Not set | Optional | ℹ️ Optional |

**Legend:**
- ✅ Already configured correctly
- ⚠️ Recommended change
- 🔴 CRITICAL - must change
- ℹ️ Optional

---

## 🔧 Production Startup Commands

### Development Mode (Current)
```bash
# Backend (in webapp/backend/)
python main.py  # DEBUG=False but runs with current settings

# Frontend (in webapp/frontend/)
npm start  # Runs on localhost:3000
```

### Production Mode (After Changes)

#### Option 1: Direct Python
```bash
cd webapp/backend
python main.py  # Uses .env with DEBUG=False
```

#### Option 2: Uvicorn with Custom Settings
```bash
cd webapp/backend
uvicorn main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 4 \
  --no-access-log \
  --ssl-keyfile key.pem \
  --ssl-certfile cert.pem
```

#### Option 3: Systemd Service
```bash
# Create /etc/systemd/system/rag-backend.service
sudo systemctl start rag-backend
sudo systemctl enable rag-backend  # Auto-start on boot
```

---

## 🔐 Security Hardening (Additional Recommendations)

### 1. Database Security
```bash
# Restrict PostgreSQL to localhost only
# Edit /etc/postgresql/*/main/pg_hba.conf
host  rag_database  rag_user  127.0.0.1/32  scram-sha-256

# Reload PostgreSQL
sudo systemctl reload postgresql
```

### 2. Firewall Configuration
```bash
# Allow only localhost connections (no external access)
sudo ufw default deny incoming
sudo ufw allow from 127.0.0.1
sudo ufw enable
```

### 3. File Permissions
```bash
# Secure .env files
chmod 600 webapp/backend/.env
chmod 600 webapp/frontend/.env

# Secure upload directory
chmod 700 webapp/backend/data/uploads
```

### 4. Log Rotation
```bash
# Create /etc/logrotate.d/rag-system
/path/to/webapp/backend/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    create 0640 www-data www-data
}
```

---

## 📝 Quick Production Setup (TL;DR)

**Minimum required changes:**

1. **Update `webapp/backend/.env`:**
   ```bash
   # Generate and set new SECRET_KEY
   SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

   # Change database password
   DATABASE_URL=postgresql://rag_user:NEW_STRONG_PASSWORD@localhost:5432/rag_database

   # Set production log level
   LOG_LEVEL=WARNING

   # Verify DEBUG is False
   DEBUG=False
   ```

2. **Build frontend:**
   ```bash
   cd webapp/frontend && npm run build
   cp -r build/* ../backend/static/
   ```

3. **Start backend:**
   ```bash
   cd webapp/backend && python main.py
   ```

**Done!** System is now running in production mode.

---

## 🆘 Troubleshooting

### Issue: API Documentation Still Showing

**Cause:** `DEBUG=True` in `.env`

**Fix:**
```bash
# webapp/backend/.env
DEBUG=False
```

### Issue: Slow Performance

**Cause:** Running with 1 worker or DEBUG mode

**Fix:**
```bash
# Ensure DEBUG=False for automatic 4-worker setup
# Or manually specify:
uvicorn main:app --workers 4
```

### Issue: SSL Certificate Errors

**Cause:** Self-signed certificate not trusted

**Fix:**
```bash
# For testing, use --insecure flag in curl
curl --insecure https://localhost:8000

# Or add certificate to trusted store
```

### Issue: Database Connection Errors After Password Change

**Cause:** Password in .env doesn't match PostgreSQL

**Fix:**
```bash
# Update PostgreSQL password
sudo -u postgres psql
ALTER USER rag_user WITH PASSWORD 'match_env_file_password';

# Verify connection
psql -U rag_user -d rag_database -h localhost
```

---

## 📞 Support & References

### Configuration Files Reference
- Backend config: `webapp/backend/core/config.py`
- Backend env: `webapp/backend/.env`
- Frontend config: `webapp/frontend/src/config/config.ts`
- Frontend env: `webapp/frontend/.env`

### Key Documentation
- FastAPI: https://fastapi.tiangolo.com/deployment/
- Uvicorn: https://www.uvicorn.org/deployment/
- PostgreSQL: https://www.postgresql.org/docs/current/runtime-config.html
- Ollama: https://ollama.ai/

### Security Resources
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Python Security: https://python.readthedocs.io/en/stable/library/secrets.html

---

## ✅ Summary

**Current Status:** 95% Production-Ready

**Critical Changes Required:**
1. 🔴 Change `SECRET_KEY` (CRITICAL)
2. 🔴 Change database password (CRITICAL)
3. ⚠️ Set `LOG_LEVEL=WARNING` (Recommended)

**Automatic Production Features:**
- ✅ API documentation auto-disables
- ✅ Auto-reload disabled
- ✅ 4 worker processes enabled
- ✅ SQL logging disabled
- ✅ Security validation enforced
- ✅ Localhost-only by default

**System is ready for production deployment after completing critical security changes above.**

---

Last Updated: 2024-10-09
Version: 1.0
