# MusicMoodBot - AI Music Recommendation Chatbot

<div align="center">

![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)
![Flet](https://img.shields.io/badge/Flet-0.25-purple.svg)

**AI-powered music recommendation chatbot that understands your mood and suggests perfect songs**

</div>

---

## 📋 Mục Lục

- [Tổng Quan](#-tổng-quan)
- [Kiến Trúc Hệ Thống](#-kiến-trúc-hệ-thống)
- [Backend](#-backend)
  - [API Endpoints](#api-endpoints)
  - [AI Pipelines](#ai-pipelines-thuật-toán)
  - [Repositories](#repositories)
  - [Database](#database)
- [Frontend](#-frontend)
  - [Screens](#screens)
  - [Services](#services)
  - [Components](#components)
- [Cài Đặt](#-cài-đặt)
- [Chạy Ứng Dụng](#-chạy-ứng-dụng)

---

## 🎯 Tổng Quan

MusicMoodBot là chatbot gợi ý nhạc thông minh sử dụng AI để:
- **Phát hiện tâm trạng** từ văn bản tiếng Việt/Anh (NLP)
- **Phân tích đặc trưng âm nhạc** (MIR - Music Information Retrieval)
- **Cá nhân hóa** gợi ý dựa trên lịch sử nghe
- **Tạo playlist mượt mà** với kỹ thuật DJ mixing

### Luồng Hoạt Động

```
User Input → Text Mood Detection → Candidate Selection → Personalization → Playlist Curation → Response
    ↓               ↓                      ↓                   ↓                    ↓
"nhạc buồn"   → "sad" mood 0.8    →  50 songs mood=sad   → Re-rank by    →  Top 10 songs
                                                            preference       curated order
```

---

## 🏗 Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Flet)                           │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Chat   │  │  Login   │  │ Signup  │  │ History  │  │ Profile │ │
│  │ Screen  │  │  Screen  │  │ Screen  │  │  Screen  │  │ Screen  │ │
│  └────┬────┘  └────┬─────┘  └────┬────┘  └────┬─────┘  └────┬────┘ │
│       │            │             │            │              │       │
│  ┌────┴────────────┴─────────────┴────────────┴──────────────┴────┐ │
│  │                      Services Layer                             │ │
│  │  chat_service.py  │  auth_service.py  │  history_service.py    │ │
│  └───────────────────────────────┬────────────────────────────────┘ │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │ HTTP REST API
┌──────────────────────────────────┼──────────────────────────────────┐
│                           BACKEND (FastAPI)                         │
│  ┌───────────────────────────────┴───────────────────────────────┐ │
│  │                         API Layer (v1)                         │ │
│  │  /auth/*  │  /chat/*  │  /user/*  │  /playlist/*              │ │
│  └───────────────────────────────┬───────────────────────────────┘ │
│  ┌───────────────────────────────┴───────────────────────────────┐ │
│  │                      Chat Orchestrator                         │ │
│  │  Coordinates all AI pipelines into unified response            │ │
│  └───────────────────────────────┬───────────────────────────────┘ │
│  ┌──────────┬──────────┬─────────┴────┬───────────┬─────────────┐ │
│  │TextMood  │MoodEngine│ Preference   │ Curator   │ TF-IDF      │ │
│  │Detector  │(VA Space)│ Model (ML)   │ Engine    │ Search      │ │
│  └────┬─────┴────┬─────┴──────┬───────┴─────┬─────┴──────┬──────┘ │
│  ┌────┴──────────┴────────────┴─────────────┴────────────┴──────┐ │
│  │                      Repository Layer                         │ │
│  │  Song │ User │ History │ Feedback │ Preferences │ Playlist   │ │
│  └───────────────────────────────┬──────────────────────────────┘ │
│  ┌───────────────────────────────┴──────────────────────────────┐ │
│  │                     SQLite Database                           │ │
│  │  songs │ users │ listening_history │ feedback │ playlists    │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend

### Cấu Trúc Thư Mục

```
backend/
├── main.py                    # FastAPI entry point
├── api/
│   └── v1/
│       ├── auth.py            # Authentication endpoints
│       ├── chat.py            # Chat & recommendation endpoints
│       ├── user.py            # User profile endpoints
│       ├── playlist.py        # Playlist management
│       └── dependencies.py    # Shared dependencies
├── services/
│   └── chat_orchestrator.py   # Main pipeline orchestrator
├── repositories/
│   ├── base.py                # Base repository class
│   ├── song_repository.py     # Song data access
│   ├── user_repository.py     # User data access
│   ├── history_repository.py  # Listening history
│   ├── feedback_repository.py # Like/dislike feedback
│   ├── preferences_repository.py # User preferences
│   └── playlist_repository.py # Playlist management
└── src/
    ├── pipelines/             # AI algorithms
    │   ├── text_mood_detector.py
    │   ├── mood_engine.py
    │   ├── curator_engine.py
    │   ├── curator_types.py
    │   └── mood_transition.py
    ├── ranking/
    │   └── preference_model.py
    ├── search/
    │   └── tfidf_search.py
    └── database/
        ├── database.py
        └── music.db
```

---

### API Endpoints

#### 🔐 Authentication (`/api/v1/auth/`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/register` | Đăng ký tài khoản mới |
| POST | `/login` | Đăng nhập, trả về JWT tokens |
| POST | `/refresh` | Làm mới access token |
| GET | `/me` | Lấy thông tin user hiện tại |

**Request Login:**
```json
{
    "email": "user@email.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "status": "success",
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
        "user_id": 1,
        "username": "user123",
        "email": "user@email.com"
    }
}
```

---

#### 💬 Chat (`/api/v1/chat/`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/message` | Gửi tin nhắn text, nhận gợi ý nhạc |
| POST | `/mood` | Chọn mood chip, nhận gợi ý nhạc |
| POST | `/feedback` | Gửi feedback (like/dislike/skip) |
| GET | `/moods` | Lấy danh sách moods hỗ trợ |

**Request Message (NLP):**
```json
{
    "message": "Tôi đang cảm thấy buồn và cô đơn",
    "limit": 10
}
```

**Request Mood (Chip):**
```json
{
    "mood": "Buồn",
    "intensity": "Vừa",
    "limit": 10
}
```

**Response:**
```json
{
    "status": "success",
    "detected_mood": {
        "mood": "sad",
        "mood_vi": "Buồn",
        "confidence": 0.85,
        "intensity": "Vừa",
        "keywords_matched": ["buồn", "cô đơn"]
    },
    "bot_message": "Mình hiểu rồi 💙 Đây là những bài hát phù hợp cho bạn:",
    "songs": [
        {
            "song_id": 42,
            "name": "Có Chàng Trai Viết Lên Cây",
            "artist": "Phan Mạnh Quỳnh",
            "genre": "Pop",
            "mood": "sad",
            "reason": "Với giai điệu sâu lắng, phù hợp mood buồn",
            "match_score": 89.5,
            "audio_features": {
                "energy": 35.0,
                "valence": 28.0,
                "tempo": 78.0
            }
        }
    ],
    "playlist_id": 123,
    "session_id": "abc-123-def"
}
```

---

#### 👤 User (`/api/v1/user/`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/profile` | Lấy profile user |
| PUT | `/profile` | Cập nhật profile |
| GET | `/history` | Lấy lịch sử nghe |
| GET | `/preferences` | Lấy preferences đã học |

---

#### 🎵 Playlist (`/api/v1/playlist/`)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Lấy danh sách playlists |
| POST | `/` | Tạo playlist mới |
| GET | `/{id}` | Lấy chi tiết playlist |
| PUT | `/{id}` | Cập nhật playlist |
| DELETE | `/{id}` | Xóa playlist |
| POST | `/{id}/songs` | Thêm bài vào playlist |

---

### AI Pipelines (Thuật Toán)

#### 1️⃣ TextMoodDetector (`text_mood_detector.py`)

**Chức năng:** Phát hiện tâm trạng từ văn bản tiếng Việt/Anh

**Thuật toán:**
```
Input: "Tôi đang buồn quá, không muốn làm gì cả"

1. Greeting Detection
   - Check xem có phải lời chào không (chào, hello, xin chào...)
   - Nếu là lời chào → require_mood_selection = True

2. Keyword Matching
   - Scan qua MOOD_KEYWORDS_VI dictionary
   - Mỗi mood có 3 level: high (1.0), medium (0.7), low (0.4)
   
   MOOD_KEYWORDS_VI = {
       "Buồn": {
           "high": ["tuyệt vọng", "đau khổ", "tan nát"],      # confidence = 1.0
           "medium": ["buồn", "grustny", "cô đơn"],           # confidence = 0.7
           "low": ["không vui", "chán", "mệt"]                # confidence = 0.4
       },
       "Vui": { ... },
       ...
   }

3. Intensity Detection
   - Check INTENSITY_KEYWORDS:
     "Mạnh": ["cực kỳ", "vô cùng", "quá", "lắm"]
     "Nhẹ": ["hơi", "một chút", "chút"]
     "Vừa": default

4. Output: MoodScore(mood="Buồn", confidence=0.7, intensity="Mạnh", keywords=["buồn", "quá"])
```

**Hỗ trợ:**
- 6 moods: Vui, Buồn, Suy tư, Chill, Năng lượng, Tập trung
- Tiếng Việt có dấu & không dấu
- Tiếng Anh

---

#### 2️⃣ MoodEngine (`mood_engine.py`)

**Chức năng:** Phân tích audio features → Dự đoán mood của bài hát

**Thuật toán: VA Space (Valence-Arousal)**
```
Mỗi bài hát có đặc trưng audio:
- energy (0-100): Năng lượng
- valence (0-100): Độ tích cực
- tempo (BPM): Nhịp độ
- loudness (-60 to 0 dB)
- mode (0/1): Minor/Major key
- camelot_key: Harmonic key

                    HIGH AROUSAL
                         ↑
                    Energetic
          Angry    /        \    Happy
                  /          \
    LOW VALENCE ←----- ● -----→ HIGH VALENCE
                  \          /
          Sad      \        /    Peaceful
                    Stress
                         ↓
                    LOW AROUSAL

Công thức tính:
1. Base Valence = energy * 0.3 + happiness * 0.4 + mode_boost
2. Base Arousal = energy * 0.5 + tempo_factor * 0.3
3. Harmonic Bias = CAMELOT_VALENCE_BIAS[key] (+/- 8 points)
4. Final Position → Map to nearest mood prototype

Mood Prototypes:
- happy:     (valence=75, arousal=65)
- sad:       (valence=25, arousal=30)
- energetic: (valence=60, arousal=85)
- stress:    (valence=35, arousal=70)
- peaceful:  (valence=65, arousal=25)
```

---

#### 3️⃣ PreferenceModel (`preference_model.py`)

**Chức năng:** Học sở thích user từ feedback, re-rank gợi ý

**Thuật toán: Logistic Regression**
```
Training Data:
- Like = 1, Dislike = 0
- Features: [energy, valence, tempo, loudness, danceability, acousticness, genre_encoded]

Model:
P(like|song) = sigmoid(w₀ + w₁*energy + w₂*valence + ... + wₙ*genre)

Training Flow:
1. User likes song A (energetic pop)     → label = 1
2. User dislikes song B (slow ballad)    → label = 0
3. Model learns: high energy + pop → higher probability

Re-ranking:
Original scores: [0.9, 0.85, 0.8, 0.75]
Preference boost: × (0.5 + P(like))
Final scores:     [0.9×1.3, 0.85×0.7, 0.8×1.2, 0.75×0.9]
                  = [1.17, 0.595, 0.96, 0.675]
```

---

#### 4️⃣ CuratorEngine (`curator_engine.py`)

**Chức năng:** Tạo playlist mượt mà như DJ mixing

**Thuật toán: Weighted Graph Pathfinding**
```
Mỗi bài hát là 1 node trong graph:
- Energy (0-100)
- Texture (acoustic/electronic/vocal/instrumental)
- Camelot Key (1A-12B)

Edge Score giữa 2 bài = f(energy_diff, key_compat, texture_smooth)

Scoring Weights:
- Energy Fit:      40%  (±15 tolerance)
- Harmonic Flow:   30%  (Camelot wheel: +1, -1, +7 = harmonic)
- Texture Smooth:  20%  (acoustic→vocal OK, but not acoustic→electronic)
- Narrative Bonus: 10%  (build-up potential)

Camelot Wheel Compatibility:
     12B -- 1B
    /         \
  11B         2B
   |           |
  10B         3B
   |    ●     |
   9B         4B
   |           |
   8B         5B
    \         /
     7B -- 6B

Compatible transitions: same key, ±1, opposite (±7)

Energy Curve:
Target: [50, 55, 60, 70, 80, 75, 65, 55]  # Build up → Peak → Cool down
Actual: Pick songs that match target[i] ± tolerance

Breather Logic:
- If 3 consecutive high-energy songs → insert breather
- Breather = song with energy -20 from average
```

---

#### 5️⃣ TF-IDF Search (`tfidf_search.py`)

**Chức năng:** Tìm kiếm bài hát theo text query

**Thuật toán:**
```
1. Vietnamese Normalization:
   "Đừng Làm Trái Tim Anh Đau" → "dung lam trai tim anh dau"

2. TF-IDF Vectorization:
   Document = song_name + artist + genre + mood
   Query = user's search text
   
   TF-IDF(term, doc) = TF(term, doc) × log(N / DF(term))

3. Cosine Similarity:
   score = cos(query_vector, doc_vector)

4. Query Intent Detection:
   - "nhạc của Sơn Tùng" → ARTIST intent → boost artist matches
   - "nhạc buồn" → MOOD intent → boost mood matches
   - "Hãy Trao Cho Anh" → TITLE intent → exact match priority

5. Fuzzy Matching (Typo tolerance):
   "son tung" matches "Sơn Tùng MTP" (similarity > 0.8)
```

---

#### 6️⃣ ChatOrchestrator (`chat_orchestrator.py`)

**Chức năng:** Điều phối toàn bộ pipeline AI

**Pipeline Flow:**
```python
def process_text_message(user_id, message, limit=10):
    # 1. NLP Mood Detection
    mood_result = text_mood_detector.detect_mood(message)
    
    # 2. Get Candidate Songs (by detected mood)
    candidates = song_repository.get_by_mood(mood_result.mood, limit=50)
    
    # 3. Personalization (re-rank by user preference)
    if user_has_feedback(user_id):
        preference_model.train(user_id)
        candidates = preference_model.rerank(candidates)
    
    # 4. Playlist Curation (smooth transitions)
    curated = curator_engine.curate(candidates[:limit])
    
    # 5. Generate Bot Response
    bot_message = generate_response(mood_result)
    
    # 6. Save to History
    history_repository.save(user_id, curated, session_id)
    
    return {
        "detected_mood": mood_result,
        "songs": curated,
        "bot_message": bot_message
    }
```

---

### Repositories

| Repository | Chức năng |
|------------|-----------|
| `SongRepository` | CRUD songs, get by mood/genre/artist |
| `UserRepository` | User data, authentication |
| `HistoryRepository` | Listening history, session tracking |
| `FeedbackRepository` | Like/dislike/skip feedback |
| `PreferencesRepository` | Learned preference weights |
| `PlaylistRepository` | Playlist CRUD, auto-generated playlists |

---

### Database

**Tables:**
```sql
-- Songs table with audio features
CREATE TABLE songs (
    song_id INTEGER PRIMARY KEY,
    song_name TEXT NOT NULL,
    artist TEXT NOT NULL,
    genre TEXT,
    mood TEXT,
    intensity TEXT,
    energy REAL,
    valence REAL,
    tempo REAL,
    loudness REAL,
    danceability REAL,
    acousticness REAL,
    camelot_key TEXT
);

-- Users
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT,
    favorite_mood TEXT,
    favorite_artist TEXT
);

-- Listening history
CREATE TABLE listening_history (
    history_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    song_id INTEGER,
    mood_at_time TEXT,
    intensity TEXT,
    input_type TEXT,          -- 'text' or 'chip'
    input_text TEXT,          -- Original user message
    session_id TEXT,
    listened_at TIMESTAMP,
    listened_duration_seconds INTEGER
);

-- Feedback for preference learning
CREATE TABLE feedback (
    feedback_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    song_id INTEGER,
    feedback_type TEXT,       -- 'like', 'dislike', 'skip'
    created_at TIMESTAMP
);

-- Learned preferences
CREATE TABLE user_preferences (
    preference_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    preference_type TEXT,     -- 'mood', 'genre', 'artist', 'tempo', 'energy'
    preference_value TEXT,
    weight REAL,
    interaction_count INTEGER
);

-- Playlists
CREATE TABLE playlists (
    playlist_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    name TEXT,
    mood TEXT,
    is_auto_generated BOOLEAN,
    song_count INTEGER
);

-- Playlist songs
CREATE TABLE playlist_songs (
    id INTEGER PRIMARY KEY,
    playlist_id INTEGER,
    song_id INTEGER,
    position INTEGER
);
```

---

## 🖥 Frontend

### Cấu Trúc Thư Mục

```
frontend/
├── main.py                    # Flet entry point
├── src/
│   ├── screens/               # UI screens
│   │   ├── login_screen.py    # Đăng nhập
│   │   ├── signup_screen.py   # Đăng ký
│   │   ├── chat_screen.py     # Chat chính
│   │   ├── history_screen.py  # Lịch sử nghe
│   │   └── profile_screen.py  # Hồ sơ user
│   ├── services/              # API clients
│   │   ├── auth_service.py    # Authentication
│   │   ├── chat_service.py    # Chat & recommendations
│   │   └── history_service.py # History loading
│   ├── components/            # UI components
│   │   ├── ui_components.py   # Common UI elements
│   │   ├── animated_mascot.py # Mascot animation
│   │   └── talking_animator.py
│   ├── config/
│   │   ├── constants.py       # App constants
│   │   ├── theme.py           # Color theme
│   │   └── theme_professional.py
│   └── utils/
│       └── state_manager.py   # Global state management
└── assets/
    └── mascots/               # Mascot images
```

---

### Screens

#### 1️⃣ ChatScreen (`chat_screen.py`)

**Chức năng:** Màn hình chat chính

**UI Components:**
```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────┐                                               │
│  │ Sidebar │    ┌─────────────────────────────────────┐   │
│  │         │    │  📱 Chat Messages Area              │   │
│  │ 💬 Chat │    │                                     │   │
│  │ 📜 Hist │    │  🤖 Bot: Chào bạn! Hôm nay thế nào? │   │
│  │👤 Prof │    │                                     │   │
│  │         │    │  👤 You: Tôi muốn nghe nhạc buồn    │   │
│  │         │    │                                     │   │
│  │         │    │  🤖 Bot: Đây là gợi ý cho bạn:      │   │
│  │         │    │  ┌─────────────────────────────┐    │   │
│  │         │    │  │ 🎵 Có Chàng Trai Viết...   │    │   │
│  │         │    │  │    Phan Mạnh Quỳnh         │    │   │
│  │         │    │  │    [▶] [🔄] [❤️] [👎]       │    │   │
│  │         │    │  └─────────────────────────────┘    │   │
│  │         │    │                                     │   │
│  └─────────┘    └─────────────────────────────────────┘   │
│                 ┌─────────────────────────────────────┐   │
│  Mood Chips:    │ 😊Vui │ 😢Buồn │ ⚡Năng động │ ... │   │
│                 └─────────────────────────────────────┘   │
│                 ┌──────────────────────────┐ ┌─────────┐  │
│                 │ Nhập tin nhắn...         │ │  Gửi    │  │
│                 └──────────────────────────┘ └─────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Flow:**
1. User nhập text → Gọi `chat_service.smart_recommend(text)`
2. API trả về songs → Hiển thị song cards
3. User click mood chip → Gọi `chat_service.get_mood_recommendations(mood, intensity)`
4. User click ❤️/👎 → Gọi `chat_service.submit_feedback(song_id, type)`

---

#### 2️⃣ LoginScreen (`login_screen.py`)

**Chức năng:** Đăng nhập

**Flow:**
```
1. Input email/password
2. Click "Đăng nhập"
3. auth_service.login(email, password)
   → POST /api/v1/auth/login
   → Store JWT tokens
   → Navigate to ChatScreen
```

---

#### 3️⃣ SignupScreen (`signup_screen.py`)

**Chức năng:** Đăng ký tài khoản

**Flow:**
```
1. Input: username, email, password, confirm_password
2. Validate:
   - Email format
   - Password >= 6 chars
   - Password match
3. auth_service.signup(...)
   → POST /api/v1/auth/register
   → Auto login
```

---

#### 4️⃣ HistoryScreen (`history_screen.py`)

**Chức năng:** Hiển thị lịch sử nghe nhạc

**Features:**
- Danh sách bài đã nghe
- Grouped by session/date
- Replay/Add to playlist buttons

---

#### 5️⃣ ProfileScreen (`profile_screen.py`)

**Chức năng:** Quản lý hồ sơ người dùng

**Features:**
- Thông tin cá nhân
- Favorite mood/artist
- Logout button

---

### Services

#### ChatService (`chat_service.py`)

```python
class ChatService:
    API_V1_URL = "http://localhost:8000/api/v1"
    
    def smart_recommend(text: str, limit: int = 5) -> dict:
        """
        Gửi text → API phát hiện mood và trả về gợi ý
        POST /api/v1/chat/message
        """
        
    def get_mood_recommendations(mood: str, intensity: str) -> dict:
        """
        Gửi mood chip → API trả về gợi ý
        POST /api/v1/chat/mood
        """
        
    def submit_feedback(song_id: int, feedback_type: str) -> bool:
        """
        Gửi feedback để cải thiện preference model
        POST /api/v1/chat/feedback
        """
```

---

#### AuthService (`auth_service.py`)

```python
class AuthService:
    _access_token: str = None
    _refresh_token: str = None
    
    def login(email: str, password: str) -> Tuple[bool, str]:
        """POST /api/v1/auth/login"""
        
    def signup(name, email, password, confirm) -> Tuple[bool, str]:
        """POST /api/v1/auth/register"""
        
    def refresh_token() -> bool:
        """POST /api/v1/auth/refresh"""
        
    def logout() -> Tuple[bool, str]:
        """Clear tokens, reset state"""
        
    def get_access_token() -> str:
        """Get current access token for API calls"""
```

---

#### HistoryService (`history_service.py`)

```python
class HistoryService:
    def get_listening_history(limit: int = 50) -> List[dict]:
        """
        GET /api/v1/user/history
        Returns list of past listening sessions
        """
```

---

### Components

| Component | Mô tả |
|-----------|-------|
| `create_bot_message()` | Bubble chat từ bot (bên trái) |
| `create_user_message()` | Bubble chat từ user (bên phải) |
| `create_song_card()` | Card hiển thị bài hát với nút play/like |
| `create_mood_chip()` | Chip chọn mood (Vui, Buồn, ...) |
| `create_intensity_chip()` | Chip chọn intensity (Nhẹ, Vừa, Mạnh) |
| `animated_mascot` | Mascot animation based on mood |

---

## 📦 Cài Đặt

### Requirements

- Python 3.10+
- pip

### Steps

```bash
# 1. Clone repository
git clone <repo-url>
cd MMB_FRONTBACK

# 2. Create virtual environment
python -m venv .venv

# 3. Activate (Windows)
.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Initialize database (nếu cần)
cd backend/src/database
python init_db.py
python migrate_v2.py
```

### Dependencies chính

```
# Backend
fastapi==0.115.*
uvicorn==0.32.*
pydantic==2.*
pyjwt==2.*
scikit-learn==1.5.*
numpy==2.*
scipy==1.14.*

# Frontend
flet==0.25.*
requests==2.*
```

---

## 🚀 Chạy Ứng Dụng

### Cách 1: Chạy riêng Backend & Frontend

```bash
# Terminal 1: Backend
cd MMB_FRONTBACK
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd MMB_FRONTBACK/frontend
python main.py
```

### Cách 2: Chạy cùng lúc

```bash
python run_app.py
```

### Endpoints khi chạy

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/api/docs |
| API Docs (ReDoc) | http://localhost:8000/api/redoc |
| Frontend | Desktop app (Flet) |

---

## 📊 Ví Dụ Sử Dụng

### 1. Chat với Bot (Text Input)

```
User: "tôi đang buồn quá ạ"
Bot:  Mình hiểu rồi 💙 Đây là những bài hát phù hợp cho bạn:
      1. 🎵 Có Chàng Trai Viết Lên Cây - Phan Mạnh Quỳnh
      2. 🎵 Chúng Ta Không Thuộc Về Nhau - Sơn Tùng MTP
      3. 🎵 Buông Đôi Tay Nhau Ra - Sơn Tùng MTP
```

### 2. Chọn Mood Chip

```
User: Click [😢 Buồn] → [✨ Vừa]
Bot:  Hãy để âm nhạc an ủi bạn nhé 🎵
      1. 🎵 Nơi Này Có Anh
      2. 🎵 Em Của Ngày Hôm Qua
      ...
```

### 3. Feedback

```
User: Click [❤️] on "Có Chàng Trai Viết Lên Cây"
→ Preference model learns: user likes slow ballads
→ Future recommendations boost similar songs
```

### 4. Search (Upcoming)

```
User: "nhạc của Sơn Tùng"
→ TF-IDF search detects ARTIST intent
→ Returns all songs by "Sơn Tùng MTP"
```

---

## 🔍 API Testing với cURL

### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"123456"}'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'
```

### Get Recommendations
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message":"tôi muốn nghe nhạc vui","limit":5}'
```

---

## 📝 License

MIT License

---

## 👥 Authors

MusicMoodBot Team - 2025
