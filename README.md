# Secure RAG System - Web Application

A production-ready **Retrieval-Augmented Generation (RAG) web application** with complete data sovereignty. Features secure authentication, document upload, semantic search, real-time chat with local LLMs, and PostgreSQL vector storage.

## 🚀 Key Features

- **🔐 Secure Authentication**: JWT-based auth with bcrypt password hashing
- **📄 Document Processing**: Upload HTML, PDF, TXT files with async processing
- **🧠 Semantic Search**: PostgreSQL pgvector with 50x faster vector search
- **💬 Real-Time Chat**: WebSocket-based chat with streaming responses
- **🤖 Local LLM Integration**: Ollama integration (Mistral, Llama2, CodeLlama)
- **📊 Rich Metadata**: Track sources, sections, and similarity scores
- **🎨 Modern UI**: React + TypeScript + Material-UI frontend
- **⚡ High Performance**: Async document processing, connection pooling
- **🛡️ Security-First**: Local-only deployment, no external dependencies
- **📈 Production-Ready**: Multi-worker support, SSL/TLS, rate limiting

## 📋 Requirements

- **Python 3.12+**
- **Node.js 18+** (for frontend)
- **PostgreSQL 14+** with pgvector extension
- **Ollama** (for LLM integration)

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

### 4. Start Ollama (Optional but Recommended)
```bash
# Install from https://ollama.ai
ollama serve
ollama pull mistral
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
├── README.md                        # This file
├── CLAUDE.md                        # Project instructions for AI assistants
├── LICENSE                          # Open source license
├── requirements.txt                 # Core Python dependencies
│
├── docs/                            # Webapp documentation
│   ├── NETWORK_SETUP.md            # Network access configuration
│   └── PRODUCTION_DEPLOYMENT.md     # Production deployment guide
│
├── webapp/                          # 🎯 Main Web Application
│   ├── README.md                   # Webapp overview
│   ├── INSTALLATION_GUIDE.md       # Detailed setup instructions
│   │
│   ├── backend/                    # FastAPI Backend (Python)
│   │   ├── api/                   # REST API endpoints
│   │   │   ├── auth.py           # Authentication
│   │   │   ├── chat.py           # WebSocket chat + messages
│   │   │   ├── documents.py      # Document upload/management
│   │   │   └── models.py         # Ollama model info
│   │   │
│   │   ├── core/                  # Core configuration
│   │   │   ├── config.py         # Settings management
│   │   │   ├── database.py       # SQLAlchemy setup
│   │   │   └── security.py       # JWT & password hashing
│   │   │
│   │   ├── models/                # Database models
│   │   │   ├── user.py           # User model
│   │   │   ├── document.py       # Document & Chunk models
│   │   │   └── conversation.py   # Chat models
│   │   │
│   │   ├── services/              # Business logic
│   │   │   ├── document_service.py    # Document processing
│   │   │   ├── embedding_service.py   # Vector embeddings
│   │   │   ├── rag_service.py         # RAG retrieval
│   │   │   └── ollama_service.py      # LLM integration
│   │   │
│   │   ├── utils/                 # Utility modules
│   │   │   └── async_web_scraper.py   # HTML content extraction
│   │   │
│   │   ├── main.py                # FastAPI application entry
│   │   ├── init_db.py             # Database initialization
│   │   └── requirements.txt       # Backend dependencies
│   │
│   ├── frontend/                   # React Frontend (TypeScript)
│   │   ├── src/
│   │   │   ├── components/        # React components
│   │   │   │   ├── Auth/         # Login, Register
│   │   │   │   ├── Chat/         # Chat interface, conversations
│   │   │   │   ├── Documents/    # Upload, document list
│   │   │   │   ├── Layout/       # App layout, sidebar
│   │   │   │   └── Settings/     # Model settings
│   │   │   │
│   │   │   ├── contexts/          # React contexts
│   │   │   │   ├── AuthContext.tsx    # Auth state
│   │   │   │   └── ChatContext.tsx    # Chat state + WebSocket
│   │   │   │
│   │   │   ├── services/          # API services
│   │   │   │   └── api.ts        # Axios API client
│   │   │   │
│   │   │   ├── config/            # Configuration
│   │   │   │   └── config.ts     # App settings
│   │   │   │
│   │   │   ├── App.tsx            # Main app component
│   │   │   └── index.tsx          # React entry point
│   │   │
│   │   ├── public/                # Static assets
│   │   ├── package.json           # Node dependencies
│   │   └── README.md              # Frontend documentation
│   │
│   └── docs/                       # Webapp Documentation
│       ├── README.md              # Docs index
│       ├── ADMIN_GUIDE.md         # Admin operations
│       ├── USER_GUIDE.md          # User manual
│       ├── DEPLOYMENT_GUIDE.md    # Docker deployment
│       ├── HANDOVER_DOCUMENT.md   # Project handover
│       └── architecture/          # Architecture decisions
│
├── archive/                        # Old RAG System (Reference)
│   └── old_rag_system/
│       ├── src/                   # Old RAG source code
│       ├── examples/              # Usage examples
│       ├── tests/                 # Tests
│       ├── notebooks/             # Jupyter notebooks
│       └── docs/                  # Old RAG documentation
│
└── venv/                          # Python virtual environment
```

## 🎯 Main Components

### Backend (FastAPI + Python)
- **Authentication**: JWT tokens, bcrypt password hashing, session management
- **Document Processing**: Async upload, chunking, embedding generation
- **Vector Search**: PostgreSQL pgvector with HNSW indexing (50x faster)
- **RAG System**: TF-IDF retrieval, semantic search, context building
- **Chat API**: WebSocket real-time messaging, conversation management
- **LLM Integration**: Ollama API for Mistral, Llama2, CodeLlama

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

### Deployment
- [Network Setup](docs/NETWORK_SETUP.md) - LAN access configuration
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md) - Production guide
- [Docker Deployment](webapp/docs/DEPLOYMENT_GUIDE.md) - Docker setup

### Development
- [Architecture](webapp/docs/architecture/) - System design
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

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral

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

## 🤖 Ollama Setup

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
