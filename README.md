# Secure RAG System - Web Application

A production-ready **Retrieval-Augmented Generation (RAG) web application** with complete data sovereignty. Features secure authentication, document upload, semantic search, real-time chat with local LLMs, and PostgreSQL vector storage.

## 🚀 Key Features

### Core Features
- **🔐 Secure Authentication**: JWT-based auth with bcrypt password hashing
- **📄 Advanced Document Processing**: Upload HTML, PDF, TXT files with async processing + real-time progress tracking
- **🧠 BGE-M3 Embeddings**: State-of-the-art 1024-dim embeddings (16x larger context window than MiniLM)
- **💬 Real-Time Chat**: WebSocket-based chat with streaming responses and Redis session management
- **🤖 Local LLM Integration**: Dual provider support (Ollama + vLLM) for Mistral, Llama2, CodeLlama with configurable system prompts
- **📊 Rich Metadata**: Track sources, sections, and similarity scores
- **🎨 Modern UI**: React + TypeScript + Material-UI frontend
- **⚡ High Performance**: Async document processing, connection pooling, memory optimization
- **🛡️ Security-First**: Local-only deployment, no external dependencies
- **📈 Production-Ready**: Multi-worker support, SSL/TLS, rate limiting, Redis WebSocket management

### 🆕 Enhanced RAG Features (October 2024)
- **🎯 Reranker Service**: Cross-encoder model for re-ranking search results (higher precision)
- **🔍 Hybrid Search**: BM25 (keyword) + Vector (semantic) search with ensemble retrieval
- **🧩 Query Expansion**: Multi-query generation for comprehensive retrieval coverage
- **✅ Corrective RAG**: Self-grading retrieval with web search fallback for missing knowledge
- **📝 System Prompt Configuration**: Customizable expert prompts with citation enforcement
- **🧠 Memory Manager**: Adaptive batching and model unloading for OOM prevention
- **📊 Document Progress Tracking**: Real-time WebSocket updates + API polling during processing

## 📋 Requirements

- **Python 3.12+** (migrated from 3.10 - October 2024, ~10-15% faster)
- **PyTorch 2.6.0+** with CUDA 12.4+ (required for BGE-M3 embeddings)
- **Node.js 18+** (for frontend)
- **PostgreSQL 14+** with pgvector extension
- **Redis 7.0+** (for WebSocket session management)
- **Ollama** (for LLM integration)
- **GPU Recommended**: 8GB+ VRAM for optimal embedding/reranker performance

## 🔧 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/rk27599/Python_RAG.git
cd Python_RAG
```

### 2. Setup Backend
```bash
cd webapp/backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python init_db.py
```

### 3. Setup Frontend
```bash
cd webapp/frontend
npm install
npm start  # Development server on http://localhost:3000
```

### 4. Start LLM Provider

**Option A: Ollama (Default - Recommended for Development)**
```bash
# Install from https://ollama.ai
ollama serve
ollama pull mistral
```

**Option B: vLLM (✅ Production Ready - Multi-User)**
```bash
# Quick start with provided script
bash webapp/scripts/start_vllm.sh

# The script will guide you through setup with:
# - Qwen3-4B-Thinking-2507-FP8 (optimized for 8GB GPU)
# - 16K context window
# - Docker-based deployment (WSL2 compatible)
# - Built-in health checks

# See webapp/docs/VLLM_GUIDE.md for detailed setup
```

### 5. Run Application
```bash
# Backend (from webapp/backend/)
python main.py

