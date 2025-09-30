# Save as: apsara-beauty/setup.sh
#!/bin/bash

echo "Setting up Apsara Beauty Platform..."

# Frontend setup
echo "Setting up frontend..."
cd frontend
npm install
cp .env.example .env.local

# Backend setup
echo "Setting up backend..."
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env

# Create necessary directories
mkdir -p uploads
mkdir -p logs

echo "Setup complete! 🎉"
echo "To start development:"
echo "1. Frontend: cd frontend && npm run dev"
echo "2. Backend: cd backend && source venv/bin/activate && python main.py"