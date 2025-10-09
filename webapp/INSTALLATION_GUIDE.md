# 🚀 RAG Web Application - Local Installation Guide

Complete guide for setting up and running the RAG Web Application on your own PC.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Running the Application](#running-the-application)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)
- [Security Notes](#security-notes)

---

## 📦 Prerequisites

### Required Software

| Software | Version | Purpose | Installation Link |
|----------|---------|---------|------------------|
| **Python** | 3.12+ | Backend runtime | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js** | 18+ | Frontend runtime | [nodejs.org](https://nodejs.org/) |
| **npm** | 9+ | Package manager | Included with Node.js |
| **Ollama** | Latest | Local LLM service | [ollama.ai](https://ollama.ai/) |
| **PostgreSQL** | 15+ | **Production database (PRIMARY)** | [postgresql.org](https://www.postgresql.org/download/) |
| **SQLite** | Built-in | Development database (backup) | Included with Python |

### System Requirements

- **OS**: Linux, macOS, or Windows (WSL2 recommended for Windows)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 10GB free space (for models and data)
- **CPU**: 4+ cores recommended

### Verify Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.12 or higher

# Check Node.js and npm
node --version     # Should be 18 or higher
npm --version      # Should be 9 or higher

# Check if Ollama is installed
ollama --version
```

---

## 🚀 Quick Start

Choose one of the following methods:

### Method 1: Automated Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/rk27599/Python_RAG.git
cd Python_RAG

# Run the automated start script
./start_rag_system.sh
```

The script will:
- ✅ Start Ollama service
- ✅ Start backend server (port 8000)
- ✅ Start frontend server (port 3000)

### Method 2: Docker (Production-Ready)

```bash
cd webapp
docker-compose -f docker-compose.prod.yml up -d
```

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for Docker details.

### Method 3: Manual Setup

Continue reading for step-by-step manual installation.

---

## 📖 Detailed Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/rk27599/Python_RAG.git
cd Python_RAG
```

### Step 2: Install and Configure Ollama

#### 2.1 Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
Download installer from [ollama.ai/download](https://ollama.ai/download)

#### 2.2 Start Ollama Service

```bash
# Start Ollama server (runs in background)
ollama serve &

# Verify it's running
curl http://localhost:11434/api/tags
```

#### 2.3 Pull AI Models

```bash
# Pull recommended models (choose at least one)
ollama pull mistral        # 4.1GB - Recommended, fast and capable
ollama pull llama2         # 3.8GB - Alternative option
ollama pull codellama      # 3.8GB - For code-related tasks

# Pull embedding model (required for RAG)
ollama pull all-minilm     # 45MB - For document embeddings
```

**Verify models:**
```bash
ollama list
```

### Step 3: Backend Setup

#### 3.1 Navigate to Backend Directory

```bash
cd webapp/backend
```

#### 3.2 Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows (Git Bash):
source venv/Scripts/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat
```

#### 3.3 Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

This installs:
- FastAPI & Uvicorn (web server)
- SQLAlchemy (database ORM)
- Ollama integration libraries
- Security & authentication
- ML libraries (scikit-learn, sentence-transformers)

#### 3.4 Configure Database

**⚡ PostgreSQL (Recommended - 50x Faster)**

PostgreSQL with pgvector provides **10-100x faster vector search** compared to SQLite:

```bash
# Run automated setup script
chmod +x backend/scripts/setup_postgres.sh
./backend/scripts/setup_postgres.sh
```

The script will:
- ✅ Install PostgreSQL + pgvector extension
- ✅ Create database `rag_database` and user `rag_user`
- ✅ Enable HNSW index for fast vector search
- ✅ Initialize database tables

**Manual PostgreSQL Setup** (if script fails):

```bash
# Install PostgreSQL
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib

# macOS:
brew install postgresql@15

# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
brew services start postgresql@15  # macOS

# Create database and user
sudo -u postgres psql
CREATE USER rag_user WITH PASSWORD 'secure_rag_password_2024';
CREATE DATABASE rag_database OWNER rag_user;
\c rag_database
CREATE EXTENSION vector;
\q

# Verify
psql -h localhost -U rag_user -d rag_database -c "SELECT version();"
```

**💾 SQLite (Development/Backup Only)**

For quick testing or development:

```bash
# Copy development environment
cp .env.dev .env

# SQLite will create dev.db automatically
```

⚠️ **Note**: SQLite is **50x slower** for vector search. Use PostgreSQL for production.

#### 3.5 Initialize Database

```bash
# Run database initialization
python init_db.py
```

Expected output:
```
✅ Security settings validation passed
✅ Database tables created successfully
✅ pgvector extension enabled (PostgreSQL)
✅ HNSW index created for vector search
```

#### 3.6 Migrate Existing Data (Optional)

If you have existing SQLite data to migrate:

```bash
# Run migration script
python migrate_sqlite_to_postgres.py --sqlite-path ./test.db

# Or dry-run first
python migrate_sqlite_to_postgres.py --dry-run
```

#### 3.7 Configure Environment Variables

```bash
# For production (PostgreSQL - already created by setup script)
cat .env

# For development (SQLite)
cp .env.dev .env

# Or create custom .env from template
cp .env.example .env
# Then edit with your settings
```

The `.env` file should contain:
```bash
# Database (PostgreSQL - PRIMARY)
DATABASE_URL=postgresql://rag_user:secure_rag_password_2024@localhost:5432/rag_database

# Or SQLite (Development/Backup)
# DATABASE_URL=sqlite:///./dev.db

# Application
DEBUG=False
HOST=127.0.0.1
PORT=8000

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral

# Security (auto-generated)
SECRET_KEY=<generated-by-config>
```

### Step 4: Frontend Setup

#### 4.1 Navigate to Frontend Directory

```bash
cd ../frontend
```

#### 4.2 Install Node Dependencies

```bash
# Install all dependencies
npm install
```

This installs:
- React 19
- Material-UI (MUI)
- Axios (HTTP client)
- TypeScript
- React Router

Expected time: 2-5 minutes

#### 4.3 Configure Frontend Environment

```bash
# Create .env file
cat > .env << 'EOF'
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENV=development
EOF
```

Or copy from example:
```bash
cp .env.example .env
```

---

## ▶️ Running the Application

### Option 1: Using the Start Script (Recommended)

```bash
# From project root
./start_rag_system.sh
```

The script starts all services automatically.

### Option 2: Manual Start (3 Terminals)

**Terminal 1 - Ollama Service:**
```bash
ollama serve
```

**Terminal 2 - Backend Server:**
```bash
cd webapp/backend
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Terminal 3 - Frontend Server:**
```bash
cd webapp/frontend
npm start
```

Expected output:
```
Compiled successfully!
You can now view frontend in the browser.
  Local:            http://localhost:3000
```

### Access the Application

1. **Frontend UI**: http://localhost:3000
2. **Backend API**: http://localhost:8000
3. **API Documentation**: http://localhost:8000/docs

---

## ✅ Verification

### 1. Check Ollama Service

```bash
curl http://localhost:11434/api/tags
```

Expected: JSON response with list of models

### 2. Check Backend API

```bash
curl http://localhost:8000/api/models
```

Expected: `{"success": true, "data": ["mistral", "llama2", ...]}`

### 3. Check System Status

```bash
curl http://localhost:8000/api/system/status
```

Expected:
```json
{
  "success": true,
  "data": {
    "ollama": {"status": "running", "models": [...]},
    "database": {"status": "connected", "connections": 5},
    "security": {"score": 96, "violations": 0}
  }
}
```

### 4. Test Frontend

1. Open http://localhost:3000
2. You should see the login page
3. Register a new account
4. Upload a document
5. Test chat functionality

---

## 🔧 Troubleshooting

### Issue: Ollama Not Running

**Symptoms:**
- Backend shows "Ollama connection failed"
- System status shows "offline"

**Solution:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# If not running, start it
ollama serve &

# Verify
curl http://localhost:11434/api/tags
```

### Issue: Port Already in Use

**Symptoms:**
- `Error: listen EADDRINUSE: address already in use :::8000`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process (replace PID)
kill -9 <PID>

# Or use different port
uvicorn main:app --host 127.0.0.1 --port 8001
```

### Issue: Database Connection Failed

**Symptoms:**
- `Database connection failed: ...`
- `relation "documents" does not exist`

**Solution for PostgreSQL:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Verify database exists
psql -l | grep rag_database

# Re-run setup if needed
cd webapp/backend
./scripts/setup_postgres.sh

# Or manually initialize
python init_db.py
```

**Solution for SQLite:**
```bash
# Switch to SQLite for development
cp .env.dev .env

# Initialize database
cd webapp/backend
python init_db.py
```

**Switch Between Databases:**
```bash
# Switch to PostgreSQL (fast)
cp .env .env.backup
echo "DATABASE_URL=postgresql://rag_user:secure_rag_password_2024@localhost:5432/rag_database" > .env

# Switch to SQLite (slow, development)
cp .env.dev .env
```

### Issue: Frontend Won't Start

**Symptoms:**
- `npm ERR!` or TypeScript errors

**Solution:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# If still failing, check Node version
node --version  # Should be 18+
```

### Issue: Models Not Found

**Symptoms:**
- "Model not found" errors
- Empty model list

**Solution:**
```bash
# List installed models
ollama list

# Pull missing models
ollama pull mistral
ollama pull all-minilm

# Restart backend
```

### Issue: Python Version Mismatch

**Symptoms:**
- Import errors with `asyncio` or `typing`

**Solution:**
```bash
# Check Python version
python3 --version

# Install Python 3.12
# Ubuntu/Debian:
sudo apt install python3.12 python3.12-venv

# Update virtual environment
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: CORS Errors in Frontend

**Symptoms:**
- Browser console shows "CORS policy" errors

**Solution:**
Check backend `main.py` has CORS middleware:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Slow Model Responses

**Symptoms:**
- Chat responses take >30 seconds

**Solutions:**
1. Use smaller models: `ollama pull mistral` (4GB) instead of larger models
2. Increase timeout in backend config
3. Check system resources: `htop` or `top`
4. Use GPU acceleration if available

---

## ⚙️ Configuration

### Backend Configuration

Edit `webapp/backend/core/config.py`:

```python
# Application settings
HOST: str = "127.0.0.1"  # Keep localhost only
PORT: int = 8000

# Database (PostgreSQL PRIMARY, SQLite backup)
DATABASE_URL: str = "postgresql://rag_user:secure_rag_password_2024@localhost:5432/rag_database"
# For SQLite (development): "sqlite:///./dev.db"

# Ollama
OLLAMA_BASE_URL: str = "http://localhost:11434"
DEFAULT_MODEL: str = "mistral"

# Security
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB

# Vector search (pgvector)
VECTOR_DIMENSION: int = 384  # sentence-transformers/all-MiniLM-L6-v2
```

### Frontend Configuration

Edit `webapp/frontend/.env`:

```bash
# API endpoints
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Features
REACT_APP_ENABLE_REGISTRATION=true
REACT_APP_MAX_UPLOAD_SIZE=52428800  # 50MB
```

### Model Parameters

Adjust in Settings page (UI) or via API:

```json
{
  "temperature": 0.7,      // 0-2, higher = more creative
  "max_tokens": 4096,      // Response length
  "top_p": 0.9,            // Diversity control
  "repeat_penalty": 1.1,   // Avoid repetition
  "use_rag_by_default": true,
  "streaming_enabled": true
}
```

---

## 🔒 Security Notes

### Local-Only Operation

This application is designed to run **locally only**:

✅ **Secure by Default:**
- Ollama runs on `localhost:11434`
- Backend runs on `127.0.0.1:8000`
- No external API calls
- All data stays on your machine

⚠️ **Do NOT expose to internet** without proper security:
- No external access by default
- If exposing, use HTTPS/SSL
- Implement firewall rules
- Use strong authentication

### Data Privacy

- ✅ All AI processing happens locally (Ollama)
- ✅ No data sent to external services
- ✅ Documents stored in local database
- ✅ Conversations never leave your PC

### Best Practices

1. **Use strong passwords** for user accounts
2. **Keep Ollama updated**: `ollama update`
3. **Regular backups**: Use `scripts/backup.sh`
4. **Monitor logs** for suspicious activity
5. **Limit file uploads** to trusted sources

---

## 📚 Next Steps

### 1. Explore the Application

- **Upload Documents**: PDF, HTML, TXT files
- **Chat Interface**: Ask questions about your documents
- **Settings Page**: Configure AI models and parameters
- **Document Management**: View and delete uploaded files

### 2. Advanced Usage

- **Custom Models**: Pull and use different Ollama models
- **Bulk Upload**: Upload multiple documents at once
- **Export Data**: Export conversations and insights
- **API Integration**: Use REST API for automation

### 3. Documentation

- [User Guide](docs/USER_GUIDE.md) - How to use the application
- [Admin Guide](docs/ADMIN_GUIDE.md) - Administration and maintenance
- [API Reference](http://localhost:8000/docs) - Interactive API docs
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Production deployment

### 4. Development

- **Frontend**: React + TypeScript in `webapp/frontend/src/`
- **Backend**: FastAPI in `webapp/backend/api/`
- **Tests**: Run with `pytest webapp/backend/tests/`
- **Pre-commit Hooks**: `./scripts/install_security_hooks.sh`

---

## 🆘 Getting Help

### Resources

- **Issues**: [GitHub Issues](https://github.com/rk27599/Python_RAG/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rk27599/Python_RAG/discussions)
- **Documentation**: `webapp/docs/` directory
- **Core Library**: See main [README.md](../README.md)

### Common Questions

**Q: Can I use without Ollama?**
A: No, Ollama is required for AI functionality. The app needs local LLM.

**Q: Which model should I use?**
A: Start with `mistral` (4GB, fast). For code: `codellama`. For general: `llama2`.

**Q: Can I use OpenAI/Claude instead?**
A: No, this is designed for local-only operation. No external APIs.

**Q: How much disk space do I need?**
A: ~10GB for models + your documents. Mistral alone is 4GB.

**Q: Can I run on Raspberry Pi?**
A: Yes, but performance will be slow. Recommended: 8GB RAM minimum.

---

## ✨ Success!

If you've completed all steps:

🎉 **Your RAG Web Application is running!**

Access at: **http://localhost:3000**

- ✅ Ollama running locally
- ✅ Backend API on port 8000
- ✅ Frontend UI on port 3000
- ✅ Database initialized
- ✅ Models loaded and ready

**Happy chatting with your documents! 🚀**

---

## 📝 Quick Reference Commands

```bash
# Start everything
./start_rag_system.sh

# Start individual services
ollama serve                          # Terminal 1
uvicorn main:app --reload            # Terminal 2 (in backend/)
npm start                             # Terminal 3 (in frontend/)

# Check status
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8000/api/models # Backend
open http://localhost:3000            # Frontend

# Stop services
pkill ollama
pkill uvicorn
# Ctrl+C in npm start terminal
```

---

**Last Updated**: October 2025
**Version**: 1.0.0
**Maintainer**: RAG System Team
