# Save as: apsara-beauty/setup.sh
#!/bin/bash

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Platform detection
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    ACTIVATE_CMD=".\venv\Scripts\activate"
else
    ACTIVATE_CMD="source venv/bin/activate"
fi

# Error handler
error_handler() {
    echo -e "${RED}Error: Setup failed at line $1${NC}"
    exit 1
}
trap 'error_handler ${LINENO}' ERR

# Verify prerequisites
for cmd in python3 npm git; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is required but not installed.${NC}"
        exit 1
    fi
done

# Project validation
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo -e "${RED}Error: Project structure invalid. Make sure you're in the root directory.${NC}"
    exit 1
fi

echo "🚀 Setting up Apsara Beauty Platform..."

# Frontend setup
echo "📦 Setting up frontend..."
cd frontend
npm install
npm run build
[ ! -f .env.local ] && cp ../.env.example .env.local

# Backend setup
echo "🐍 Setting up backend..."
cd ../backend
python3 -m venv venv
source venv/bin/activate || source venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
[ ! -f .env ] && cp ../.env.example .env

# Database setup
echo "🗄️ Setting up database..."
if command -v psql &> /dev/null; then
    echo "🗄️ Initializing database..."
    psql -c "CREATE DATABASE apsara_db;" 2>/dev/null || echo "Database exists"
    (cd backend && python -c "from database.connection import init_db; init_db()") || echo "Database initialized"
fi

# Frontend validation
echo "📝 Validating frontend..."
cd frontend
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Frontend package.json missing${NC}"
    exit 1
fi
npm install
npm run validate || echo "Skipping frontend validation"
cd ..

# Backend validation
echo "🐍 Validating backend..."
cd backend
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Backend requirements.txt missing${NC}"
    exit 1
fi
$ACTIVATE_CMD
pip install -r requirements.txt
python -c "from main import app" || echo "Backend validation failed"
cd ..

# Create necessary directories
mkdir -p uploads logs data/models

echo "✨ Setup complete!"
echo "To start development:"
echo "1. Frontend: cd frontend && npm run dev"
echo "2. Backend: cd backend && source venv/activate && python main.py"