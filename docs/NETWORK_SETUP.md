# Network Access Setup Guide

## Overview

This guide explains how to configure your RAG system for **network access** within your local network (LAN). Your PC will act as the **server** (hosting PostgreSQL, Ollama LLM, and FastAPI backend), while other devices on the same network can access the application through their **web browsers only** (no installation required).

---

## Current Architecture

### Server Components (Your PC)
- **PostgreSQL Database**: `localhost:5432` (server-side only)
- **Ollama LLM**: `localhost:11434` (server-side only)
- **FastAPI Backend**: Currently bound to `127.0.0.1:8000` (localhost only)
- **React Frontend**: Port 3000 (development) or served via backend (production)

### Network Information
- **Server Local IP**: `172.22.218.226` (your current WSL2 IP)
  - To check: `hostname -I | awk '{print $1}'`
  - **Note**: WSL2 IP may change on restart. Check before each session or configure static IP.

---

## Configuration Steps

### Step 1: Backend Network Binding

#### 1.1 Update Backend Environment File
**File**: `webapp/backend/.env`

**Change this:**
```env
HOST=127.0.0.1
PORT=8000
```

**To this:**
```env
HOST=0.0.0.0
PORT=8000
```

**Explanation**:
- `127.0.0.1` = localhost only (current setup)
- `0.0.0.0` = accept connections from any network interface

