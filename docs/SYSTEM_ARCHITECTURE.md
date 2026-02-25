# 🏗️ MusicMoodBot Production Backend Architecture

> Tài liệu kiến trúc hệ thống backend production-level

## 📋 Mục lục

1. [System Overview](#1-system-overview)
2. [Architecture Layers](#2-architecture-layers)
3. [Database Schema](#3-database-schema)
4. [API Design](#4-api-design)
5. [Chat Pipeline Flow](#5-chat-pipeline-flow)
6. [Component Details](#6-component-details)

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Flet UI)                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │   Login     │ │   Chat      │ │   History   │ │   Profile   │       │
│  │   Screen    │ │   Screen    │ │   Screen    │ │   Screen    │       │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘       │
└─────────┼───────────────┼───────────────┼───────────────┼───────────────┘
          │               │               │               │
          ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        REST API GATEWAY                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI + JWT Authentication + Rate Limiting + CORS             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CONTROLLER LAYER (Routers)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  /auth   │ │  /chat   │ │ /playlist│ │  /user   │ │ /search  │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
└───────┼────────────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │            │
        ▼            ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        SERVICE LAYER                                     │
│  ┌────────────┐ ┌────────────────────────────────────────────────┐      │
│  │  Auth      │ │             Chat Orchestrator                   │      │
│  │  Service   │ │  ┌──────────────────────────────────────────┐  │      │
│  └────────────┘ │  │ 1. Text Mood Detector (NLP)               │  │      │
│  ┌────────────┐ │  │ 2. Mood Engine (Song Selection)           │  │      │
│  │  User      │ │  │ 3. Preference Model (Personalization)     │  │      │
│  │  Service   │ │  │ 4. Curator Engine (Playlist Smoothing)    │  │      │
│  └────────────┘ │  └──────────────────────────────────────────┘  │      │
│  ┌────────────┐ └────────────────────────────────────────────────┘      │
│  │  Playlist  │ ┌────────────────────────────────────────────────┐      │
│  │  Service   │ │  Feedback Service → Preference Learning        │      │
│  └────────────┘ └────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        REPOSITORY LAYER                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  User    │ │  Song    │ │ History  │ │ Feedback │ │ Playlist │      │
│  │  Repo    │ │  Repo    │ │  Repo    │ │  Repo    │ │  Repo    │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
└───────┼────────────┼────────────┼────────────┼────────────┼─────────────┘
        │            │            │            │            │
        ▼            ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATABASE (SQLite/PostgreSQL)                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  users │ songs │ listening_history │ feedback │ playlists │ ...  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Clean Architecture** | 4 layers: Controller → Service → Repository → Database |
| **Single Responsibility** | Mỗi service/repo chỉ làm 1 việc |
| **Dependency Injection** | Services được inject qua constructors |
| **Repository Pattern** | Abstract data access, dễ switch database |
| **Orchestrator Pattern** | ChatOrchestrator điều phối toàn bộ pipeline |

---

## 2. Architecture Layers

### 2.1 Controller Layer (API Routes)

Xử lý HTTP requests, validation, authorization.

```
backend/
├── api/
│   ├── __init__.py
│   ├── app.py              # FastAPI app entry
│   └── v1/
│       ├── __init__.py
│       ├── auth.py         # POST /auth/login, /auth/register
│       ├── chat.py         # POST /chat/message, /chat/feedback
│       ├── playlist.py     # GET/POST playlist endpoints
│       ├── user.py         # GET/PUT user profile
│       └── search.py       # GET /search
```

### 2.2 Service Layer

Business logic, không phụ thuộc HTTP/database.

```
backend/
├── services/
│   ├── __init__.py
│   ├── auth_service.py          # Authentication logic
│   ├── user_service.py          # User profile management
│   ├── chat_orchestrator.py     # ⭐ Main chat pipeline
│   ├── recommendation_service.py # Song recommendation
│   ├── playlist_service.py      # Playlist management
│   └── feedback_service.py      # Feedback processing
```

### 2.3 Repository Layer

Data access abstraction.

```
backend/
├── repositories/
│   ├── __init__.py
│   ├── base.py              # Abstract base repository
│   ├── user_repository.py
│   ├── song_repository.py
│   ├── history_repository.py
│   ├── feedback_repository.py
│   └── playlist_repository.py
```

### 2.4 AI Pipelines (Existing)

```
backend/
├── src/
│   ├── pipelines/
│   │   ├── text_mood_detector.py   # NLP mood detection
│   │   ├── mood_engine.py          # VA-space recommendation
│   │   ├── curator_engine.py       # Playlist smoothing
│   │   └── song_similarity.py      # Similar song finding
│   ├── ranking/
│   │   └── preference_model.py     # ML personalization
│   └── search/
│       └── tfidf_search.py         # Vietnamese search
```

---

## 3. Database Schema

### 3.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────┐
│     users       │       │       songs         │
├─────────────────┤       ├─────────────────────┤
│ user_id (PK)    │       │ song_id (PK)        │
│ username        │       │ name                │
│ email           │       │ artist              │
│ password_hash   │       │ genre               │
│ created_at      │       │ energy              │
│ favorite_mood   │       │ valence             │
│ favorite_genres │       │ tempo               │
│ avatar_url      │       │ loudness            │
└────────┬────────┘       │ danceability        │
         │                │ acousticness        │
         │                │ mood                │
         │                │ camelot_key         │
         │                └──────────┬──────────┘
         │                           │
         ▼                           ▼
┌─────────────────────────────────────────────────┐
│              listening_history                   │
├─────────────────────────────────────────────────┤
│ history_id (PK)                                 │
│ user_id (FK → users)                            │
│ song_id (FK → songs)                            │
│ mood_at_time                                    │
│ intensity                                       │
│ input_type ('text' | 'chip')                    │
│ input_text (nullable)                           │
│ session_id                                      │
│ listened_at                                     │
│ listened_duration_seconds                       │
│ completed (boolean)                             │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│                  feedback                        │
├─────────────────────────────────────────────────┤
│ feedback_id (PK)                                │
│ user_id (FK → users)                            │
│ song_id (FK → songs)                            │
│ history_id (FK → listening_history)             │
│ feedback_type ('like' | 'dislike' | 'skip')     │
│ created_at                                      │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│              user_preferences                    │
├─────────────────────────────────────────────────┤
│ preference_id (PK)                              │
│ user_id (FK → users)                            │
│ preference_type ('mood' | 'genre' | 'artist')   │
│ preference_value                                │
│ weight (float, learned)                         │
│ updated_at                                      │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│                  playlists                       │
├─────────────────────────────────────────────────┤
│ playlist_id (PK)                                │
│ user_id (FK → users)                            │
│ name                                            │
│ mood                                            │
│ created_at                                      │
│ is_auto_generated (boolean)                     │
└────────────────────────┬────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────┐
│              playlist_songs                      │
├─────────────────────────────────────────────────┤
│ id (PK)                                         │
│ playlist_id (FK → playlists)                    │
│ song_id (FK → songs)                            │
│ position (int, for ordering)                    │
│ added_at                                        │
└─────────────────────────────────────────────────┘
```

### 3.2 SQL Schema

```sql
-- users table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    favorite_mood TEXT,
    favorite_genres TEXT,  -- JSON array
    avatar_url TEXT
);

-- songs table (with audio features)
CREATE TABLE songs (
    song_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    artist TEXT NOT NULL,
    genre TEXT,
    energy REAL DEFAULT 50,
    valence REAL DEFAULT 50,
    tempo REAL DEFAULT 120,
    loudness REAL DEFAULT -10,
    danceability REAL DEFAULT 50,
    acousticness REAL DEFAULT 50,
    mood TEXT,
    camelot_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- listening_history table
CREATE TABLE listening_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    song_id INTEGER NOT NULL,
    mood_at_time TEXT,
    intensity TEXT,
    input_type TEXT CHECK(input_type IN ('text', 'chip')),
    input_text TEXT,
    session_id TEXT,
    listened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    listened_duration_seconds INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (song_id) REFERENCES songs(song_id)
);

-- feedback table
CREATE TABLE feedback (
    feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    song_id INTEGER NOT NULL,
    history_id INTEGER,
    feedback_type TEXT CHECK(feedback_type IN ('like', 'dislike', 'skip')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (song_id) REFERENCES songs(song_id),
    FOREIGN KEY (history_id) REFERENCES listening_history(history_id)
);

-- user_preferences table (learned preferences)
CREATE TABLE user_preferences (
    preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    preference_type TEXT CHECK(preference_type IN ('mood', 'genre', 'artist', 'tempo', 'energy')),
    preference_value TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, preference_type, preference_value)
);

-- playlists table
CREATE TABLE playlists (
    playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    mood TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_auto_generated BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- playlist_songs table
CREATE TABLE playlist_songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id INTEGER NOT NULL,
    song_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
    FOREIGN KEY (song_id) REFERENCES songs(song_id)
);

-- Indexes for performance
CREATE INDEX idx_history_user ON listening_history(user_id);
CREATE INDEX idx_history_time ON listening_history(listened_at);
CREATE INDEX idx_feedback_user ON feedback(user_id);
CREATE INDEX idx_songs_mood ON songs(mood);
CREATE INDEX idx_preferences_user ON user_preferences(user_id);
```

### 3.3 Preference Learning Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PREFERENCE LEARNING DATA FLOW                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  User Feedback         listening_history           user_preferences      │
│  ┌──────────┐         ┌──────────────────┐        ┌──────────────────┐  │
│  │ Like 👍  │────────▶│ song_id, mood,   │───────▶│ mood: happy      │  │
│  │ Dislike👎│         │ genre, features  │        │ weight: 1.5      │  │
│  │ Skip ⏭  │         └──────────────────┘        │ genre: V-Pop     │  │
│  └──────────┘                                     │ weight: 1.2      │  │
│       │                                           └────────┬─────────┘  │
│       │                                                    │            │
│       ▼                                                    ▼            │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              PreferenceModel.update_from_feedback()               │  │
│  │  1. Extract song features (mood, genre, artist, energy, tempo)    │  │
│  │  2. Update weights: like → +0.1, dislike → -0.2, skip → -0.05    │  │
│  │  3. Normalize weights to prevent extreme values                   │  │
│  │  4. Retrain LogisticRegression with new samples (periodic)        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. API Design

### 4.1 Authentication APIs

#### POST /api/auth/register
```json
// Request
{
    "username": "musicfan123",
    "email": "fan@email.com",
    "password": "securePass123"
}

// Response 201
{
    "status": "success",
    "user_id": 1,
    "message": "Đăng ký thành công"
}

// Response 400
{
    "status": "error",
    "detail": "Username đã tồn tại"
}
```

#### POST /api/auth/login
```json
// Request
{
    "email": "fan@email.com",
    "password": "securePass123"
}

// Response 200
{
    "status": "success",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
        "user_id": 1,
        "username": "musicfan123",
        "email": "fan@email.com",
        "favorite_mood": "Vui",
        "favorite_genres": ["V-Pop", "Ballad"]
    }
}

// Response 401
{
    "status": "error",
    "detail": "Email hoặc mật khẩu không đúng"
}
```

### 4.2 Chat APIs

#### POST /api/chat/message
Main endpoint, handles both text and chip input.

```json
// Request - Text Input (NLP mood detection)
{
    "message": "Tôi đang cảm thấy rất buồn và cô đơn",
    "input_type": "text",
    "session_id": "sess_abc123"
}

// Request - Chip Input (Direct mood)
{
    "mood": "Vui",
    "intensity": "Vừa",
    "input_type": "chip",
    "session_id": "sess_abc123"
}

// Response 200
{
    "status": "success",
    "detected_mood": {
        "mood": "Buồn",
        "mood_vi": "Buồn",
        "confidence": 0.87,
        "intensity": "Mạnh",
        "keywords_matched": ["buồn", "cô đơn"]
    },
    "bot_message": "Tôi hiểu bạn đang cảm thấy buồn 😢. Đây là những bài hát có thể đồng cảm cùng bạn:",
    "songs": [
        {
            "song_id": 42,
            "name": "Nơi Này Có Anh",
            "artist": "Sơn Tùng M-TP",
            "genre": "V-Pop",
            "mood": "Buồn",
            "reason": "Giai điệu da diết, phù hợp khi bạn muốn suy ngẫm",
            "match_score": 0.92,
            "audio_features": {
                "energy": 45,
                "valence": 35,
                "tempo": 78
            }
        },
        {
            "song_id": 56,
            "name": "Có Chàng Trai Viết Lên Cây",
            "artist": "Phan Mạnh Quỳnh",
            "genre": "Ballad",
            "mood": "Buồn",
            "reason": "Lời ca sâu lắng, giúp bạn giải tỏa cảm xúc",
            "match_score": 0.88
        }
        // ... more songs
    ],
    "playlist": {
        "id": "auto_gen_12345",
        "total_duration_minutes": 45,
        "transition_quality": "smooth"
    },
    "session_id": "sess_abc123"
}
```

#### POST /api/chat/feedback
```json
// Request
{
    "song_id": 42,
    "feedback_type": "like",  // "like" | "dislike" | "skip"
    "history_id": 123,
    "listened_duration_seconds": 180
}

// Response 200
{
    "status": "success",
    "message": "Đã ghi nhận. Tôi sẽ gợi ý nhiều bài tương tự hơn!",
    "preference_updated": true
}
```

### 4.3 Playlist/Recommendation APIs

#### GET /api/recommendations/history
```json
// Request: GET /api/recommendations/history?limit=20&mood=Vui&from_date=2024-01-01

// Response 200
{
    "status": "success",
    "total": 45,
    "items": [
        {
            "history_id": 123,
            "song": {
                "song_id": 42,
                "name": "Nơi Này Có Anh",
                "artist": "Sơn Tùng M-TP",
                "genre": "V-Pop"
            },
            "mood": "Buồn",
            "intensity": "Vừa",
            "listened_at": "2024-02-20T15:30:00Z",
            "feedback": "like"
        }
        // ... more items
    ],
    "pagination": {
        "limit": 20,
        "offset": 0,
        "has_more": true
    }
}
```

#### GET /api/recommendations/by-mood
```json
// Request: GET /api/recommendations/by-mood?mood=Chill&intensity=Nhẹ&limit=10

// Response 200
{
    "status": "success",
    "mood": "Chill",
    "intensity": "Nhẹ",
    "songs": [
        {
            "song_id": 78,
            "name": "Phía Sau Một Cô Gái",
            "artist": "Soobin Hoàng Sơn",
            "genre": "V-Pop",
            "match_score": 0.95,
            "reason": "Nhịp điệu nhẹ nhàng, hoàn hảo cho Chill"
        }
    ]
}
```

### 4.4 User Profile APIs

#### GET /api/user/profile
```json
// Response 200
{
    "user_id": 1,
    "username": "musicfan123",
    "email": "fan@email.com",
    "created_at": "2024-01-15T10:00:00Z",
    "stats": {
        "total_songs_listened": 156,
        "total_playlists": 5,
        "favorite_mood": "Vui",
        "favorite_genres": ["V-Pop", "Ballad", "R&B"],
        "favorite_artists": ["Sơn Tùng M-TP", "Đen Vâu"]
    },
    "preferences": {
        "mood_weights": {
            "Vui": 1.5,
            "Buồn": 1.2,
            "Chill": 1.0
        },
        "genre_weights": {
            "V-Pop": 1.8,
            "Ballad": 1.3
        }
    }
}
```

#### PUT /api/user/profile
```json
// Request
{
    "favorite_mood": "Chill",
    "favorite_genres": ["V-Pop", "Indie"]
}

// Response 200
{
    "status": "success",
    "message": "Đã cập nhật thông tin"
}
```

---

## 5. Chat Pipeline Flow

### 5.1 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     COMPLETE CHAT PIPELINE FLOW                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  USER INPUT                                                              │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ "Tôi đang cảm thấy buồn và muốn nghe nhạc để thư giãn"        │     │
│  │                         OR                                      │     │
│  │ Chip Selected: [Mood: Chill] [Intensity: Nhẹ]                  │     │
│  └─────────────────────────────┬──────────────────────────────────┘     │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ STEP 1: Input Classification                                     │    │
│  │ ┌─────────────────────────────────────────────────────────────┐ │    │
│  │ │ if input_type == "text":                                    │ │    │
│  │ │     mood_result = TextMoodDetector.detect(text)             │ │    │
│  │ │     → Returns: mood="Buồn", intensity="Vừa", conf=0.85      │ │    │
│  │ │ else:                                                       │ │    │
│  │ │     mood_result = direct_from_chip(mood, intensity)         │ │    │
│  │ └─────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────┬───────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ STEP 2: Candidate Song Selection                                 │    │
│  │ ┌─────────────────────────────────────────────────────────────┐ │    │
│  │ │ MoodEngine.recommend_by_mood(                               │ │    │
│  │ │     mood="Buồn",                                            │ │    │
│  │ │     intensity="Vừa",                                        │ │    │
│  │ │     limit=50  # Get more candidates for re-ranking          │ │    │
│  │ │ )                                                           │ │    │
│  │ │ → Returns: 50 songs sorted by mood match score              │ │    │
│  │ └─────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────┬───────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ STEP 3: Personalization Re-ranking                               │    │
│  │ ┌─────────────────────────────────────────────────────────────┐ │    │
│  │ │ # Load user preferences from DB                             │ │    │
│  │ │ user_prefs = UserPreferenceRepository.get(user_id)          │ │    │
│  │ │                                                             │ │    │
│  │ │ # Apply preference model                                    │ │    │
│  │ │ PreferenceModel.load_user_model(user_id)                    │ │    │
│  │ │ for song in candidates:                                     │ │    │
│  │ │     song.pref_score = PreferenceModel.predict_proba(song)   │ │    │
│  │ │                                                             │ │    │
│  │ │ # Combine scores: 60% mood match + 40% preference           │ │    │
│  │ │ final_score = 0.6 * mood_score + 0.4 * pref_score           │ │    │
│  │ │                                                             │ │    │
│  │ │ # Re-sort and take top 10-15                                │ │    │
│  │ │ personalized = sorted(candidates, by=final_score)[:15]      │ │    │
│  │ └─────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────┬───────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ STEP 4: Playlist Curation                                        │    │
│  │ ┌─────────────────────────────────────────────────────────────┐ │    │
│  │ │ CuratorEngine.curate_playlist(                              │ │    │
│  │ │     songs=personalized,                                     │ │    │
│  │ │     target_mood="Buồn",                                     │ │    │
│  │ │     config=CuratorConfig(                                   │ │    │
│  │ │         w_energy_fit=0.4,      # Match energy curve         │ │    │
│  │ │         w_harmonic_flow=0.3,   # Camelot wheel mixing       │ │    │
│  │ │         w_texture_smooth=0.2,  # Smooth transitions         │ │    │
│  │ │         w_narrative_bonus=0.1  # Build-up potential         │ │    │
│  │ │     )                                                       │ │    │
│  │ │ )                                                           │ │    │
│  │ │ → Returns: Ordered playlist with smooth transitions         │ │    │
│  │ └─────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────┬───────────────────────────────────┘    │
│                                │                                         │
│                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ STEP 5: Save & Respond                                           │    │
│  │ ┌─────────────────────────────────────────────────────────────┐ │    │
│  │ │ # Save to listening_history                                 │ │    │
│  │ │ for song in playlist:                                       │ │    │
│  │ │     HistoryRepository.add(user_id, song_id, mood, ...)      │ │    │
│  │ │                                                             │ │    │
│  │ │ # Generate bot response message                             │ │    │
│  │ │ message = NarrativeGenerator.generate(mood, intensity)      │ │    │
│  │ │                                                             │ │    │
│  │ │ # Build JSON response for frontend                          │ │    │
│  │ │ return ChatResponse(                                        │ │    │
│  │ │     detected_mood, bot_message, songs, playlist_info        │ │    │
│  │ │ )                                                           │ │    │
│  │ └─────────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Sequence Diagram

```
Frontend        ChatController     ChatOrchestrator    Services           Database
    │                 │                   │                │                  │
    │ POST /message   │                   │                │                  │
    │────────────────▶│                   │                │                  │
    │                 │ process_message() │                │                  │
    │                 │──────────────────▶│                │                  │
    │                 │                   │                │                  │
    │                 │                   │ detect_mood()  │                  │
    │                 │                   │───────────────▶│ TextMoodDetector │
    │                 │                   │◀───────────────│                  │
    │                 │                   │                │                  │
    │                 │                   │ get_songs()    │                  │
    │                 │                   │───────────────▶│ MoodEngine       │
    │                 │                   │◀───────────────│                  │
    │                 │                   │                │                  │
    │                 │                   │ get_prefs()    │                  │
    │                 │                   │───────────────▶│─────────────────▶│
    │                 │                   │◀───────────────│◀─────────────────│
    │                 │                   │                │                  │
    │                 │                   │ rerank()       │                  │
    │                 │                   │───────────────▶│ PreferenceModel  │
    │                 │                   │◀───────────────│                  │
    │                 │                   │                │                  │
    │                 │                   │ curate()       │                  │
    │                 │                   │───────────────▶│ CuratorEngine    │
    │                 │                   │◀───────────────│                  │
    │                 │                   │                │                  │
    │                 │                   │ save()         │                  │
    │                 │                   │───────────────▶│─────────────────▶│
    │                 │                   │◀───────────────│◀─────────────────│
    │                 │◀──────────────────│                │                  │
    │◀────────────────│ JSON Response     │                │                  │
    │                 │                   │                │                  │
```

---

## 6. Component Details

### 6.1 ChatOrchestrator Class

**Responsibilities:**
1. Điều phối toàn bộ pipeline từ input → output
2. Quản lý session state
3. Handle errors gracefully với fallback
4. Logging và monitoring

**Key Methods:**
- `process_message(user_id, message, input_type, session_id)` → ChatResponse
- `process_feedback(user_id, song_id, feedback_type)` → FeedbackResponse
- `_detect_mood(text)` → MoodResult
- `_get_candidates(mood, intensity)` → List[Song]
- `_personalize(songs, user_id)` → List[Song]
- `_curate_playlist(songs)` → Playlist

### 6.2 PreferenceModel Integration

**Learning Sources:**
1. **Explicit Feedback**: Like/Dislike → Direct weight update
2. **Implicit Feedback**: Listen duration, Skip → Soft weight adjustment
3. **Historical Patterns**: Mood frequency, Time-of-day preferences

**Update Strategy:**
```python
# On feedback received
def update_preferences(user_id: int, song: Song, feedback_type: str):
    # Determine weight delta
    delta = {
        "like": +0.1,
        "dislike": -0.2,
        "skip": -0.05,
        "complete": +0.05
    }[feedback_type]
    
    # Update multiple preference dimensions
    update_mood_weight(user_id, song.mood, delta)
    update_genre_weight(user_id, song.genre, delta)
    update_artist_weight(user_id, song.artist, delta * 0.5)
    
    # Periodic model retraining (batch, not real-time)
    if should_retrain(user_id):
        retrain_user_model(user_id)
```

### 6.3 Error Handling Strategy

```python
class ChatOrchestrator:
    async def process_message(self, ...):
        try:
            # Main pipeline
            mood = await self._detect_mood(message)
            songs = await self._get_candidates(mood)
            personalized = await self._personalize(songs, user_id)
            playlist = await self._curate_playlist(personalized)
            return ChatResponse(success=True, songs=playlist)
        
        except MoodDetectionError:
            # Fallback: Ask user to select mood manually
            return ChatResponse(
                success=True,
                require_mood_selection=True,
                message="Tôi chưa hiểu rõ tâm trạng của bạn. Bạn có thể chọn mood bên dưới?"
            )
        
        except NoSongsFoundError:
            # Fallback: Return popular songs
            popular = await self.song_repo.get_popular(limit=10)
            return ChatResponse(
                success=True,
                songs=popular,
                message="Không tìm thấy bài phù hợp. Đây là một số bài phổ biến:"
            )
        
        except Exception as e:
            logger.error(f"Chat pipeline error: {e}")
            return ChatResponse(
                success=False,
                error="Có lỗi xảy ra. Vui lòng thử lại sau."
            )
```

---

## Appendix: Folder Structure

```
MMB_FRONTBACK/
├── backend/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry
│   ├── requirements.txt
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py          # JWT, rate limiting
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py              # Authentication routes
│   │       ├── chat.py              # Chat routes
│   │       ├── playlist.py          # Playlist routes
│   │       ├── user.py              # User profile routes
│   │       └── search.py            # Search routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── chat_orchestrator.py     # ⭐ Main orchestrator
│   │   ├── recommendation_service.py
│   │   ├── playlist_service.py
│   │   └── feedback_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user_repository.py
│   │   ├── song_repository.py
│   │   ├── history_repository.py
│   │   ├── feedback_repository.py
│   │   └── playlist_repository.py
│   └── src/
│       ├── pipelines/               # AI/ML modules
│       │   ├── text_mood_detector.py
│       │   ├── mood_engine.py
│       │   ├── curator_engine.py
│       │   └── song_similarity.py
│       ├── ranking/
│       │   └── preference_model.py
│       ├── search/
│       │   └── tfidf_search.py
│       └── database/
│           ├── database.py
│           └── migrations/
├── frontend/
│   ├── main.py
│   └── src/
│       ├── screens/
│       ├── services/
│       ├── components/
│       └── utils/
├── shared/
│   ├── constants.py
│   └── types.py
└── docs/
    ├── API.md
    ├── ARCHITECTURE.md
    └── SYSTEM_ARCHITECTURE.md
```

---

*Document Version: 1.0.0*
*Last Updated: 2026-02-24*
