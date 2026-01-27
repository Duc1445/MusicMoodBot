# 🚀 Quick Start Guide

## Merged Project - Music Mood Prediction

The project is now organized as a unified full-stack application at: **`d:\MMB_FRONTBACK\merged`**

### Structure Overview

```
merged/
├── backend/              # FastAPI REST API server
│   ├── main.py          # Entry point (runs on port 8000)
│   ├── src/
│   │   ├── api/         # API routes
│   │   ├── services/    # Business logic
│   │   ├── database/    # Database operations
│   │   ├── ranking/     # ML ranking algorithms
│   │   └── test/        # Tests
│   └── requirements.txt
│
├── frontend/            # Flet UI Application
│   ├── main.py         # Entry point
│   ├── src/
│   │   ├── screens/    # UI screens
│   │   ├── components/ # Reusable UI components
│   │   ├── services/   # Frontend services
│   │   └── config/     # Configuration
│   └── requirements.txt
│
├── requirements.txt     # Combined dependencies
├── setup.bat           # Windows setup script
├── setup.sh            # Linux/Mac setup script
└── .env.example        # Configuration template
```

## Installation (Windows)

### Option 1: Automatic Setup
```powershell
cd d:\MMB_FRONTBACK\merged
.\setup.bat
```

### Option 2: Manual Setup

**Step 1:** Install dependencies
```powershell
cd d:\MMB_FRONTBACK\merged
pip install -r requirements.txt
```

**Step 2:** Configure backend
```powershell
cd backend
copy .env.example .env
```

**Step 3:** Initialize database
```powershell
python -m backend.database
```

## Running the Application

### Terminal 1 - Backend Server
```powershell
cd d:\MMB_FRONTBACK\merged\backend
python -m uvicorn backend.main:app --reload
```
✅ API will be available at: http://localhost:8000
📚 API Documentation: http://localhost:8000/api/docs

### Terminal 2 - Frontend Application
```powershell
cd d:\MMB_FRONTBACK\merged\frontend
python main.py
```
✅ Flet UI will launch

## Testing

```powershell
cd d:\MMB_FRONTBACK\merged
pytest backend/src/test/ -v
```

## Key Features

✨ **Backend (FastAPI)**
- RESTful API endpoints for music mood prediction
- ML-powered mood classification
- User preferences and history tracking
- Search and ranking services

✨ **Frontend (Flet)**
- Modern, responsive UI
- Chat interface for recommendations
- Music history tracking
- User authentication and profiles
- Mood-based playlist generation

## Important Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI application entry point |
| `backend/database.py` | Database initialization and models |
| `backend/src/api/mood_api.py` | API routes and endpoints |
| `frontend/main.py` | Flet application entry point |
| `frontend/src/screens/chat_screen.py` | Main chat/recommendation screen |
| `requirements.txt` | All dependencies (backend + frontend) |

## Troubleshooting

**Port 8000 already in use?**
```powershell
python -m uvicorn backend.main:app --reload --port 8001
```

**Import errors?**
```powershell
# Ensure you're in the right directory
cd d:\MMB_FRONTBACK\merged
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Database issues?**
```powershell
# Reinitialize database
cd backend
python -m backend.database
```

## Documentation

- See `merged/README.md` for full documentation
- See `backend/README.md` for backend-specific details
- See `frontend/README.md` for frontend-specific details

---

**Happy coding! 🎵**