**Keep unchanged:**
```env
DATABASE_URL=postgresql://rag_user:secure_rag_password_2024@localhost:5432/rag_database
OLLAMA_BASE_URL=http://localhost:11434
```
*(PostgreSQL and Ollama stay on localhost - they're server-side only)*

---

#### 1.2 Update CORS Configuration
**File**: `webapp/backend/main.py`

**Find lines 84-96** (CORS middleware):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost",
        "https://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

**Change to:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.22.218.226:3000",    # Your server IP - Dev server
        "http://172.22.218.226:8000",    # Your server IP - Production
        "*"                               # Allow all (for testing only!)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

**Security Note**:
- Use `"*"` for testing only
- For production, list specific client IPs: `"http://192.168.1.50:*"`
- Or use domain-based origins if you set up DNS

---

#### 1.3 Update Backend Config Validation
**File**: `webapp/backend/core/config.py`

**Find line 82-87** (host validator):
```python
@field_validator("HOST")
@classmethod
def validate_host(cls, v):
    """Ensure host is localhost for security"""
    if v not in ["127.0.0.1", "localhost", "0.0.0.0"]:
        raise ValueError("Host must be localhost for security compliance")
    return v
```

**Already allows** `0.0.0.0` - No change needed! ✅

---

### Step 2: Frontend Configuration

#### 2.1 Update Frontend Environment File
**File**: `webapp/frontend/.env`

**Change from:**
```env
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_WS_URL=http://127.0.0.1:8000
PORT=3000
```

**To:**
```env
REACT_APP_API_URL=http://172.22.218.226:8000
REACT_APP_WS_URL=http://172.22.218.226:8000
PORT=3000
```

**Replace** `172.22.218.226` with your actual server IP if different.

---

#### 2.2 Update Frontend Config TypeScript
**File**: `webapp/frontend/src/config/config.ts`

**Find lines 64-75** (security validation):
```typescript
export const validateSecurityConfig = (): boolean => {
  const urls = [config.api.baseUrl, config.websocket.url];

  for (const url of urls) {
    if (!url.includes('localhost') && !url.includes('127.0.0.1')) {
      console.error('🚨 SECURITY VIOLATION: Non-localhost URL detected:', url);
      return false;
    }
  }

  return true;
};
```

**Option A: Disable validation completely** (easiest):
```typescript
export const validateSecurityConfig = (): boolean => {
  // Network access enabled - validation disabled
  return true;
};
```

**Option B: Allow specific network IPs**:
```typescript
export const validateSecurityConfig = (): boolean => {
  const urls = [config.api.baseUrl, config.websocket.url];
  const allowedHosts = ['localhost', '127.0.0.1', '172.22.218.226']; // Your server IP

  for (const url of urls) {
    const isAllowed = allowedHosts.some(host => url.includes(host));
    if (!isAllowed) {
      console.error('🚨 SECURITY VIOLATION: Non-allowed URL detected:', url);
      return false;
    }
  }

  return true;
};
```

---

### Step 3: Build React for Production (Recommended)

#### 3.1 Build Frontend
```bash
cd webapp/frontend
npm run build
```

This creates optimized production build in `webapp/frontend/build/`

#### 3.2 Copy Build to Backend
```bash
# Create static directory in backend
mkdir -p webapp/backend/static

# Copy built files
cp -r webapp/frontend/build/* webapp/backend/static/
```

#### 3.3 Verify Static Files Serving
**File**: `webapp/backend/main.py` (lines 131-134)

```python
# Mount static files for React frontend
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
```

**Already configured!** ✅

---

### Step 4: Firewall Configuration

#### 4.1 Linux Firewall (WSL/Ubuntu)
```bash
# Allow FastAPI backend port
sudo ufw allow 8000/tcp

# Allow React dev server port (if using development mode)
sudo ufw allow 3000/tcp

# Enable firewall (if not already enabled)
sudo ufw enable

# Check status
sudo ufw status
```

---

#### 4.2 Windows Firewall (Required for WSL2)

**Open PowerShell as Administrator** and run:

```powershell
# Allow FastAPI backend
netsh advfirewall firewall add rule name="RAG Backend Port 8000" dir=in action=allow protocol=TCP localport=8000

# Allow React dev server (optional)
netsh advfirewall firewall add rule name="RAG Frontend Port 3000" dir=in action=allow protocol=TCP localport=3000

# Verify rules
netsh advfirewall firewall show rule name="RAG Backend Port 8000"
```

---

### Step 5: WSL2 Port Forwarding (CRITICAL)

WSL2 uses **NAT networking**, so Windows cannot directly access WSL2 ports from external devices. You need port forwarding.

#### 5.1 Find Your WSL2 IP
```bash
# Inside WSL2
hostname -I | awk '{print $1}'
# Example output: 172.22.218.226
```

#### 5.2 Configure Port Forwarding
**On Windows (PowerShell as Administrator):**

```powershell
# Port forward from Windows to WSL2
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=172.22.218.226

# If using dev server on port 3000
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=172.22.218.226

# Verify port forwarding rules
netsh interface portproxy show v4tov4
```

**Important Notes:**
- **Run on every WSL2 restart** (WSL2 IP changes)
- Consider creating a PowerShell script to automate this
- Or configure static WSL2 IP in `.wslconfig`

#### 5.3 Automate WSL2 Port Forwarding (Optional)

**Create**: `setup_wsl_ports.ps1` (Windows PowerShell script)

```powershell
# Get WSL2 IP dynamically
$wslIP = (wsl hostname -I).Trim()
Write-Host "WSL2 IP: $wslIP"

# Remove old port forwarding rules
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0

# Add new port forwarding rules
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIP
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIP

Write-Host "Port forwarding configured successfully!"
netsh interface portproxy show v4tov4
```

**Run on every boot**: `PowerShell -ExecutionPolicy Bypass -File setup_wsl_ports.ps1`

---

### Step 6: Get Windows Host IP (For Client Access)

Clients need your **Windows machine's IP** (not WSL2 IP).

**On Windows (PowerShell or CMD):**
```powershell
ipconfig
```

**Look for**:
- **Ethernet adapter** (wired): `IPv4 Address`
- **Wi-Fi adapter** (wireless): `IPv4 Address`

**Example output:**
```
Wireless LAN adapter Wi-Fi:
   IPv4 Address. . . . . . . . . . . : 192.168.1.100
```

This is the IP clients will use: `http://192.168.1.100:8000`

---

## Deployment Options

### Option A: Development Mode (Two Servers)

**Use when**: Actively developing frontend

**Start Backend:**
```bash
cd webapp/backend
python main.py
# Backend runs on: http://0.0.0.0:8000
```

**Start Frontend (separate terminal):**
```bash
cd webapp/frontend
npm start
# Frontend runs on: http://0.0.0.0:3000
```

**Client Access:**
- Development: `http://192.168.1.100:3000` (Windows host IP)
- Hot reload enabled for development

---

### Option B: Production Mode (Single Server) ⭐ RECOMMENDED

**Use when**: Deploying for end users

**Steps:**
1. Build frontend: `cd webapp/frontend && npm run build`
2. Copy to backend: `cp -r build/* ../backend/static/`
3. Start backend only: `cd ../backend && python main.py`

**Client Access:**
- Production: `http://192.168.1.100:8000` (Windows host IP)
- Single endpoint for everything (API + React UI)

---

## Testing the Setup

### On Server (Your PC)

1. **Start PostgreSQL:**
   ```bash
   sudo service postgresql start
   # Or: sudo systemctl start postgresql
   ```

2. **Start Ollama:**
   ```bash
   ollama serve
   ```

3. **Start Backend:**
   ```bash
   cd webapp/backend
   python main.py
   ```

4. **Check Backend Health:**
   ```bash
   curl http://localhost:8000/api/health
   ```

   **Expected response:**
   ```json
   {
     "status": "healthy",
     "version": "1.0.0",
     "security_mode": "local_only",
     "external_dependencies": "none"
   }
   ```

---

### On Client PC (Same Network)

1. **Find server IP** (Windows host IP): `192.168.1.100` (example)

2. **Test backend from browser:**
   ```
   http://192.168.1.100:8000/api/health
   ```

3. **Access application:**
   - Development: `http://192.168.1.100:3000`
   - Production: `http://192.168.1.100:8000`

4. **Test functionality:**
   - Register account
   - Upload document
   - Start chat with RAG
   - Verify real-time features (WebSocket)

---

## Troubleshooting

### Issue 1: Cannot Access from Client

**Symptoms**: Browser shows "Cannot connect" or timeout

**Checks:**
1. Verify server is running: `curl http://localhost:8000/api/health` (on server)
2. Check firewall rules: `sudo ufw status` (Linux), `netsh advfirewall firewall show rule name=all` (Windows)
3. Verify port forwarding: `netsh interface portproxy show v4tov4` (Windows)
4. Confirm WSL2 IP: `hostname -I` (WSL)
5. Ping server from client: `ping 192.168.1.100` (client)

**Solutions:**
- Restart firewalls: `sudo ufw reload` (Linux)
- Re-run port forwarding setup: `setup_wsl_ports.ps1` (Windows)
- Check Windows host IP hasn't changed: `ipconfig` (Windows)

---

### Issue 2: CORS Errors in Browser Console

**Symptoms**:
```
Access to XMLHttpRequest at 'http://192.168.1.100:8000' from origin 'http://192.168.1.100:3000'
has been blocked by CORS policy
```

**Solutions:**
1. Update CORS origins in `main.py` (Step 1.2 above)
2. Add client IP to allowed origins
3. Temporarily use `allow_origins=["*"]` for testing
4. Restart backend after changes

---

### Issue 3: WebSocket Connection Failed

**Symptoms**: Chat doesn't work, "Disconnected" status in UI

**Checks:**
1. Verify WebSocket URL in frontend `.env`: `REACT_APP_WS_URL=http://192.168.1.100:8000`
2. Check browser console for WebSocket errors
3. Verify Socket.IO is properly mounted in `main.py:216`

**Solutions:**
- Ensure Socket.IO uses same port as backend (8000)
- Update WebSocket URL in frontend config
- Check firewall allows WebSocket connections (same port as HTTP)

---

### Issue 4: WSL2 IP Changes After Restart

**Symptoms**: Clients cannot connect after WSL restart

**Solutions:**

**Option A: Re-run port forwarding** (Quick fix)
```powershell
# Windows PowerShell (Admin)
.\setup_wsl_ports.ps1
```

**Option B: Configure static WSL2 IP** (Permanent fix)

**Create/edit**: `C:\Users\<YourUsername>\.wslconfig`
```ini
[wsl2]
networkingMode=bridged
vmSwitch=WSLSwitch
```

Then create external virtual switch in Hyper-V Manager named "WSLSwitch"

**Option C: Use Windows hostname instead of IP**
- Configure local DNS or hosts file
- Update frontend URLs to use hostname: `http://YOUR-PC-NAME:8000`

---

### Issue 5: Slow Performance from Clients

**Symptoms**: App is slow when accessed from other PCs

**Possible causes:**
1. Network bandwidth issues
2. LLM processing taking time (expected)
3. Database queries slow

**Optimizations:**
1. Use production build (minified, optimized)
2. Enable PostgreSQL connection pooling
3. Check network speed: `iperf3` between server and client
4. Monitor server resources: `htop`, `nvidia-smi` (if using GPU)

---

## Security Considerations

### Current Setup: LAN-Only Access
✅ **Safe for home/office networks**
- Not exposed to internet
- All data stays on local network
- No external API dependencies

### Additional Security Measures

#### 1. Enable HTTPS (Recommended for production)
**Generate self-signed certificate:**
```bash
openssl req -x509 -newkey rsa:4096 -nodes -keyout key.pem -out cert.pem -days 365
```

**Update backend `.env`:**
```env
SSL_KEYFILE=key.pem
SSL_CERTFILE=cert.pem
```

**Update URLs to use HTTPS:**
- Backend: `https://192.168.1.100:8000`
- Frontend: `https://192.168.1.100:8000`

**Note**: Browsers will show "Not secure" warning for self-signed certs (expected)

---

#### 2. Restrict CORS to Specific IPs
**File**: `main.py`

```python
allow_origins=[
    "http://192.168.1.50",    # Alice's laptop
    "http://192.168.1.51",    # Bob's desktop
    "http://192.168.1.100",   # Your server
]
```

---

#### 3. Enable Authentication
Your app already has authentication! Ensure users:
- Create strong passwords
- Don't share credentials
- Use unique accounts per person

---

#### 4. Network Segmentation
- Keep RAG system on private VLAN
- Use firewall rules to limit access to specific devices
- Consider VPN for remote access instead of port forwarding to internet

---

## Production Deployment Checklist

Before deploying to multiple users:

- [ ] Frontend built and copied to `backend/static/`
- [ ] Backend `.env` configured with `HOST=0.0.0.0`
- [ ] Frontend `.env` points to server IP
- [ ] CORS configured with allowed origins
- [ ] Security validation updated in frontend config
- [ ] Firewall rules configured (Linux + Windows)
- [ ] WSL2 port forwarding configured
- [ ] PostgreSQL running and accessible
- [ ] Ollama running with required models
- [ ] Health check endpoint accessible: `/api/health`
- [ ] Tested from at least one client device
- [ ] WebSocket connections working
- [ ] File upload/download working
- [ ] Chat with RAG working
- [ ] User authentication working
- [ ] HTTPS enabled (optional but recommended)
- [ ] Backup strategy in place for database

---

## Quick Reference

### Server URLs (Internal - WSL2)
- Backend API: `http://172.22.218.226:8000`
- Frontend Dev: `http://172.22.218.226:3000`

### Client URLs (External - From other PCs)
- Production: `http://192.168.1.100:8000` (Windows host IP)
- Development: `http://192.168.1.100:3000` (Windows host IP)

### Key Commands

**Start services:**
```bash
# PostgreSQL
sudo service postgresql start

# Ollama (separate terminal)
ollama serve

# Backend
cd webapp/backend && python main.py
```

**Build and deploy:**
```bash
# Build frontend
cd webapp/frontend && npm run build

# Copy to backend
cp -r build/* ../backend/static/

# Start production server
cd ../backend && python main.py
```

**Check status:**
```bash
# Backend health
curl http://localhost:8000/api/health

# PostgreSQL
sudo service postgresql status

# Ollama
curl http://localhost:11434/api/tags
```

---

## Summary

After completing all steps:
1. ✅ Your PC runs all services (PostgreSQL, Ollama, FastAPI)
2. ✅ Other devices access via web browser only
3. ✅ Single URL for clients: `http://<YOUR_WINDOWS_IP>:8000`
4. ✅ All processing happens on your server
5. ✅ No installation required on client devices
6. ✅ LAN-only access (not exposed to internet)

**Client experience:**
- Open browser → Enter URL → Login → Use RAG system
- Zero installation, zero configuration on client side

---

## Support

If you encounter issues not covered in troubleshooting:
1. Check logs: `webapp/backend/logs/rag_app.log`
2. Verify all services running: PostgreSQL, Ollama, FastAPI
3. Test each component individually (database → backend → frontend)
4. Review browser console for client-side errors
5. Check network connectivity: ping, traceroute, firewall logs
