# 📦 MUSIC MOOD PREDICTION - OPTIMIZED STRUCTURE

**Status**: ✅ Refactored & Optimized  
**Last Updated**: 2026-01-28  
**Version**: 2.1.0

---

## 🎯 Project Overview

Full-stack music recommendation system with ML-powered mood prediction.

- **Backend**: FastAPI (Python)
- **Frontend**: Flet (Cross-platform UI)
- **Database**: SQLite (music.db)
- **ML Engine**: Valence-Arousal Mood Model

---

## 📁 CLEAN STRUCTURE

```
MMB_FRONTBACK/
├── 🎯 ENTRY POINTS
│   ├── backend/main.py           ⭐ FastAPI Application
│   ├── backend/run_server.py     🚀 Start Backend Server
│   └── frontend/main.py          ⭐ Flet UI Application
│
├── 🔧 BACKEND (FastAPI)
│   ├── .env                      ⚙️  Environment config
│   ├── requirements.txt          📦 Backend dependencies
│   └── src/
│       ├── api/                  🔌 API Endpoints
│       │   ├── mood_api.py
│       │   └── extended_api.py
│       ├── database/             💾 Database Management
│       │   ├── database.py       (Main DB connection)
│       │   ├── music.db          ⭐ PRIMARY DATABASE
│       │   ├── music_final_backup_*.db
│       │   ├── init_db.py        (Initialize schema)
│       │   ├── migrate.py        (Schema migration)
│       │   └── bulk_update.py    (Batch updates)
│       ├── pipelines/            🤖 ML Modules
│       │   ├── mood_engine.py    (Valence-Arousal model)
│       │   ├── mood_transition.py
│       │   ├── text_mood_detector.py (Vietnamese/English)
│       │   ├── smart_recommendation.py
│       │   └── song_similarity.py
│       ├── ranking/              📊 Ranking System
│       │   └── preference_model.py
│       ├── repo/                 🗂️  Data Access Layer
│       │   ├── db_pool.py        (Connection pooling)
│       │   ├── history_repo.py
│       │   └── song_repo.py
│       ├── search/               🔍 Search Engine
│       │   └── tfidf_search.py   (TF-IDF search)
│       └── services/             ⚙️  Business Logic
│           ├── analytics_service.py
│           ├── cache_service.py
│           ├── event_system.py
│           ├── export_service.py
│           ├── history_service.py
│           ├── mood_services.py
│           ├── playlist_service.py
│           ├── preference_learning.py
│           ├── queue_service.py
│           ├── ranking_service.py
│           ├── time_recommender.py
│           ├── constants.py
│           └── helpers.py
│
├── 🎨 FRONTEND (Flet)
│   ├── requirements.txt          📦 Frontend dependencies
│   └── src/
│       ├── config/               ⚙️  Configuration
│       │   ├── constants.py
│       │   ├── theme.py
│       │   └── theme_professional.py
│       ├── components/           🧩 Reusable UI Components
│       │   ├── ui_components.py
│       │   ├── ui_components_pro.py
│       │   ├── animated_mascot.py
│       │   ├── decoration_mascot.py
│       │   └── talking_animator.py
│       ├── screens/              📺 Page Screens
│       │   ├── login_screen.py
│       │   ├── signup_screen.py
│       │   ├── chat_screen.py
│       │   ├── history_screen.py
│       │   └── profile_screen.py
│       ├── services/             🔗 Backend Integration
│       │   ├── auth_service.py
│       │   ├── chat_service.py
│       │   └── history_service.py
│       └── utils/                🛠️  Utilities
│           ├── state_manager.py  (UI State)
│           └── helpers.py
│
├── 📚 DOCUMENTATION
│   ├── README.md                 📖 Main guide
│   ├── STRUCTURE.md              🗺️  Old structure (deprecated)
│   ├── PROJECT_STRUCTURE.md      🗺️  This file (NEW)
│   └── docs_src/
│       ├── README.md             (Index)
│       ├── docs_be/              (Backend docs)
│       └── docs_fr/              (Frontend docs)
│
├── 🚀 DEPLOYMENT & TESTING
│   ├── scripts/                  🔨 Automation Scripts
│   │   ├── run_backend.py
│   │   └── README.md
│   ├── demos/                    🎬 Demo Applications
│   │   ├── demo_with_ui.py
│   │   └── README.md
│   ├── tools/                    🔧 Utility Tools
│   │   ├── calculate_music_attributes.py
│   │   └── README.md
│   └── tests/                    ✅ Test Suites
│       ├── README.md
│       └── (Backend tests in backend/src/test/)
│
├── 📦 ROOT CONFIG
│   ├── requirements.txt          📋 All dependencies
│   ├── package.json              📝 Project metadata
│   ├── .gitignore                🚫 Git ignore rules
│   └── .git/                     🔀 Version control
```

