@echo off
REM Music Mood Prediction - Development Environment Setup

echo.
echo 🎵 Setting up Music Mood Prediction Application...
echo.

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Setup backend
echo 🔧 Setting up backend...
cd backend
if not exist .env (
    copy .env.example .env
    echo ✅ Created .env from .env.example
)

REM Initialize database
echo 💾 Initializing database...
python -m backend.database

cd ..

echo.
echo ✅ Setup complete!
echo.
echo 🚀 Start development:
echo    Terminal 1: cd backend ^&^& python -m uvicorn backend.main:app --reload
echo    Terminal 2: cd frontend ^&^& python main.py
echo.
