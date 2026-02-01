# System Architecture

> MusicMoodBot Architecture Documentation v1.0

## Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Backend Architecture](#2-backend-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Database Schema](#4-database-schema)
5. [ML/NLP Pipelines](#5-mlnlp-pipelines)
6. [Security Architecture](#6-security-architecture)
7. [Sequence Diagrams](#7-sequence-diagrams)

---

## 1. Tổng quan kiến trúc

### 1.1 System Overview

```
                                    MusicMoodBot System
    ┌──────────────────────────────────────────────────────────────────────┐
    │                                                                       │
    │  ┌─────────────────┐              ┌─────────────────┐                │
    │  │   Flet Desktop  │   HTTP/REST  │   FastAPI       │                │
    │  │   Application   │◄────────────►│   Server        │                │
    │  │   (Frontend)    │              │   (Backend)     │                │
    │  └─────────────────┘              └────────┬────────┘                │
    │                                            │                         │
    │                                            ▼                         │
    │                              ┌─────────────────────────┐             │
    │                              │    Service Layer        │             │
    │                              │  ┌─────┬─────┬─────┐   │             │
    │                              │  │Mood │Curatе│Text │   │             │
    │                              │  │Eng. │Eng.  │Det. │   │             │
    │                              │  └─────┴─────┴─────┘   │             │
    │                              └───────────┬─────────────┘             │
    │                                          │                           │
    │                                          ▼                           │
    │                              ┌─────────────────────────┐             │
    │                              │      SQLite (WAL)       │             │
    │                              │  ┌─────┬─────┬─────┐   │             │
    │                              │  │songs│users│hist │   │             │
    │                              │  └─────┴─────┴─────┘   │             │
    │                              └─────────────────────────┘             │
    │                                                                       │
    └──────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Separation of Concerns** | 4-layer architecture (UI, API, Service, Data) |
| **Single Responsibility** | Mỗi module có 1 nhiệm vụ duy nhất |
| **Repository Pattern** | Data access abstracted |
| **Dependency Injection** | Services được inject, dễ test |

### 1.3 Technology Stack

```
┌─────────────────────────────────────────────────────────────┐
│                       PRESENTATION                          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Flet 0.80.2 │ Material Design │ Responsive Layout    │ │
│  └───────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                          API                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  FastAPI 0.115 │ Pydantic │ JWT Auth │ OpenAPI Docs   │ │
│  └───────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                        BUSINESS                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  MoodEngine │ CuratorEngine │ TextMoodDetector │ TF-IDF│ │
│  └───────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                          DATA                               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  SQLite 3 (WAL) │ Repository Pattern │ Connection Pool │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Backend Architecture

### 2.1 Directory Structure

```
backend/
├── main.py                    # Application entry point
├── core/                      # Core engine exports
│   └── __init__.py           # Re-exports ML engines
├── repositories/              # Data Access Layer
│   ├── base.py               # Base repository (generic CRUD)
│   ├── song_repository.py    # Song data access
│   ├── user_repository.py    # User data access
│   └── history_repository.py # History data access
└── src/
    ├── api/                   # API Layer
    │   ├── mood_api.py       # Main router
    │   └── routes/           # Modular routes
    │       ├── health.py     # Health check endpoints
    │       ├── moods.py      # Mood endpoints
    │       ├── songs.py      # Song endpoints
    │       ├── search.py     # Search endpoints
    │       └── recommendations.py
    ├── pipelines/             # ML/NLP Algorithms
    │   ├── mood_engine.py    # MoodEngine v5.2
    │   ├── curator_engine.py # CuratorEngine v2.0
    │   └── text_mood_detector.py
    ├── services/              # Business Logic
    │   ├── mood_services.py
    │   └── playlist_service.py
    └── database/              # Database Layer
        ├── database.py       # Connection management
        └── music.db          # SQLite database
```

### 2.2 Layer Responsibilities

| Layer | Responsibility | Example |
|-------|----------------|---------|
| **API Routes** | HTTP handling, validation | `POST /api/moods/detect` |
| **Services** | Business logic orchestration | `MoodService.get_songs()` |
| **Pipelines** | ML/NLP algorithms | `MoodEngine.analyze()` |
| **Repositories** | Data persistence | `SongRepository.find_by_mood()` |

### 2.3 Request Flow

```
HTTP Request
     │
     ▼
┌─────────────┐
│   FastAPI   │  1. Validate request
│   Router    │  2. Parse parameters
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Service   │  3. Business logic
│   Layer     │  4. Coordinate components
└──────┬──────┘
       │
       ├─────────────────┐
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│   Pipeline  │   │  Repository │
│   (ML/NLP)  │   │  (Data)     │
└─────────────┘   └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   SQLite    │
                  │   Database  │
                  └─────────────┘
```

### 2.4 Repository Pattern

```python
# Base Repository (Abstract)
class BaseRepository(Generic[T]):
    def find_by_id(self, id: int) -> Optional[T]
    def find_all(self, limit: int) -> List[T]
    def create(self, entity: T) -> T
    def update(self, entity: T) -> T
    def delete(self, id: int) -> bool

# Concrete Implementation
class SongRepository(BaseRepository[Song]):
    def find_by_mood(self, mood: str, intensity: str) -> List[Song]
    def search(self, query: str) -> List[Song]
```

---

## 3. Frontend Architecture

### 3.1 Directory Structure

```
frontend/
├── main.py                    # Application entry
├── state/                     # State Management
│   └── app_state.py          # Centralized state (Singleton)
├── infrastructure/            # Infrastructure Layer
│   ├── api_client.py         # HTTP client
│   └── token_storage.py      # JWT storage
└── src/
    ├── screens/               # Screen Components
    │   ├── login_screen.py
    │   ├── chat_screen.py
    │   └── history_screen.py
    ├── components/            # Reusable Components
    │   ├── song_card.py
    │   └── message_bubble.py
    └── services/              # Frontend Services
        └── auth_service.py
```

### 3.2 State Management

```python
# Singleton Pattern
@dataclass
class AppState:
    # User state
    user_id: Optional[int] = None
    username: Optional[str] = None
    jwt_token: Optional[str] = None
    
    # Chat state
    messages: List[Message] = field(default_factory=list)
    current_mood: Optional[str] = None
    
    # Navigation state
    current_screen: str = "login"
    is_loading: bool = False

# Usage
state = AppState.get_instance()
state.user_id = 1
```

### 3.3 API Client

```python
class APIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.timeout = 30
        
    async def get(self, endpoint: str, headers: dict = None) -> dict
    async def post(self, endpoint: str, data: dict = None) -> dict
    
    # Automatic token injection
    def _get_headers(self) -> dict:
        token = TokenStorage.get_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
```

### 3.4 Screen Navigation

```
┌─────────────────────────────────────────────────────┐
│                    App Shell                         │
│  ┌────────────────────────────────────────────┐     │
│  │              Navigation Bar                 │     │
│  │  [Chat] [History] [Profile] [Settings]     │     │
│  └────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────┐     │
│  │                                             │     │
│  │              Screen Content                 │     │
│  │                                             │     │
│  │  ┌────────────────────────────────────┐    │     │
│  │  │  LoginScreen / ChatScreen /        │    │     │
│  │  │  HistoryScreen / ProfileScreen     │    │     │
│  │  └────────────────────────────────────┘    │     │
│  │                                             │     │
│  └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### 4.1 Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────┐
│      users       │       │      songs       │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │
│ username         │       │ title            │
│ password_hash    │       │ artist           │
│ created_at       │       │ mood             │
│ updated_at       │       │ intensity        │
└────────┬─────────┘       │ valence          │
         │                 │ energy           │
         │                 │ key              │
         │                 │ camelot          │
         │                 │ spotify_id       │
         │                 └────────┬─────────┘
         │                          │
         │    ┌─────────────────────┘
         │    │
         ▼    ▼
┌──────────────────┐
│     history      │
├──────────────────┤
│ id (PK)          │
│ user_id (FK)     │
│ song_id (FK)     │
│ action           │
│ duration_played  │
│ played_at        │
└──────────────────┘
```

### 4.2 Table Definitions

#### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | UNIQUE NOT NULL |
| password_hash | TEXT | NOT NULL |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

#### songs
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| title | TEXT | Song title |
| artist | TEXT | Artist name |
| mood | TEXT | Primary mood classification |
| intensity | TEXT | low/medium/high |
| valence | REAL | 0.0-1.0 (sadness-happiness) |
| energy | REAL | 0.0-1.0 (calm-energetic) |
| key | TEXT | Musical key (C, D, etc.) |
| camelot | TEXT | Camelot wheel notation |
| spotify_id | TEXT | Spotify track ID |

#### history
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | FK to users |
| song_id | INTEGER | FK to songs |
| action | TEXT | play/skip/like/dislike |
| duration_played | INTEGER | Seconds played |
| played_at | TIMESTAMP | When played |

---

## 5. ML/NLP Pipelines

### 5.1 Mood Engine v5.2

**Purpose:** Phân tích và phân loại mood dựa trên Valence-Arousal space

```
                    High Energy
                         │
          Angry    ┌─────┼─────┐    Energetic
                   │     │     │
         ──────────┼─────┼─────┼──────────
        Low        │     │     │       High
        Valence    │     │     │     Valence
         ──────────┼─────┼─────┼──────────
                   │     │     │
           Sad     └─────┼─────┘    Happy
                         │
                    Low Energy
```

**Algorithm:**
1. Extract audio features (valence, energy)
2. Map to 2D Valence-Arousal space
3. Classify into mood quadrant
4. Determine intensity based on distance from center

### 5.2 Text Mood Detector

**Purpose:** Phát hiện mood từ text tiếng Việt

**Pipeline:**
```
Text Input
     │
     ▼
┌─────────────┐
│ Preprocessing│  - Lowercase
│              │  - Remove punctuation
└──────┬───────┘  - Tokenize
       │
       ▼
┌─────────────┐
│  Keyword    │  - Match mood keywords
│  Matching   │  - Vietnamese synonyms
└──────┬───────┘
       │
       ▼
┌─────────────┐
│  Scoring    │  - Calculate mood scores
│             │  - Determine confidence
└──────┬───────┘
       │
       ▼
┌─────────────┐
│  Output     │  - Primary mood
│             │  - Intensity
└─────────────┘  - Confidence score
```

**Vietnamese Keywords:**

| Mood | Keywords |
|------|----------|
| happy | vui, hạnh phúc, phấn khởi, sướng |
| sad | buồn, đau khổ, chán, tủi |
| energetic | quẩy, sôi động, bốc, phê |
| calm | thư giãn, yên bình, nhẹ nhàng |
| romantic | yêu, nhớ, thương, tình |

### 5.3 Curator Engine v2.0

**Purpose:** Tạo playlist với harmonic mixing

**Camelot Wheel:**
```
         12B
    11B  12A  1B
   10B        2B
   10A        2A
    9B        3B
     9A  8A  3A
         8B
```

**Compatible Transitions:**
- Same position: 8A → 8A
- Adjacent number: 8A → 7A, 8A → 9A
- Same number, different letter: 8A → 8B

**Algorithm:**
1. Start with seed song
2. Find compatible next songs (Camelot)
3. Score by mood similarity
4. Select best match
5. Repeat until playlist complete

---

## 6. Security Architecture

### 6.1 Authentication Flow

```
┌─────────┐      ┌─────────┐      ┌─────────┐
│ Client  │      │  API    │      │   DB    │
└────┬────┘      └────┬────┘      └────┬────┘
     │                │                │
     │  POST /login   │                │
     │  {user, pass}  │                │
     │───────────────►│                │
     │                │  Verify hash   │
     │                │───────────────►│
     │                │◄───────────────│
     │                │                │
     │                │  Generate JWT  │
     │                │                │
     │  {token}       │                │
     │◄───────────────│                │
     │                │                │
     │  GET /api/*    │                │
     │  Bearer token  │                │
     │───────────────►│                │
     │                │  Verify JWT    │
     │                │                │
     │  Response      │                │
     │◄───────────────│                │
```

### 6.2 JWT Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "username": "duc",
    "iat": 1706745600,
    "exp": 1706832000
  }
}
```

### 6.3 Security Measures

| Measure | Implementation |
|---------|----------------|
| Password Hashing | bcrypt with salt |
| Token Expiration | 24 hours |
| HTTPS | Required in production |
| Input Validation | Pydantic models |

---

## 7. Sequence Diagrams

### 7.1 Smart Recommendation Flow

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│Frontend│     │  API   │     │TextDet │     │MoodEng │     │  DB    │
└───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘
    │              │              │              │              │
    │ POST /smart  │              │              │              │
    │ {text}       │              │              │              │
    │─────────────►│              │              │              │
    │              │              │              │              │
    │              │ detect(text) │              │              │
    │              │─────────────►│              │              │
    │              │              │              │              │
    │              │ {mood, int}  │              │              │
    │              │◄─────────────│              │              │
    │              │              │              │              │
    │              │ get_songs(mood, int)        │              │
    │              │─────────────────────────────►│              │
    │              │              │              │              │
    │              │              │              │ SELECT songs │
    │              │              │              │─────────────►│
    │              │              │              │              │
    │              │              │              │ [songs]      │
    │              │              │              │◄─────────────│
    │              │              │              │              │
    │              │ ranked_songs │              │              │
    │              │◄─────────────────────────────│              │
    │              │              │              │              │
    │ {songs}      │              │              │              │
    │◄─────────────│              │              │              │
```

### 7.2 Playlist Generation Flow

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│Frontend│     │  API   │     │Curator │     │  DB    │
└───┬────┘     └───┬────┘     └───┬────┘     └───┬────┘
    │              │              │              │
    │ POST /playlist              │              │
    │ {seed_id, len}              │              │
    │─────────────►│              │              │
    │              │              │              │
    │              │ get_seed()   │              │
    │              │─────────────────────────────►
    │              │              │              │
    │              │ seed_song    │              │
    │              │◄─────────────────────────────
    │              │              │              │
    │              │ curate(seed, len)           │
    │              │─────────────►│              │
    │              │              │              │
    │              │              │ loop: find_next()
    │              │              │─────────────►│
    │              │              │◄─────────────│
    │              │              │              │
    │              │ playlist     │              │
    │              │◄─────────────│              │
    │              │              │              │
    │ {playlist}   │              │              │
    │◄─────────────│              │              │
```

---

## Appendix

### A. Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `requirements.txt` | Python dependencies |
| `run_app.py` | Application launcher |

### B. Performance Considerations

| Component | Optimization |
|-----------|-------------|
| Database | WAL mode, connection pooling |
| API | Async handlers |
| Search | TF-IDF indexing |
| Caching | In-memory song cache |

---

*Document Version: 1.0.0*
*Last Updated: February 2025*
