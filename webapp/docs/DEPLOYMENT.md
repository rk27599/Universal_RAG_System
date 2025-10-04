# 🚀 Secure RAG System - Complete Deployment Guide

> **📌 IMPORTANT**: This guide is for deploying the **optional web application** found in the `app/` and `frontend/` directories.
>
> If you only need the core RAG library for programmatic use, see the main [README.md](README.md) instead. The web application provides a UI for the RAG system but is not required for basic usage.

This deployment guide covers the complete setup of your secure, localhost-only RAG (Retrieval-Augmented Generation) system with React frontend and FastAPI backend.

## 📋 Prerequisites

### System Requirements
- **Python 3.12+** (for backend - migrated from 3.10)
- **Node.js 16+** (for frontend)
- **PostgreSQL 14+** (for vector database)
- **Ollama** (for local AI models)
- **Git** (for version control)

### Security Notice
🔒 **This system operates exclusively on localhost and never sends data to external services, ensuring complete privacy and data sovereignty.**

## 🎯 Quick Start (5 Minutes)

### 1. Backend Setup
```bash
# Navigate to project root
cd /home/rkpatel/RAG

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Start backend server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### 3. Access Your System
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Detailed Setup Instructions

### Backend Configuration

#### Database Setup (PostgreSQL + pgvector)
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE rag_system;
CREATE USER rag_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE rag_system TO rag_user;

# Install pgvector extension
sudo apt install postgresql-14-pgvector
# Connect to your database and run:
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Environment Configuration
Create `.env` file in project root:
```env
# Database Configuration
DATABASE_URL=postgresql://rag_user:your_secure_password@localhost:5432/rag_system

# Security Settings
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Settings (localhost only)
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# File Upload Settings
MAX_FILE_SIZE=100MB
UPLOAD_DIRECTORY=./uploads

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral
```

#### Ollama Setup
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull recommended models
ollama pull mistral
ollama pull llama2
ollama pull codellama
```

### Frontend Configuration

#### Environment Variables
Create `frontend/.env`:
```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
GENERATE_SOURCEMAP=false
```

#### Build Configuration
The frontend is configured with:
- **Material-UI** for component library
- **TypeScript** for type safety
- **WebSocket** for real-time chat
- **Axios** for API communication
- **Security validation** for localhost-only operation

## 🏭 Production Deployment

### Backend Production Setup
```bash
# Create production environment
python -m venv prod_venv
source prod_venv/bin/activate

# Install production dependencies
pip install -r requirements.txt
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app --bind 127.0.0.1:8000 --workers 4
```

### Frontend Production Build
```bash
cd frontend

# Create production build
npm run build

# Serve with a static server
npm install -g serve
serve -s build -l 3000
```

### Database Production Configuration
```sql
-- Create production database
CREATE DATABASE rag_system_prod;
CREATE USER rag_prod_user WITH PASSWORD 'strong_production_password';
GRANT ALL PRIVILEGES ON DATABASE rag_system_prod TO rag_prod_user;

-- Install required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

## 🛡️ Security Configuration

### System Security Validation
The system includes comprehensive security validation:

```python
# Backend security features:
- JWT token authentication
- CORS protection (localhost only)
- File upload validation
- SQL injection prevention
- XSS protection
- Rate limiting
- Input sanitization
```

### Frontend Security Features
```typescript
// Frontend security features:
- HTTPS-only cookies
- CSP headers
- XSS protection
- Input validation
- Localhost-only API calls
- No external dependencies
```

## 📊 System Monitoring

### Health Checks
```bash
# Backend health check
curl http://localhost:8000/health

# Database connection test
curl http://localhost:8000/system/status

# Ollama status
curl http://localhost:11434/api/tags
```

### Performance Monitoring
```bash
# Check system resources
htop

# Monitor database connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Check Ollama model status
ollama list
```

## 🔄 Maintenance & Updates

### Regular Maintenance Tasks
```bash
# Update Python dependencies
pip list --outdated
pip install --upgrade package_name

# Update Node.js dependencies
cd frontend
npm audit
npm update

# Database maintenance
sudo -u postgres psql rag_system -c "VACUUM ANALYZE;"
```

### Backup Strategy
```bash
# Database backup
pg_dump -U rag_user -h localhost rag_system > backup_$(date +%Y%m%d).sql

# Code backup
git add . && git commit -m "Backup $(date +%Y-%m-%d)"
```

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.10+

# Check port availability
lsof -i :8000

# Check database connection
psql -U rag_user -h localhost rag_system
```

#### Frontend Build Fails
```bash
# Clear Node.js cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 16+
```

#### Ollama Connection Issues
```bash
# Check Ollama service
systemctl status ollama

# Test Ollama API
curl http://localhost:11434/api/tags

# Restart Ollama
sudo systemctl restart ollama
```

### Debug Mode
```bash
# Backend debug mode
export DEBUG=1
python -m uvicorn app.main:app --reload --log-level debug

# Frontend debug mode
REACT_APP_DEBUG=true npm start
```

## 📈 Performance Optimization

### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- Vector similarity index
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

### Frontend Optimization
```bash
# Analyze bundle size
cd frontend
npm install -g webpack-bundle-analyzer
npm run build
npx webpack-bundle-analyzer build/static/js/*.js
```

## 🔧 Advanced Configuration

### Custom Model Configuration
```python
# Add custom models in backend/app/core/config.py
SUPPORTED_MODELS = [
    "mistral",
    "llama2",
    "codellama",
    "custom-model"  # Add your custom models here
]
```

### Custom Frontend Themes
```typescript
// Modify frontend/src/App.tsx theme configuration
const theme = createTheme({
  palette: {
    primary: { main: '#your-color' },
    secondary: { main: '#your-secondary-color' },
    mode: 'light' // or 'dark'
  }
});
```

## 📞 Support & Documentation

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Component Documentation
- **Material-UI**: https://mui.com/
- **React**: https://reactjs.org/docs
- **FastAPI**: https://fastapi.tiangolo.com/

### Log Files
```bash
# Backend logs
tail -f logs/app.log

# Frontend logs (browser console)
# Database logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

## 🎯 Final Verification

After deployment, verify all components:

```bash
# 1. Backend API health
curl http://localhost:8000/health

# 2. Database connection
curl http://localhost:8000/system/status

# 3. Frontend accessibility
curl http://localhost:3000

# 4. Ollama integration
curl http://localhost:8000/models

# 5. Full system test
# Upload a document, create a conversation, and test RAG functionality
```

## 🚀 Success!

Your secure RAG system is now fully deployed and operational. The system provides:

- ✅ **Complete Privacy**: All data processing happens locally
- ✅ **Production Ready**: Scalable architecture with proper security
- ✅ **User Friendly**: Modern React interface with real-time features
- ✅ **AI Powered**: Local LLM integration with document retrieval
- ✅ **Fully Featured**: Document management, chat, and model configuration

**Next Steps**:
1. Upload your first documents through the web interface
2. Start a conversation and test the RAG functionality
3. Configure your preferred AI models in the settings
4. Explore the document search and management features

**Happy RAG-ing!** 🎉