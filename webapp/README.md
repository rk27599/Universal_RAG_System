# RAG Web Application

Full-stack web application providing a user-friendly interface for the core RAG (Retrieval-Augmented Generation) system.

## 🎯 Overview

This web application wraps the core RAG library (`../src/`) with a modern web interface, making document processing and AI-powered question answering accessible through a browser.

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
- PostgreSQL / SQLite
- Ollama (Local LLM)
- SQLAlchemy ORM
- JWT Authentication

**Frontend:**
- React 19 + TypeScript
- Material-UI (MUI)
- Axios (HTTP client)
- WebSocket support
- React Router

**Infrastructure:**
- Docker & Docker Compose
- Nginx (production)
- Pre-commit hooks (security)

## 💡 Features

- 📄 **Document Upload** - PDF, HTML, TXT, DOCX, Markdown support
- 💬 **AI Chat** - Context-aware conversations about your documents
- 🔍 **Semantic Search** - Advanced RAG with TF-IDF and embeddings
- ⚙️ **Model Settings** - Configure temperature, tokens, and AI parameters
- 🔐 **User Management** - Secure authentication and multi-user sessions
- 📊 **Document Management** - Track uploads, processing status, and history
- 🎨 **Modern UI** - Clean, responsive Material Design interface
- 📱 **Mobile Friendly** - Works on desktop, tablet, and mobile

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
- REST API endpoints (`api/`)
- Authentication & authorization (`core/security.py`)
- Document processing service (`services/document_service.py`)
- Ollama integration (`services/ollama_service.py`)
- Database management (`models/`, `core/database.py`)
- RAG system integration (`services/rag_service.py`)

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
| Node.js | 18+ | Frontend runtime |
| npm | 9+ | Package manager |
| Ollama | Latest | Local LLM service |
| PostgreSQL | 13+ (optional) | Production database |

See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed setup instructions.

## 🤝 Integration with Core Library

The web application uses the core RAG library from `../src/`:
- `RAGSystem` - For retrieval and generation
- `WebScraper` - For document ingestion
- `AsyncWebScraper` - For high-performance processing

All web app functionality is built on top of the core library, ensuring consistency and code reuse.

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
**Last Updated**: January 2025
**License**: See [../LICENSE](../LICENSE)

**Note**: This is the optional web application. For the core RAG library (Python-only), see [../README.md](../README.md).
