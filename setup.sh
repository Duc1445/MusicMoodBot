#!/bin/bash

# Music Mood Prediction - Development Environment Setup

echo "🎵 Setting up Music Mood Prediction Application..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Setup backend
echo "🔧 Setting up backend..."
cd backend
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from .env.example"
fi

# Initialize database
echo "💾 Initializing database..."
python -m backend.database || true

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Start development:"
echo "   Terminal 1: cd backend && python -m uvicorn backend.main:app --reload"
echo "   Terminal 2: cd frontend && python main.py"
