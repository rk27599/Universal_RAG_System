#!/bin/bash

# ==============================================================================
# PostgreSQL + pgvector Setup Script for RAG System
# ==============================================================================
# This script installs PostgreSQL, pgvector extension, and sets up the database
# for optimal vector search performance (50x faster than SQLite)
# ==============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration from .env
DB_NAME="rag_database"
DB_USER="rag_user"
DB_PASSWORD="secure_rag_password_2024"
DB_HOST="localhost"
DB_PORT="5432"

echo -e "${BLUE}==============================================================================
PostgreSQL + pgvector Setup for RAG System
==============================================================================${NC}\n"

# ==============================================================================
# Step 1: Detect OS and Install PostgreSQL
# ==============================================================================
echo -e "${YELLOW}[1/6] Detecting OS and checking PostgreSQL installation...${NC}"

if command -v psql &> /dev/null; then
    PG_VERSION=$(psql --version | awk '{print $3}' | cut -d. -f1)
    echo -e "${GREEN}✓ PostgreSQL ${PG_VERSION} already installed${NC}"
else
    echo -e "${BLUE}PostgreSQL not found. Installing...${NC}"

    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Check for specific Linux distribution
        if [ -f /etc/debian_version ]; then
            # Debian/Ubuntu
            echo -e "${BLUE}Detected Debian/Ubuntu. Installing PostgreSQL...${NC}"
            sudo apt-get update
            sudo apt-get install -y postgresql postgresql-contrib postgresql-server-dev-all
        elif [ -f /etc/redhat-release ]; then
            # RHEL/CentOS/Fedora
            echo -e "${BLUE}Detected RHEL/CentOS/Fedora. Installing PostgreSQL...${NC}"
            sudo dnf install -y postgresql-server postgresql-contrib postgresql-devel
            sudo postgresql-setup --initdb --unit postgresql
        else
            echo -e "${RED}✗ Unsupported Linux distribution${NC}"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo -e "${BLUE}Detected macOS. Installing PostgreSQL via Homebrew...${NC}"
        if ! command -v brew &> /dev/null; then
            echo -e "${RED}✗ Homebrew not installed. Please install Homebrew first:${NC}"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        brew install postgresql@15
    else
        echo -e "${RED}✗ Unsupported operating system: $OSTYPE${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ PostgreSQL installed successfully${NC}"
fi

# ==============================================================================
# Step 2: Start PostgreSQL Service
# ==============================================================================
echo -e "\n${YELLOW}[2/6] Starting PostgreSQL service...${NC}"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    echo -e "${GREEN}✓ PostgreSQL service started and enabled${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew services start postgresql@15
    echo -e "${GREEN}✓ PostgreSQL service started${NC}"
fi

# Wait for PostgreSQL to be ready
sleep 2

# ==============================================================================
# Step 3: Install pgvector Extension
# ==============================================================================
echo -e "\n${YELLOW}[3/6] Installing pgvector extension...${NC}"

# Check if pgvector is already installed
if sudo -u postgres psql -c "SELECT * FROM pg_available_extensions WHERE name='vector';" 2>/dev/null | grep -q vector; then
    echo -e "${GREEN}✓ pgvector already installed${NC}"
else
    echo -e "${BLUE}Installing pgvector from source...${NC}"

    # Install build dependencies
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            sudo apt-get install -y git build-essential postgresql-server-dev-all
        elif [ -f /etc/redhat-release ]; then
            sudo dnf install -y git gcc make postgresql-devel
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # pgvector is available via Homebrew on macOS
        brew install pgvector
    fi

    # Clone and install pgvector (for Linux)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        TEMP_DIR=$(mktemp -d)
        cd "$TEMP_DIR"
        git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
        cd pgvector
        make
        sudo make install
        cd -
        rm -rf "$TEMP_DIR"
    fi

    echo -e "${GREEN}✓ pgvector installed successfully${NC}"
fi

# ==============================================================================
# Step 4: Create Database and User
# ==============================================================================
echo -e "\n${YELLOW}[4/6] Creating database and user...${NC}"

# Check if user exists
if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo -e "${BLUE}User '$DB_USER' already exists. Updating password...${NC}"
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
else
    echo -e "${BLUE}Creating user '$DB_USER'...${NC}"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
fi

# Check if database exists
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${BLUE}Database '$DB_NAME' already exists${NC}"
else
    echo -e "${BLUE}Creating database '$DB_NAME'...${NC}"
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
fi

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL ON SCHEMA public TO $DB_USER;"

echo -e "${GREEN}✓ Database and user configured${NC}"

# ==============================================================================
# Step 5: Enable pgvector Extension
# ==============================================================================
echo -e "\n${YELLOW}[5/6] Enabling pgvector extension in database...${NC}"

sudo -u postgres psql -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo -e "${GREEN}✓ pgvector extension enabled${NC}"

# ==============================================================================
# Step 6: Initialize Database Tables
# ==============================================================================
echo -e "\n${YELLOW}[6/6] Initializing database tables...${NC}"

# Check if Python environment is ready
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not found. Skipping table initialization.${NC}"
    echo -e "${YELLOW}Run 'python init_db.py' manually after activating your virtual environment.${NC}"
else
    # Activate virtual environment and run initialization
    source venv/bin/activate
    python init_db.py
    echo -e "${GREEN}✓ Database tables initialized${NC}"
fi

# ==============================================================================
# Verification
# ==============================================================================
echo -e "\n${BLUE}==============================================================================
Verifying Installation
==============================================================================${NC}\n"

# Test connection
echo -e "${YELLOW}Testing database connection...${NC}"
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    exit 1
fi

# Verify pgvector
echo -e "${YELLOW}Verifying pgvector extension...${NC}"
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT extversion FROM pg_extension WHERE extname='vector';" | grep -q "0.5"; then
    echo -e "${GREEN}✓ pgvector extension active${NC}"
else
    echo -e "${RED}✗ pgvector extension not found${NC}"
    exit 1
fi

# ==============================================================================
# Success Summary
# ==============================================================================
echo -e "\n${GREEN}==============================================================================
✓ PostgreSQL + pgvector Setup Complete!
==============================================================================${NC}\n"

echo -e "${BLUE}Database Information:${NC}"
echo -e "  Host:     ${DB_HOST}"
echo -e "  Port:     ${DB_PORT}"
echo -e "  Database: ${DB_NAME}"
echo -e "  User:     ${DB_USER}"
echo -e "  Password: ${DB_PASSWORD}"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "  1. Ensure ../.env file contains:"
echo -e "     ${YELLOW}DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}${NC}"
echo -e ""
echo -e "  2. (Optional) Migrate existing SQLite data:"
echo -e "     ${YELLOW}python scripts/migrate_sqlite_to_postgres.py${NC}"
echo -e ""
echo -e "  3. Start the application:"
echo -e "     ${YELLOW}python main.py${NC}"
echo -e ""
echo -e "  4. Verify 50x performance improvement with:"
echo -e "     ${YELLOW}python tests/test_vector_search_performance.py${NC}"

echo -e "\n${GREEN}🚀 Your RAG system is now ready for high-performance vector search!${NC}\n"