# Frontend (from webapp/frontend/)
npm start
```

Access the application at **http://localhost:3000**

## 📁 Project Structure

```
/home/rkpatel/RAG/
├── README.md                        # This file - Project overview
├── CLAUDE.md                        # Project instructions for AI assistants
├── LICENSE                          # Open source license
├── .gitignore                       # Git ignore rules
│
├── logs/                            # Application logs (gitignored)
├── data/                            # Data files (gitignored)
├── archive/                         # Old RAG system (reference)
├── venv/                            # Python virtual environment
│
└── webapp/                          # 🎯 Main Web Application (ALL code & docs here)
    ├── requirements.txt             # Dev/testing dependencies
    ├── tests/                       # All test files
    │   ├── test_enhanced_rag_e2e.py     # End-to-end RAG tests
    │   ├── test_pdf_sample.py           # PDF processing tests
    │   ├── test_phase3_integration.py   # Phase 3 integration tests
    │   └── validate_phases_1_2.py       # Phase 1 & 2 validation
    │
    ├── README.md                    # Webapp overview
    ├── INSTALLATION_GUIDE.md        # Detailed setup instructions
    │
    ├── backend/                     # FastAPI Backend (Python)
    │   ├── api/                   # REST API endpoints
    │   │   ├── auth.py           # Authentication
    │   │   ├── chat.py           # WebSocket chat + messages + Redis
    │   │   ├── documents.py      # Document upload/management
    │   │   └── models.py         # Ollama model info
    │   │
    │   ├── core/                  # Core configuration
    │   │   ├── config.py         # Settings management + Redis config
    │   │   ├── database.py       # SQLAlchemy setup
    │   │   └── security.py       # JWT & password hashing
    │   │
    │   ├── models/                # Database models
    │   │   ├── user.py           # User model
    │   │   ├── document.py       # Document & Chunk models (progress tracking)
    │   │   └── conversation.py   # Chat models
    │   │
    │   ├── services/              # Business logic
    │   │   ├── document_service.py         # Document processing with progress
    │   │   ├── embedding_service_bge.py    # BGE-M3 embeddings (1024-dim)
    │   │   ├── pdf_processor.py            # Advanced PDF processing
    │   │   ├── enhanced_search_service.py  # 🆕 Unified enhanced RAG
    │   │   ├── reranker_service.py         # 🆕 Cross-encoder reranking
    │   │   ├── bm25_retriever.py           # 🆕 BM25 keyword search
    │   │   ├── ensemble_retriever.py       # 🆕 Hybrid search orchestration
    │   │   ├── query_expander.py           # 🆕 Multi-query generation
    │   │   ├── corrective_rag.py           # 🆕 Self-grading RAG
    │   │   ├── web_search_fallback.py      # 🆕 External knowledge fallback
    │   │   ├── document_recovery_service.py # 🆕 Document repair/recovery
    │   │   ├── rag_service.py              # RAG retrieval orchestration
    │   │   └── ollama_service.py           # LLM integration
    │   │
    │   ├── utils/                 # Utility modules
    │   │   ├── async_web_scraper.py   # HTML content extraction
    │   │   └── memory_manager.py      # 🆕 RAM/swap monitoring, adaptive batching
    │   │
    │   ├── prompts/               # 🆕 LLM Prompt Templates
    │   │   ├── citation_template.py    # Citation-enforcing prompts
    │   │   ├── cot_template.py         # Chain-of-thought prompts
    │   │   └── extractive_template.py  # Extractive QA prompts
    │   │
    │   ├── scripts/               # Backend scripts
    │   │   ├── reembed_with_bge_m3.py   # BGE-M3 migration script
    │   │   ├── setup_postgres.sh        # Database setup
    │   │   ├── redis_health.py          # Redis monitoring
    │   │   └── migrate_*.py             # Database migrations
    │   │
    │   ├── docs/                  # Backend documentation
    │   │   ├── ENHANCED_SEARCH_INTEGRATION.md  # RAG features guide
    │   │   ├── README_ENHANCED_SEARCH.md       # Enhanced search overview
    │   │   ├── TESTING_GUIDE.md                # Testing documentation
    │   │   ├── VECTOR_SEARCH_OPTIMIZATION.md   # Performance tuning
    │   │   └── redis/                          # Redis-specific docs
    │   │       ├── REDIS_DEPLOYMENT_STEPS.md
    │   │       ├── REDIS_FIX_SUMMARY.md
    │   │       └── FIX_REDIS_PUBSUB.md
    │   │
    │   ├── tests/                 # Backend tests
    │   │   └── test_enhanced_search_integration.py
    │   │
    │   ├── main.py                # FastAPI application entry
    │   ├── init_db.py             # Database initialization
    │   └── requirements.txt       # Backend dependencies
    │
    ├── frontend/                   # React Frontend (TypeScript)
    │   ├── src/
    │   │   ├── components/        # React components
    │   │   │   ├── Auth/         # Login, Register
    │   │   │   ├── Chat/         # Chat interface, conversations
    │   │   │   ├── Documents/    # Upload, document list (🆕 progress tracking)
    │   │   │   ├── Layout/       # App layout, sidebar
    │   │   │   └── Settings/     # Model settings (🆕 system prompt config)
    │   │   │
    │   │   ├── contexts/          # React contexts
    │   │   │   ├── AuthContext.tsx    # Auth state
    │   │   │   └── ChatContext.tsx    # Chat state + WebSocket
    │   │   │
    │   │   ├── services/          # API services
    │   │   │   └── api.ts        # Axios API client
    │   │   │
    │   │   ├── config/            # Configuration
    │   │   │   └── config.ts     # App settings
    │   │   │
    │   │   ├── App.tsx            # Main app component
    │   │   └── index.tsx          # React entry point
    │   │
    │   ├── public/                # Static assets
    │   ├── package.json           # Node dependencies
    │   └── README.md              # Frontend documentation
    │
    ├── docs/                       # 📚 Complete Documentation
    │   ├── README.md              # Docs index
    │   ├── README_ROOT.md         # Root docs overview
    │   ├── BGE_M3_MIGRATION_GUIDE.md   # 🆕 BGE-M3 migration guide
    │   ├── FEATURES_GUIDE.md      # 🆕 Complete features guide (consolidated)
    │   ├── NETWORK_SETUP.md       # Network/LAN configuration
    │   ├── PRODUCTION_DEPLOYMENT.md  # Production deployment
    │   ├── REDIS_COMPLETE_GUIDE.md   # Redis setup & troubleshooting
    │   ├── ADMIN_GUIDE.md         # Admin operations
    │   ├── USER_GUIDE.md          # User manual
    │   ├── DEPLOYMENT_GUIDE.md    # Docker deployment
    │   ├── HANDOVER_DOCUMENT.md   # Project handover
    │   └── architecture/          # Architecture decisions
    │
    └── scripts/                    # Webapp utility scripts
        ├── deploy.sh              # Deployment automation
        ├── backup.sh              # Database backup
        ├── setup_ollama.sh        # Ollama setup
        └── security_validator.py  # Security checks
