# Webapp Documentation

This directory contains documentation specific to the **Secure RAG System Web Application**.

## 📚 Available Documentation

### Network & Deployment

- **[NETWORK_SETUP.md](NETWORK_SETUP.md)** - Network access configuration guide
  - LAN access setup for other devices on your network
  - Firewall configuration
  - Security considerations
  - Troubleshooting network issues

- **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** - Production deployment guide
  - Configuration changes for production mode
  - Security hardening checklist
  - SSL/TLS setup
  - Performance optimization
  - Deployment steps and verification

## 🎯 Quick Links

### Getting Started
- [Main README](../README.md) - Project overview and quick start
- [Installation Guide](../webapp/INSTALLATION_GUIDE.md) - Detailed setup instructions
- [User Guide](../webapp/docs/USER_GUIDE.md) - User manual
- [Admin Guide](../webapp/docs/ADMIN_GUIDE.md) - Admin operations

### Architecture & Development
- [Webapp Documentation](../webapp/docs/) - Complete webapp docs
- [Architecture Decisions](../webapp/docs/architecture/) - System design
- [Handover Document](../webapp/docs/HANDOVER_DOCUMENT.md) - Project overview

### Old RAG System
- [Old RAG System Docs](../archive/old_rag_system/docs/) - Documentation for the legacy standalone RAG library (archived for reference)

## 📋 Documentation Structure

```
/home/rkpatel/RAG/
├── README.md                        # Main project documentation
├── docs/                            # Webapp documentation (this folder)
│   ├── README.md                   # This file
│   ├── NETWORK_SETUP.md            # Network access guide
│   └── PRODUCTION_DEPLOYMENT.md     # Production deployment guide
│
├── webapp/                          # Main web application
│   ├── docs/                       # Additional webapp docs
│   │   ├── USER_GUIDE.md
│   │   ├── ADMIN_GUIDE.md
│   │   ├── DEPLOYMENT_GUIDE.md
│   │   └── architecture/
│   └── INSTALLATION_GUIDE.md
│
└── archive/old_rag_system/          # Legacy RAG system (reference)
    └── docs/                       # Old RAG system documentation
        ├── README.md
        ├── architecture.md
        └── api/, guides/
```

## 🔧 Common Tasks

### Enable LAN Access
See [NETWORK_SETUP.md](NETWORK_SETUP.md) for complete instructions on allowing other devices to access your RAG system.

### Deploy to Production
See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for step-by-step production deployment guide.

### Configure SSL/TLS
See [PRODUCTION_DEPLOYMENT.md#ssl-tls-setup](PRODUCTION_DEPLOYMENT.md#ssl-tls-setup) for HTTPS configuration.

## 📞 Support

- 📖 **Full Documentation**: See [webapp/docs/](../webapp/docs/)
- 🐛 **Issues**: Report on GitHub
- 💬 **Questions**: GitHub Discussions
- 📧 **Contact**: Reach out to maintainers

---

**Note**: This documentation is for the production web application. For documentation about the legacy standalone RAG library, see [archive/old_rag_system/docs/](../archive/old_rag_system/docs/).