---

## 🎯 Quick Commands

### Backend
```bash
# Start server
python backend/run_server.py
# Access: http://localhost:8000/api/docs
```

### Frontend
```bash
# Run UI
python frontend/main.py
```

### Scripts & Tools
```bash
# Run demo
python demos/demo_with_ui.py

# Calculate mood attributes
python tools/calculate_music_attributes.py

# Run tests
pytest backend/src/test/
```

---

## 🗑️ CLEANUP CHANGES

### ✅ Deleted Files (Optimized)
- ~~`frontend/app.py`~~ → Consolidated to `main.py`
- ~~`frontend/frontend.py`~~ → Consolidated to `main.py`
- ~~`frontend/test.py`~~ → Moved to `/tests`
- ~~`backend/.env.example`~~ → Unnecessary (use `.env`)
- ~~`frontend/user_state.json`~~ → Temp state (recreated at runtime)
- ~~`config/`~~ → Empty folder
- ~~`docs/`~~ → Replaced by `docs_src/`
- ~~`logs/`~~ → Runtime only
- ~~`setup.bat`, `setup.sh`~~ → Replaced by scripts/
- ~~`start_backend.bat`, `start_frontend.bat`~~ → Use Python scripts
- ~~All `__pycache__/`~~ → Build artifacts

### 📊 Size Freed
- **Total**: ~300KB cleaned
- **Structure**: Leaner, more maintainable

---

## 📈 Database (Backend)

### Primary Database
```
backend/src/database/music.db (76KB)
├── 30 Songs (full mood attributes)
├── 2 User Accounts (demo, hung)
├── 7 Recommendations
├── 11 Tables:
│   ├── songs (core data)
│   ├── users (auth)
│   ├── recommendations
│   ├── chat_history
│   ├── listening_history
│   ├── playlists
│   ├── playlist_songs
│   ├── playlist_follows
│   ├── user_preferences
│   ├── user_interactions
│   └── recommendation_history
```

### Backup
```
backend/src/database/music_final_backup_20260128_082940.db
└── Complete copy for safety
```

---

## 🔐 Environment Setup

Create `.env` in backend (or use existing):
```env
DATABASE_PATH=music.db
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
MOOD_ENGINE_AUTO_FIT=true
SEARCH_TOP_K=10
```

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| **Python Files** | ~45 |
| **API Endpoints** | 20+ |
| **Database Tables** | 11 |
| **Songs** | 30 |
| **Components** | 8 |
| **Total Size** | ~2MB (excluding venv) |

---

## 🚀 Getting Started

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Backend**
   ```bash
   python backend/run_server.py
   ```

3. **Start Frontend** (in new terminal)
   ```bash
   python frontend/main.py
   ```

4. **Access API Docs**
   - http://localhost:8000/api/docs

---

## 📝 File Naming Convention

- **Services**: `*_service.py`
- **Repositories**: `*_repo.py`
- **APIs**: `*_api.py`
- **Pipelines**: `*_model.py` or `*_engine.py`
- **Screens**: `*_screen.py`
- **Components**: `*_component.py` or `*_ui.py`

---

## ✨ Best Practices

✅ **DO**
- Use services for business logic
- Keep components reusable
- Document complex functions
- Use type hints
- Test before deployment

❌ **DON'T**
- Hardcode paths (use `os.path`)
- Mix concerns (API logic in UI)
- Create duplicate entry points
- Leave debug code in production
- Ignore error handling

---

## 🔄 Continuous Improvement

- Update `.gitignore` when adding new build artifacts
- Keep `requirements.txt` synchronized
- Document new services in respective README files
- Use semantic versioning

---

**Created**: 2026-01-28  
**Maintained by**: AI Assistant  
**Status**: Production Ready ✅
