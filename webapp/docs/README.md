# Web Application Documentation

Complete documentation for the RAG Web Application.

## 📖 Quick Navigation

### 🚀 Deployment
- **[Deployment Guide (Docker)](DEPLOYMENT_GUIDE.md)** - Production deployment with Docker Compose
- **[Deployment Guide (Manual)](DEPLOYMENT.md)** - Manual setup and configuration

### 👨‍💼 Administration
- **[Administrator Guide](ADMIN_GUIDE.md)** - System administration, monitoring, and maintenance
- **[Project Handover](HANDOVER_DOCUMENT.md)** - Complete project handover documentation

### 👥 End Users
- **[User Guide](USER_GUIDE.md)** - How to use the web application

### 🏗️ Architecture
- **[Architecture Overview](architecture/)** - Technical decisions and system design
  - [Decision Tree](architecture/decision-tree.md)
  - [Technology Decisions](architecture/technology-decisions.md)
  - [Security Validation](architecture/security-validation.md)
  - [Comparison Matrices](architecture/comparison-matrices/)

## 🎯 Documentation by Audience

| Audience | Start Here |
|----------|-----------|
| **DevOps/Deployment** | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| **System Administrators** | [ADMIN_GUIDE.md](ADMIN_GUIDE.md) |
| **End Users** | [USER_GUIDE.md](USER_GUIDE.md) |
| **Developers** | [architecture/](architecture/) |
| **Project Managers** | [HANDOVER_DOCUMENT.md](HANDOVER_DOCUMENT.md) |

## 🏗️ Web Application Stack

- **Backend**: FastAPI (Python 3.12+)
- **Frontend**: React 18 + TypeScript
- **Database**: PostgreSQL + pgvector
- **Cache**: Redis
- **AI**: Ollama (Local LLMs)
- **Deployment**: Docker + Docker Compose

## 📦 Core RAG Library

The web application uses the core RAG library from `../../src/`. For core library documentation:
- See [../../docs/README.md](../../docs/README.md)

## 🔗 Related Documentation

- **[Main README](../../README.md)** - Project overview
- **[Core RAG Docs](../../docs/)** - Core library documentation
- **[Examples](../../examples/)** - Usage examples

---

*Last updated: October 2025*
