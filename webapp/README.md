# RAG Web Application

> **Optional web interface for the core RAG library**

This directory contains the optional web application that provides a user-friendly interface for the RAG system. The web app consists of:

- **Backend** (`../app/`): FastAPI server with REST API
- **Frontend** (`../frontend/`): React-based user interface
- **Deployment configs**: Docker Compose and pre-commit hooks

## 📋 What's In This Directory

```
webapp/
├── README.md                    # This file
├── DEPLOYMENT.md                # Manual deployment guide
├── docker-compose.prod.yml      # Production Docker setup
└── .pre-commit-config.yaml      # Git hooks for security validation
```

## 🚀 Quick Start

### Option 1: Manual Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed manual setup instructions.

### Option 2: Docker Deployment
See [../docs/DEPLOYMENT_GUIDE.md](../docs/DEPLOYMENT_GUIDE.md) for Docker-based deployment.

## 📖 Related Documentation

- **Main README**: [../README.md](../README.md) - Core RAG library documentation
- **Admin Guide**: [../docs/ADMIN_GUIDE.md](../docs/ADMIN_GUIDE.md) - Administrative tasks
- **User Guide**: [../docs/USER_GUIDE.md](../docs/USER_GUIDE.md) - End-user documentation
- **Architecture**: [../docs/architecture.md](../docs/architecture.md) - System design

## 🔧 Components

### Backend (FastAPI)
Located in `../app/` directory:
- REST API endpoints
- Authentication & authorization
- Document processing service
- Ollama integration
- Database management

### Frontend (React)
Located in `../frontend/` directory:
- Material-UI components
- Real-time chat interface
- Document management
- User authentication

## 🔒 Security

The web application includes:
- Localhost-only operation by default
- JWT authentication
- CORS protection
- Input validation
- Security headers
- Pre-commit security validation hooks

## ⚙️ Configuration Files

- **`DEPLOYMENT.md`**: Step-by-step manual deployment guide
- **`docker-compose.prod.yml`**: Production Docker Compose configuration
- **`.pre-commit-config.yaml`**: Git hooks for code quality and security

## 🎯 Do I Need This?

**You DON'T need the web app if:**
- You want to use the RAG library programmatically
- You're building your own interface
- You only need the core RAG functionality

**You DO need the web app if:**
- You want a ready-made UI
- You need multi-user support with authentication
- You want chat interface and document management
- You prefer a full-stack solution

## 📦 Installation

1. **Backend setup**: See `../app/` directory
2. **Frontend setup**: See `../frontend/` directory
3. **Deployment**: Follow [DEPLOYMENT.md](DEPLOYMENT.md)

## 🤝 Integration

The web application uses the core RAG library from `../src/`:
- `RAGSystem` for retrieval and generation
- `WebScraper` for document ingestion
- `AsyncWebScraper` for high-performance processing

All web app functionality is built on top of the core library.
