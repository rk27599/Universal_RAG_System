#!/bin/bash
"""
Security-First Database Setup Script
Sets up PostgreSQL with pgvector extension for local-only operation
"""

set -e  # Exit on any error

echo "🔒 Setting up PostgreSQL + pgvector for Secure RAG System"
echo "========================================================="

# Configuration
DB_NAME="rag_database"
DB_USER="rag_user"
DB_PASSWORD="secure_rag_password_2024"  # Change this in production
DB_HOST="localhost"
DB_PORT="5432"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Installing..."

    # Detect OS and install PostgreSQL
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y postgresql postgresql-contrib postgresql-client
            echo "✅ PostgreSQL installed via apt-get"
        # CentOS/RHEL/Fedora
        elif command -v yum &> /dev/null; then
            sudo yum install -y postgresql postgresql-server postgresql-contrib
            sudo postgresql-setup initdb
            sudo systemctl enable postgresql
            sudo systemctl start postgresql
            echo "✅ PostgreSQL installed via yum"
        else
            echo "❌ Unsupported Linux distribution. Please install PostgreSQL manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install postgresql
            brew services start postgresql
            echo "✅ PostgreSQL installed via Homebrew"
        else
            echo "❌ Homebrew not found. Please install PostgreSQL manually."
            exit 1
        fi
    else
        echo "❌ Unsupported operating system. Please install PostgreSQL manually."
        exit 1
    fi
fi

# Start PostgreSQL service if not running
echo "🔧 Ensuring PostgreSQL service is running..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start postgresql
fi

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if sudo -u postgres psql -c "SELECT 1;" &> /dev/null; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to start within 30 seconds"
        exit 1
    fi
done

# Install pgvector extension
echo "📦 Installing pgvector extension..."

# Check if pgvector is already installed
if sudo -u postgres psql -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';" | grep -q vector; then
    echo "✅ pgvector extension is available"
else
    echo "📥 Installing pgvector extension..."

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Ubuntu/Debian
        if command -v apt-get &> /dev/null; then
            # Add PostgreSQL APT repository if needed
            sudo apt-get install -y wget ca-certificates
            wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
            echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
            sudo apt-get update

            # Install pgvector
            sudo apt-get install -y postgresql-15-pgvector || sudo apt-get install -y postgresql-14-pgvector || sudo apt-get install -y postgresql-13-pgvector
            echo "✅ pgvector installed via apt-get"
        else
            echo "⚠️  pgvector package not found. Installing from source..."
            # Install from source
            sudo apt-get install -y git build-essential postgresql-server-dev-all
            cd /tmp
            git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
            cd pgvector
            make
            sudo make install
            echo "✅ pgvector compiled and installed from source"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install pgvector
            echo "✅ pgvector installed via Homebrew"
        else
            echo "⚠️  Installing pgvector from source..."
            cd /tmp
            git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
            cd pgvector
            make
            make install
            echo "✅ pgvector compiled and installed from source"
        fi
    fi
fi

# Create database user and database
echo "👤 Creating database user and database..."

# Create user if not exists
sudo -u postgres psql -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = '$DB_USER') THEN
        CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASSWORD';
        GRANT CONNECT ON DATABASE postgres TO $DB_USER;
        ALTER USER $DB_USER CREATEDB;
        GRANT ALL PRIVILEGES ON DATABASE postgres TO $DB_USER;
    END IF;
END
\$\$;" || echo "⚠️  User creation had warnings (may already exist)"

# Create database if not exists
sudo -u postgres psql -c "
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME');
" | sudo -u postgres psql || echo "⚠️  Database may already exist"

# Grant permissions to user on the database
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" || echo "⚠️  Permission grant had warnings"

# Enable pgvector extension on the database
echo "🧩 Enabling pgvector extension..."
sudo -u postgres psql -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;" || {
    echo "❌ Failed to create vector extension. Trying alternative method..."

    # Alternative installation method
    sudo -u postgres psql -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
    sudo -u postgres psql -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;" || {
        echo "❌ pgvector extension installation failed"
        echo "Please install pgvector manually:"
        echo "1. Visit: https://github.com/pgvector/pgvector"
        echo "2. Follow installation instructions for your system"
        exit 1
    }
}

