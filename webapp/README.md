# RAG Web Application

Full-stack web application providing a complete RAG (Retrieval-Augmented Generation) system with a modern web interface.

## 🎯 Overview

This is a standalone RAG web application with secure authentication, document upload, advanced semantic search with BGE-M3 embeddings, and real-time chat powered by local LLMs. Everything runs locally on your machine with zero external dependencies.

## 📁 Structure

```
webapp/
├── README.md                    # This file - Start here!
├── INSTALLATION_GUIDE.md        # Complete local setup guide
├── backend/                     # FastAPI backend
├── frontend/                    # React frontend
├── docs/                        # Web app documentation
├── scripts/                     # Deployment & utility scripts
├── tests/                       # Integration tests
├── docker-compose.prod.yml      # Production Docker setup
└── .pre-commit-config.yaml      # Security validation hooks
```

## 🚀 Quick Start

### ⚡ **New Users: Local Installation**

**Want to run this on your own PC?** Follow our complete guide:

👉 **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Step-by-step local setup

**Quick Start (3 commands):**
```bash
git clone https://github.com/rk27599/Python_RAG.git
cd Python_RAG
./start_rag_system.sh
```

Then open **http://localhost:3000**

### 🐳 **Production: Docker Deployment**

```bash
cd webapp
docker-compose -f docker-compose.prod.yml up -d
```

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for details.

## 📖 Documentation

### Getting Started (Read These First!)
- 🆕 **[Installation Guide](INSTALLATION_GUIDE.md)** - **Local setup for your PC**
- [User Guide](docs/USER_GUIDE.md) - How to use the application

### Advanced Topics
- [Deployment Guide (Docker)](docs/DEPLOYMENT_GUIDE.md) - Container deployment
- [Deployment Guide (Manual)](docs/DEPLOYMENT.md) - Manual production setup
- [Administrator Guide](docs/ADMIN_GUIDE.md) - Maintenance & admin tasks
- [Architecture Decisions](docs/architecture/) - Technical design docs
- [Handover Document](docs/HANDOVER_DOCUMENT.md) - Project overview

## 🛠️ Technology Stack

**Backend:**
- FastAPI (Python 3.12+)
- PostgreSQL 15+ with pgvector (50x faster vector search)
- Redis 7.0+ (WebSocket session management)
- SQLAlchemy ORM
- JWT Authentication
- python-socketio 5.11.0 (WebSocket support)

**AI/ML:**
- Ollama (Local LLM - Mistral, Llama2, CodeLlama)
- BGE-M3 Embeddings (1024-dim, 100+ languages)
- PyTorch 2.6.0+ (CUDA 12.4+)
- FlagEmbedding 1.3.5 (BGE reranker)

**Frontend:**
- React 19 + TypeScript
- Material-UI (MUI)
- Axios (HTTP client)
- React Router
- WebSocket (real-time chat)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (production)
- Redis (session management)
- Pre-commit hooks (security)

## 💡 Features

### Core Features
- 📄 **Document Upload** - PDF, HTML, TXT, DOCX, Markdown with real-time progress tracking
- 💬 **Real-Time Chat** - WebSocket-based conversations with streaming responses
- 🔐 **User Management** - Secure JWT authentication and multi-user sessions
- 📊 **Document Management** - Track uploads, processing status, and history with WebSocket updates
- 🎨 **Modern UI** - Clean, responsive Material Design interface
- 📱 **Mobile Friendly** - Works on desktop, tablet, and mobile

### 🆕 Advanced RAG Features (October 2024)
- 🧠 **BGE-M3 Embeddings** - 1024-dim state-of-the-art embeddings (16x larger context than MiniLM)
- 🎯 **Reranker Service** - Cross-encoder model for 85-90% precision (vs 75% baseline)
- 🔍 **Hybrid Search** - BM25 (keyword) + Vector (semantic) ensemble retrieval
- 🧩 **Query Expansion** - Multi-query generation for comprehensive coverage
- ✅ **Corrective RAG** - Self-grading retrieval with optional web search fallback
- 📝 **System Prompt Configuration** - Customizable expert prompts with citation enforcement
- 🧠 **Memory Manager** - Adaptive batching and model unloading for OOM prevention
- 🔄 **Redis WebSocket** - Multi-worker session management (production-ready)

## 🔒 Security

- **Local-only operation** - No external APIs, all processing on your machine
- **JWT authentication** - Secure token-based auth
- **Pre-commit hooks** - Automated security validation
- **Rate limiting** - API protection
- **Input validation** - Sanitized user inputs
- **CORS protection** - Configured for localhost only
- **Data sovereignty** - All data stays on your machine

