# Web Application Documentation

Complete documentation for the RAG Web Application.

## 📖 Quick Navigation

### 🚀 Deployment
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment with Docker Compose
- **[Production Deployment](PRODUCTION_DEPLOYMENT.md)** - Production best practices
- **[Network Setup](NETWORK_SETUP.md)** - LAN/network configuration

### 🤖 AI/ML Components
- **[BGE-M3 Guide](BGE_M3_GUIDE.md)** - Comprehensive BGE-M3 embedding model documentation
- **[BGE-M3 Migration](BGE_M3_MIGRATION_GUIDE.md)** - Migration from MiniLM to BGE-M3
- **[Features Guide](FEATURES_GUIDE.md)** - RAG system features and configuration
- **[vLLM Complete Guide](VLLM_COMPLETE_GUIDE.md)** - High-performance LLM serving
- **[vLLM Installation](VLLM_INSTALLATION.md)** - vLLM setup and installation
- **[vLLM Troubleshooting](VLLM_TROUBLESHOOTING.md)** - Common vLLM issues and solutions

### 🔧 Infrastructure
- **[Redis Complete Guide](REDIS_COMPLETE_GUIDE.md)** - Redis setup, configuration, and troubleshooting

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
| **AI/ML Developers** | [BGE_M3_GUIDE.md](BGE_M3_GUIDE.md), [FEATURES_GUIDE.md](FEATURES_GUIDE.md) |
| **Backend Developers** | [architecture/](architecture/), [REDIS_COMPLETE_GUIDE.md](REDIS_COMPLETE_GUIDE.md) |
| **Project Managers** | [HANDOVER_DOCUMENT.md](HANDOVER_DOCUMENT.md) |

## 🏗️ Web Application Stack

- **Backend**: FastAPI (Python 3.12+)
- **Frontend**: React 19 + TypeScript
- **Database**: PostgreSQL + pgvector (HNSW indexing)
- **Embeddings**: BGE-M3 (1024-dim, 100+ languages)
- **LLM Providers**: Ollama (default) or vLLM (high-performance)
- **Cache/Sessions**: Redis
- **Deployment**: Docker + Docker Compose

## 📦 Core RAG Library

The web application uses the core RAG library from `../../src/`. For core library documentation:
- See [../../docs/README.md](../../docs/README.md)

## 🔗 Related Documentation

- **[Main README](../../README.md)** - Project overview
- **[Core RAG Docs](../../docs/)** - Core library documentation
- **[Examples](../../examples/)** - Usage examples

---

*Last updated: October 2024*