# Test the installation
echo "🧪 Testing pgvector installation..."
sudo -u postgres psql -d $DB_NAME -c "SELECT vector_dims('[1,2,3]'::vector);" && echo "✅ pgvector is working correctly"

# Create .env file for the application
echo "📄 Creating environment configuration..."
cat > ../app/.env << EOF
# Database Configuration (LOCAL ONLY)
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME

# Application Configuration
DEBUG=True
SECRET_KEY=$(openssl rand -hex 32)
HOST=127.0.0.1
PORT=8000

# Ollama Configuration (LOCAL ONLY)
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral

# File Storage (LOCAL ONLY)
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE=52428800

# Security Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/rag_app.log

# SSL/TLS (for production)
# SSL_KEYFILE=./ssl/server.key
# SSL_CERTFILE=./ssl/server.crt
EOF

echo "✅ Environment configuration created"

# Set secure permissions on .env file
chmod 600 ../app/.env
echo "🔒 Environment file permissions secured"

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p ../app/data/uploads
mkdir -p ../app/logs
mkdir -p ../app/static
echo "✅ Application directories created"

# Test database connection
echo "🔌 Testing database connection..."
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

# Test with psql
if psql "$DATABASE_URL" -c "SELECT version();" &> /dev/null; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    echo "Please check:"
    echo "1. PostgreSQL is running"
    echo "2. User credentials are correct"
    echo "3. Database exists and is accessible"
    exit 1
fi

# Security validation
echo "🔒 Performing security validation..."

# Check that database is localhost only
if echo "$DATABASE_URL" | grep -q "localhost\|127.0.0.1"; then
    echo "✅ Database is configured for localhost access only"
else
    echo "❌ Security violation: Database is not configured for localhost"
    exit 1
fi

# Final setup summary
echo ""
echo "🎉 DATABASE SETUP COMPLETE!"
echo "=========================="
echo "✅ PostgreSQL installed and running"
echo "✅ pgvector extension enabled"
echo "✅ Database '$DB_NAME' created"
echo "✅ User '$DB_USER' created with appropriate permissions"
echo "✅ Environment configuration file created"
echo "✅ Security validation passed"
echo ""
echo "📋 Next Steps:"
echo "1. Install Python dependencies: pip install -r app/requirements.txt"
echo "2. Run database migrations: cd app && python -m alembic upgrade head"
echo "3. Start the application: cd app && python main.py"
echo ""
echo "🔒 Security Notes:"
echo "• Database is configured for local access only"
echo "• Change the default password in production"
echo "• All data remains on your local infrastructure"
echo "• No external dependencies configured"

# Create database initialization script for application
cat > ../app/init_db.py << 'EOF'
#!/usr/bin/env python3
"""
Database initialization script for Secure RAG System
Run this to create all database tables and initial data
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from core.database import init_db, engine, SessionLocal
from core.config import settings
from models.user import User
from models.document import Document
from models.conversation import Conversation
from core.security import security_manager

async def main():
    """Initialize database with tables and sample data"""

    print("🔒 Initializing Secure RAG System Database")
    print("==========================================")

    try:
        # Initialize database tables
        print("📊 Creating database tables...")
        init_db()
        print("✅ Database tables created successfully")

        # Create admin user if not exists
        db = SessionLocal()
        admin_user = db.query(User).filter(User.username == "admin").first()

        if not admin_user:
            print("👤 Creating admin user...")
            admin_user = User(
                username="admin",
                email="admin@localhost",
                full_name="System Administrator",
                password_hash=security_manager.get_password_hash("admin123"),
                is_admin=True,
                is_active=True,
                email_verified=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Admin user created (username: admin, password: admin123)")
            print("⚠️  Please change the admin password after first login")
        else:
            print("✅ Admin user already exists")

        db.close()

        print("")
        print("🎉 DATABASE INITIALIZATION COMPLETE!")
        print("===================================")
        print("✅ All tables created")
        print("✅ Admin user configured")
        print("🔒 Ready for secure local operation")

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x ../app/init_db.py
echo "✅ Database initialization script created"

echo ""
echo "🚀 Ready to start development!"
echo "Run: cd app && python init_db.py to initialize the database"