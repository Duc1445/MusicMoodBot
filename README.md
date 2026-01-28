# 🎵 Music Mood Prediction

**Full-stack music recommendation system with ML-powered mood prediction.**

Combines FastAPI backend + Flet UI + SQLite database for intelligent music recommendations based on mood.

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start backend (Terminal 1)
python backend/run_server.py
# API: http://localhost:8000/api/docs

# 3. Start frontend (Terminal 2)
python frontend/main.py
```

---

## 🏗️ Project Structure

| Component | Tech | Entry Point |
|-----------|------|-------------|
| **Backend** | FastAPI | `backend/run_server.py` |
| **Frontend** | Flet | `frontend/main.py` |
| **Database** | SQLite | `backend/src/database/music.db` |
| **ML Engine** | Python | Valence-Arousal model |

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed architecture.

---

## 🎯 Features

✅ **Music Analysis**
- 🎵 Mood prediction (happy, sad, stressed, energetic, thoughtful)
- 🔍 Smart search with Vietnamese support
- 📊 Song similarity matching

✅ **Recommendations**
- 📈 Personalized recommendations based on mood
- ⏰ Time-based suggestions
- 🎭 Smart mood transition planning

✅ **User Management**
- 👤 User accounts (login/signup)
- 📝 Listening history
- ❤️ Preferences learning
- 📋 Playlist management

✅ **Data**
- 💾 30+ pre-loaded songs
- 📊 ML attributes (valence, arousal, energy, etc.)
- 🔐 Secure authentication

---

## 🛠️ Commands

### Backend
```bash
# Start server
python backend/run_server.py

# Test backend
pytest backend/src/test/
```

### Frontend
```bash
# Start UI
python frontend/main.py
```

### Tools & Scripts
```bash
# Run demo
python demos/demo_with_ui.py

# Calculate mood attributes
python tools/calculate_music_attributes.py
```

---

## 📁 Key Files

```
backend/
├── main.py              ← FastAPI app
├── run_server.py        ← Server launcher
├── .env                 ← Config
└── src/
    ├── api/             ← API endpoints
    ├── database/        ← DB + music.db
    ├── pipelines/       ← ML models
    ├── services/        ← Business logic
    └── repo/            ← Data access

frontend/
├── main.py              ← UI entry point
└── src/
    ├── screens/         ← Pages
    ├── components/      ← UI widgets
    ├── services/        ← Backend calls
    └── config/          ← Themes
```

---

## 📦 Database

**Primary**: `backend/src/database/music.db` (76KB)
- 30 songs with mood attributes
- 2 user accounts
- 11 tables (songs, users, history, etc.)

**Backup**: `music_final_backup_20260128_082940.db`

---

## 🔧 Environment

Create/edit `backend/.env`:
```env
DATABASE_PATH=music.db
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
MOOD_ENGINE_AUTO_FIT=true
SEARCH_TOP_K=10
```

---

## 📚 Documentation

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Detailed architecture
- [backend/README.md](backend/README.md) - Backend guide
- [frontend/README.md](frontend/README.md) - Frontend guide
- [docs_src/README.md](docs_src/README.md) - Additional docs

---

## 🚀 Status

✅ **Production Ready**
- Database consolidated & optimized
- ML models working
- API endpoints tested
- UI responsive
- Backup created

---

## 📊 Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Flet (Python) |
| Backend | FastAPI |
| Database | SQLite3 |
| ML | Scikit-learn, NumPy |
| NLP | Vietnamese text processing |

---

**Last Updated**: 2026-01-28 | **Version**: 2.1.0