```

**Note**: 🆕 indicates new features/files added in October 2024 reorganization.

## 🎯 Main Components

### Backend (FastAPI + Python)
- **Authentication**: JWT tokens, bcrypt password hashing, session management
- **Document Processing**: Async upload, chunking, embedding generation
- **Vector Search**: PostgreSQL pgvector with HNSW indexing (50x faster)
- **RAG System**: TF-IDF retrieval, semantic search, context building
- **Chat API**: WebSocket real-time messaging, conversation management
- **LLM Integration**: Dual provider support (Ollama/vLLM) for Mistral, Llama2, CodeLlama with factory pattern

### Frontend (React + TypeScript)
- **Auth UI**: Login, registration, password validation
- **Document Manager**: Drag-and-drop upload, processing status, document list
- **Chat Interface**: Real-time messaging, conversation history, markdown rendering
- **Settings**: Model selection, RAG parameters, temperature control
- **Security**: Localhost-only validation, JWT authentication

### Database (PostgreSQL + pgvector)
- **Users**: Authentication, roles, sessions
- **Documents**: File metadata, processing status, chunks
- **Vectors**: Embeddings with pgvector extension, HNSW indexing
- **Conversations**: Chat history, messages, ratings

## 📊 Performance

- **Vector Search**: 50x faster with PostgreSQL pgvector vs Python
- **Document Processing**: Async processing with progress tracking
- **Real-Time Chat**: WebSocket streaming responses
- **Concurrent Users**: Multi-worker support (4 workers in production)
- **Connection Pooling**: Optimized database connections

## 🛡️ Security Features

- **Local-Only**: No external API dependencies
- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: bcrypt with secure rounds
- **Rate Limiting**: Prevent abuse
- **CORS Protection**: Localhost-only by default
- **Security Headers**: XSS, CSRF, clickjacking protection
- **Input Validation**: Pydantic models, type checking

## 📖 Documentation

### Getting Started
- [Installation Guide](webapp/INSTALLATION_GUIDE.md) - Detailed setup
- [User Guide](webapp/docs/USER_GUIDE.md) - User manual
- [Admin Guide](webapp/docs/ADMIN_GUIDE.md) - Admin operations

### Features & Configuration
- [Features Guide](webapp/docs/FEATURES_GUIDE.md) - 🆕 Complete RAG features overview
- [BGE-M3 Migration Guide](webapp/docs/BGE_M3_MIGRATION_GUIDE.md) - 🆕 Embedding migration
- [Enhanced Search Integration](webapp/backend/docs/ENHANCED_SEARCH_INTEGRATION.md) - 🆕 Technical details
- [vLLM Complete Guide](webapp/docs/VLLM_GUIDE.md) - ✅ Production-ready multi-user LLM setup

### Deployment
- [Network Setup](webapp/docs/NETWORK_SETUP.md) - LAN access configuration
- [Production Deployment](webapp/docs/PRODUCTION_DEPLOYMENT.md) - Production guide
- [Redis Setup](webapp/docs/REDIS_COMPLETE_GUIDE.md) - 🆕 Redis configuration
- [Docker Deployment](webapp/docs/DEPLOYMENT_GUIDE.md) - Docker setup

### Development
- [Architecture](webapp/docs/architecture/) - System design
- [Testing Guide](webapp/backend/docs/TESTING_GUIDE.md) - Testing documentation
- [Handover Document](webapp/docs/HANDOVER_DOCUMENT.md) - Project overview

## 🧪 Testing

### Backend Tests
```bash
cd webapp/backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd webapp/frontend
npm test
```

### Integration Tests
```bash
cd webapp
./tests/test_backend.sh
```

## 🚀 Deployment

### Development
```bash
# Backend
cd webapp/backend && python main.py

