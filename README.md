Apsara - Divine Beauty Recommendations 🌸
AI-powered personalized skincare recommendation platform that analyzes your skin and suggests the perfect products for your unique needs.

Features
📸 AI-powered skin analysis from photos

💆‍♀️ Personalized product recommendations

💬 Interactive skincare chatbot

📺 Curated YouTube reviews integration

🔔 Daily beauty tips and deals notifications

📊 Skin progress tracking

Tech Stack
Frontend: Next.js, TypeScript, Emotion CSS

Backend: FastAPI, Python

ML/AI: TensorFlow, OpenCV

Database: PostgreSQL, Redis

Image Storage: Local Server Storage

Quick Start
Clone the repository

git clone [https://github.com/YOUR_USERNAME/apsara-beauty.git](https://github.com/YOUR_USERNAME/apsara-beauty.git)
cd apsara-beauty

Run the setup script

sh setup.sh

Start the development servers

# In Terminal 1
cd frontend && npm run dev

# In Terminal 2
cd backend && source venv/bin/activate && python main.py

Deployment
This project is designed to be deployed with a modern full-stack setup:

Frontend (Next.js): Host on Vercel for seamless, automated deployments.

Backend (FastAPI): Host on Render as a Web Service.

Database (PostgreSQL): Host on Render as a PostgreSQL instance.

Image Storage: The backend saves images to a local uploads directory. On a platform like Render, this will use their persistent disk storage.