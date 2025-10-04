# RAG Web Application

Full-stack web application providing a user-friendly interface for the core RAG (Retrieval-Augmented Generation) system.

## 🎯 Overview

This web application wraps the core RAG library (`../src/`) with a modern web interface, making document processing and AI-powered question answering accessible through a browser.

## 📁 Structure

```
webapp/
├── backend/          # FastAPI backend
├── frontend/         # React frontend  
├── docs/            # Web app documentation
├── scripts/         # Deployment scripts
└── tests/           # Integration tests
```

## 🚀 Quick Start

### Docker Deployment (Recommended)
```bash
cd webapp
docker-compose -f docker-compose.prod.yml up -d
```

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for complete instructions.

## 📖 Documentation

- [Deployment Guide (Docker)](docs/DEPLOYMENT_GUIDE.md)
- [Deployment Guide (Manual)](docs/DEPLOYMENT.md)
- [Administrator Guide](docs/ADMIN_GUIDE.md)
- [User Guide](docs/USER_GUIDE.md)
- [Architecture Decisions](docs/architecture/)

## 🔒 Security

- Local-only operation
- JWT authentication
- Pre-commit security hooks
- Rate limiting

---

**Note**: This is the optional web application. For core RAG library, see [../README.md](../README.md).