# Frontend
cd webapp/frontend && npm start
```

### Production
```bash
# Update configuration
cd webapp/backend
cp .env.example .env
# Edit .env: DEBUG=False, SECRET_KEY=<new-key>

# Build frontend
cd ../frontend
npm run build
cp -r build/* ../backend/static/

# Run backend (auto-serves frontend)
cd ../backend
python main.py  # 4 workers, docs disabled, production mode
```

See [PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) for complete guide.

## 🔧 Configuration

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://rag_user:password@localhost:5432/rag_database
DEBUG=False  # Set to True for development

# Security
SECRET_KEY=<generate-secure-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Provider (choose one)
LLM_PROVIDER=ollama  # Options: "ollama" (default), "vllm"

# Ollama (default)
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral

# vLLM (optional - for multi-user production)
VLLM_BASE_URL=http://localhost:8001
VLLM_GPU_COUNT=1
VLLM_TENSOR_PARALLEL_SIZE=1

# Server
HOST=127.0.0.1
PORT=8000
```

### Frontend (.env)
```bash
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_WS_URL=http://127.0.0.1:8000
PORT=3000
```

## 🗄️ Database Setup

### PostgreSQL with pgvector
```bash
# Install PostgreSQL and pgvector
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgresql-14-pgvector

# Create database and user
sudo -u postgres psql
CREATE DATABASE rag_database;
CREATE USER rag_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE rag_database TO rag_user;

# Enable pgvector extension
\c rag_database
CREATE EXTENSION IF NOT EXISTS vector;
```

See [webapp setup scripts](webapp/backend/scripts/) for automated setup.

## 🤖 LLM Provider Setup

The RAG system supports two LLM providers with easy switching via configuration:

### Ollama (Default)

**Best for:** Development, single-user, simple setup

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull models
ollama pull mistral
ollama pull llama2
ollama pull codellama
```

### vLLM (Production, Multi-User)

**Best for:** Production deployment, 5+ concurrent users, multi-GPU servers

```bash
# Docker (recommended)
docker pull vllm/vllm-openai:latest
docker run --gpus all -p 8001:8000 --ipc=host \
    vllm/vllm-openai:latest \
    --model mistralai/Mistral-7B-Instruct-v0.2

# Or native installation
pip install vllm==0.11.0
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --port 8001
```

**Switching Providers (No Code Changes):**

```bash
# Use vLLM in .env
LLM_PROVIDER=vllm
VLLM_BASE_URL=http://localhost:8001

# Restart backend - that's it!
```

**📚 Complete Guide:** See [webapp/docs/VLLM_GUIDE.md](webapp/docs/VLLM_GUIDE.md) for comprehensive documentation on:
- Architecture and factory pattern
- Installation methods (Docker, native, conda)
- Configuration and usage
- Performance tuning and multi-GPU setup
- Troubleshooting and migration guide

**Features:**
- ✅ Simple one-command setup
- ✅ Automatic model management
- ✅ Good for development and low-concurrency
- ✅ Works on systems with limited GPU resources

---

### vLLM (Advanced - Optional)

**Best for:** Production, multi-user (5+), multi-GPU servers

**Why vLLM?**
- 🚀 **8-100x faster** for concurrent requests
- 🔥 **Parallel batching** (vs Ollama's serial processing)
- 💪 **Multi-GPU tensor parallelism**
- ⚡ **Production-scale throughput**

**Quick Start (Docker):**
```bash
# Pull official vLLM image
docker pull vllm/vllm-openai:latest

# Run vLLM server (single GPU)
docker run --gpus all -p 8001:8000 --ipc=host \
    vllm/vllm-openai:latest \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --host 0.0.0.0 --port 8000

# Switch to vLLM in .env
LLM_PROVIDER=vllm
VLLM_BASE_URL=http://localhost:8001
```

**Quick Start:**
```bash
# Use the provided script (recommended)
bash webapp/scripts/start_vllm.sh

# Or see complete documentation
# webapp/docs/VLLM_GUIDE.md
```

**Comparison:**

| Feature | Ollama | vLLM |
|---------|--------|------|
| Setup | Simple (one command) | Easy (provided script) ✅ |
| Single User | Fast ✅ | Fast ✅ |
| 10 Concurrent Users | Slow (serialized) | **8-10x faster** 🚀 |
| Multi-GPU | Limited | Excellent ✅ |
| Model Management | Automatic | Manual (Hugging Face) |
| Production Ready | Development | ✅ Production |

**Switching Providers:**
```bash
# No code changes required! Just update .env

# Use Ollama (default)
LLM_PROVIDER=ollama

# Use vLLM (production)
LLM_PROVIDER=vllm
```

For detailed vLLM setup, performance tuning, and multi-GPU configuration, see [VLLM_GUIDE.md](webapp/docs/VLLM_GUIDE.md).

## 📝 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user

### Documents
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List documents
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/documents/{id}/chunks` - Get document chunks

### Chat
- `WebSocket /socket.io` - Real-time chat
- `GET /api/conversations` - List conversations
- `POST /api/conversations` - Create conversation
- `GET /api/conversations/{id}/messages` - Get messages

### Models
- `GET /api/models` - List available Ollama models
- `GET /api/models/default` - Get default model

## 🎨 Frontend Features

- **Authentication**: Secure login/register with validation
- **Document Upload**: Drag-and-drop with progress tracking
- **Chat Interface**: Real-time messaging with markdown rendering
- **Conversation Management**: Create, switch, delete conversations
- **Model Selection**: Choose Ollama models
- **RAG Settings**: Configure temperature, top_k, RAG mode
- **Responsive Design**: Works on desktop and mobile

## 🌐 Network Access

For LAN access (other devices on your network):

1. Update `webapp/backend/.env`: `HOST=0.0.0.0`
2. Update `webapp/frontend/.env`: `REACT_APP_API_URL=http://<your-ip>:8000`
3. Configure firewall to allow ports 3000, 8000

See [NETWORK_SETUP.md](docs/NETWORK_SETUP.md) for complete guide.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI**: Modern Python web framework
- **React**: UI library
- **PostgreSQL**: Powerful database with vector support
- **Ollama**: Local LLM platform
- **Material-UI**: React component library
- **Socket.IO**: Real-time communication

## 📞 Support

- 📖 **Documentation**: See [webapp/docs/](webapp/docs/)
- 🐛 **Issues**: Report on GitHub
- 💬 **Questions**: GitHub Discussions
- 📧 **Contact**: Reach out to maintainers

---

**Note**: The `archive/old_rag_system/` folder contains the previous standalone RAG library for reference. The current production application is in `webapp/`.
