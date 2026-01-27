# Music Mood Prediction Application - Merged Project

A full-stack music recommendation application combining FastAPI backend with Flet frontend.

## Project Structure

```
merged/
├── backend/           # FastAPI backend service
│   ├── src/
│   │   ├── api/      # API endpoints
│   │   ├── database/ # Database operations
│   │   ├── services/ # Business logic
│   │   ├── ranking/  # Ranking algorithms
│   │   ├── pipelines/# ML pipelines
│   │   └── test/     # Backend tests
│   ├── main.py       # FastAPI entry point
│   └── requirements.txt
│
├── frontend/         # Flet UI application
│   ├── src/
│   │   ├── screens/  # UI screens
│   │   ├── components/ # Reusable components
│   │   ├── services/ # Frontend services
│   │   └── config/   # Frontend config
│   ├── main.py       # Flet entry point
│   └── requirements.txt
│
├── requirements.txt  # Unified dependencies
└── README.md         # This file
```

## Setup & Installation

### 1. Install Dependencies
```bash
cd merged
pip install -r requirements.txt
```

### 2. Setup Environment
Copy `.env.example` to `.env` and configure:
```bash
cd backend
cp .env.example .env
```

### 3. Initialize Database
```bash
cd backend
python -m backend.database
```

### 4. Run Backend Server
```bash
cd backend
python -m uvicorn backend.main:app --reload
```

### 5. Run Frontend Application
```bash
cd frontend
python main.py
```

## Development

### Backend
- **Framework**: FastAPI
- **Location**: `backend/`
- **API Docs**: http://localhost:8000/api/docs

### Frontend
- **Framework**: Flet (Python)
- **Location**: `frontend/`
- **Entry Point**: `frontend/main.py`

## Features

- 🎵 Music mood prediction using ML
- 🔍 Smart search and filtering
- 📊 Personalized recommendations
- 💾 User history tracking
- 🎨 Modern UI with Flet

## Testing

Run tests with:
```bash
pytest backend/src/test/
```

## Documentation

See individual README files in:
- `backend/README.md`
- `frontend/README.md`