All AI processing happens locally via Ollama - **zero external dependencies**.

## 🎯 Do I Need the Web App?

**You DON'T need this if:**
- ✅ You want to use the RAG library programmatically (Python code)
- ✅ You're building your own custom interface
- ✅ You only need core RAG functionality
- ✅ You prefer command-line tools

See the main [README.md](../README.md) for core library usage.

**You DO need this if:**
- ✅ You want a ready-made user interface
- ✅ You need multi-user support with authentication
- ✅ You want a chat interface and document management UI
- ✅ You prefer a full-stack solution with database
- ✅ You want to deploy for non-technical users

## 🔧 Components

### Backend (FastAPI)
Located in `backend/` directory:
- **REST API endpoints** (`api/`) - auth, chat, documents, models
- **Authentication** (`core/security.py`) - JWT & bcrypt
- **Core Services**:
  - `document_service.py` - Document processing with real-time progress
  - `embedding_service_bge.py` - BGE-M3 embeddings (1024-dim)
  - `pdf_processor.py` - Advanced PDF processing with table/image extraction
  - `ollama_service.py` - LLM integration (Mistral, Llama2, CodeLlama)
  - `redis_service.py` - Redis client for WebSocket sessions
- **Enhanced RAG Services** (🆕 October 2024):
  - `enhanced_search_service.py` - Unified RAG pipeline orchestration
  - `reranker_service.py` - Cross-encoder reranking (BGE-reranker-v2-m3)
  - `bm25_retriever.py` - BM25 keyword search
  - `ensemble_retriever.py` - Hybrid search (BM25 + Vector fusion)
  - `query_expander.py` - Multi-query generation
  - `corrective_rag.py` - Self-grading retrieval with web fallback
  - `web_search_fallback.py` - DuckDuckGo fallback (optional)
  - `document_recovery_service.py` - Document repair/recovery
- **Utilities** (`utils/`):
  - `memory_manager.py` - RAM/swap monitoring, adaptive batching
  - `async_web_scraper.py` - HTML content extraction
- **Prompt Templates** (`prompts/`) - Citation, CoT, Extractive QA
- **Database management** (`models/`, `core/database.py`)

### Frontend (React + TypeScript)
Located in `frontend/` directory:
- Material-UI components (`src/components/`)
- Real-time chat interface (`src/components/Chat/`)
- Document management (`src/components/Documents/`)
- User authentication (`src/contexts/AuthContext.tsx`)
- Settings page (`src/components/Settings/`)
- API client (`src/services/api.ts`)

### Database
- **Development**: SQLite (auto-created)
- **Production**: PostgreSQL with pgvector extension
- Models: User, Document, Conversation, Message

## 📦 Prerequisites

Before installation, ensure you have:

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | Backend runtime |
| PyTorch | 2.6.0+ | BGE-M3 embeddings (CUDA 12.4+) |
| Node.js | 18+ | Frontend runtime |
| npm | 9+ | Package manager |
| Ollama | Latest | Local LLM service |
| Redis | 7.0+ | WebSocket sessions (REQUIRED for production) |
| PostgreSQL | 15+ | Production database (RECOMMENDED - 50x faster) |

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed setup instructions.

## 🔍 API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
cd webapp/tests
python test_phase3_integration.py
```

## 🛡️ Security Validation

Pre-commit hooks automatically validate:
- No external API calls
- Localhost-only configuration
- No hardcoded credentials
- Security best practices

Install hooks:
```bash
./scripts/install_security_hooks.sh
```

## 📊 System Requirements

**Minimum:**
- 8GB RAM
- 4 CPU cores
- 10GB disk space

**Recommended:**
- 16GB RAM
- 8 CPU cores
- 20GB disk space (for models + data)

## 🆘 Need Help?

- **Installation Issues**: See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Troubleshooting section
- **Usage Questions**: See [User Guide](docs/USER_GUIDE.md)
- **Admin Tasks**: See [Admin Guide](docs/ADMIN_GUIDE.md)
- **Bugs/Issues**: [GitHub Issues](https://github.com/rk27599/Python_RAG/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rk27599/Python_RAG/discussions)

## 🌟 Quick Links

- **Start Here**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
- **Core RAG Library**: [../README.md](../README.md)
- **Docker Deployment**: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- **API Reference**: http://localhost:8000/docs (when running)

---

**Version**: 1.0.0
**Last Updated**: October 2024
**License**: See [../LICENSE](../LICENSE)
