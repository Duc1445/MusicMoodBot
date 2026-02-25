# System Architecture

> **MusicMoodBot Production-Ready Adaptive AI System Architecture v5.0**
> 
> A comprehensive technical architecture document for an intelligent music recommendation system with online learning capabilities, designed for CDIO academic evaluation.

---

## Document Information

| Attribute | Value |
|-----------|-------|
| **Version** | 5.0.0 |
| **Status** | Production-Ready |
| **Last Updated** | February 2026 |
| **Classification** | CDIO Capstone Project |
| **Target Audience** | Technical Reviewers, Academic Evaluators |

---

## Mục lục

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Backend Architecture](#2-backend-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Database Schema](#4-database-schema)
5. [ML/NLP Pipelines](#5-mlnlp-pipelines)
6. [Conversation Intelligence Layer](#6-conversation-intelligence-layer)
7. [Advanced Recommendation Engine v5.0](#7-advanced-recommendation-engine-v50)
8. [Cold Start Strategy](#8-cold-start-strategy)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Monitoring & Observability](#10-monitoring--observability)
11. [Security Architecture](#11-security-architecture)
12. [Sequence Diagrams](#12-sequence-diagrams)
13. [Risk Analysis & Trade-offs](#13-risk-analysis--trade-offs)
14. [End-to-End Technical Walkthrough](#14-end-to-end-technical-walkthrough)
15. [CDIO Mapping & Academic Evaluation](#15-cdio-mapping)

---

## 1. Tổng quan kiến trúc

### 1.1 System Overview (v5.0)

```
                         MusicMoodBot Production-Ready Adaptive AI System v5.0
    ┌─────────────────────────────────────────────────────────────────────────────────────┐
    │                                                                                      │
    │  ┌─────────────────┐                    ┌──────────────────────────────────────────┐│
    │  │   Flet Desktop  │    HTTP/REST       │              FastAPI Server              ││
    │  │   Application   │◄──────────────────►│  ┌────────────────────────────────────┐  ││
    │  │   (Frontend)    │                    │  │         API Gateway Layer          │  ││
    │  └─────────────────┘                    │  │   Auth │ Rate Limit │ Validation   │  ││
    │                                         │  └───────────────┬────────────────────┘  ││
    │                                         │                  │                        ││
    │  ┌─────────────────────────────────────────────────────────┼────────────────────┐  ││
    │  │                     CONVERSATION INTELLIGENCE LAYER     │                    │  ││
    │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │                    │  ││
    │  │  │ Context      │  │ Emotional    │  │ Session      │  │                    │  ││
    │  │  │ Memory       │  │ Trajectory   │  │ Reward       │◄─┘                    │  ││
    │  │  │ Manager      │  │ Tracker      │  │ Calculator   │                       │  ││
    │  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                       │  ││
    │  │         └─────────────────┴─────────────────┘                               │  ││
    │  └───────────────────────────────┬─────────────────────────────────────────────┘  ││
    │                                  │                                                 ││
    │  ┌───────────────────────────────┼─────────────────────────────────────────────┐  ││
    │  │              ADAPTIVE RECOMMENDATION ENGINE v5.0                            │  ││
    │  │  ┌────────────┬────────────┬────────────┬────────────┬────────────┐         │  ││
    │  │  │  Emotion   │  Content   │ Collaborat.│ Diversity  │Exploration │         │  ││
    │  │  │  Strategy  │  Strategy  │  Strategy  │  Strategy  │  Strategy  │◄────────│  ││
    │  │  └─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┘         │  ││
    │  │        │            │            │            │            │                 │  ││
    │  │        └────────────┴────────────┼────────────┴────────────┘                 │  ││
    │  │                                  ▼                                           │  ││
    │  │              ┌────────────────────────────────────────┐                      │  ││
    │  │              │   Exploration/Exploitation Balancer    │                      │  ││
    │  │              │   (Thompson Sampling / UCB1 / ε-Greedy)│                      │  ││
    │  │              └────────────────────────────────────────┘                      │  ││
    │  │                                  │                                           │  ││
    │  │              ┌───────────────────┴────────────────────┐                      │  ││
    │  │              │        Cold Start Handler              │                      │  ││
    │  │              │   (Popularity / Cluster Bootstrap)     │                      │  ││
    │  │              └────────────────────────────────────────┘                      │  ││
    │  └───────────────────────────────┬─────────────────────────────────────────────┘  ││
    │                                  │                                                 ││
    │  ┌───────────────────────────────┼─────────────────────────────────────────────┐  ││
    │  │              ONLINE LEARNING & FEEDBACK LOOP                                │  ││
    │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐             │  ││
    │  │  │ Contextual │  │ Preference │  │  Weight    │  │  Strategy  │             │  ││
    │  │  │ Feedback   │  │  Drift     │  │ Adjustment │  │  Updating  │◄────────────│  ││
    │  │  │ Recording  │  │ Detection  │  │  Engine    │  │  (Bandit)  │             │  ││
    │  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘             │  ││
    │  └───────────────────────────────┬─────────────────────────────────────────────┘  ││
    │                                  │                                                 ││
    │  ┌───────────────────────────────┼─────────────────────────────────────────────┐  ││
    │  │              DATA LAYER (SQLite WAL + Cache)                                │  ││
    │  │  ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐              │  ││
    │  │  │  songs  │  users  │ history │feedback │ weights │sessions │              │  ││
    │  │  └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘              │  ││
    │  └─────────────────────────────────────────────────────────────────────────────┘  ││
    │                                                                                    ││
    │  ┌─────────────────────────────────────────────────────────────────────────────┐  ││
    │  │              MONITORING & OBSERVABILITY LAYER                               │  ││
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │  ││
    │  │  │  Structured │  │  Metrics    │  │  Decision   │  │   Alert     │         │  ││
    │  │  │  Logging    │  │  Collector  │  │  Audit Log  │  │   Manager   │         │  ││
    │  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │  ││
    │  └─────────────────────────────────────────────────────────────────────────────┘  ││
    │                                                                                    ││
    └──────────────────────────────────────────────────────────────────────────────────┘│
    └─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 End-to-End Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            PRODUCTION DATA FLOW v5.0                                    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  User Input    Multi-Turn     Emotional      Context       Strategy      Ranked        │
│  "buồn quá"    Conversation   Trajectory     Enrichment    Selection     Recommendations│
│      │         Memory         Tracking           │             │              │        │
│      │              │              │             │             │              │        │
│      ▼              ▼              ▼             ▼             ▼              ▼        │
│  ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐      ┌──────┐       │
│  │ NLP  │─────►│Memory│─────►│ VA   │─────►│Feature│─────►│Bandit│─────►│Score │       │
│  │Extract│     │Update│      │Track │      │Enrich│      │Select│      │Rank  │       │
│  └──────┘      └──────┘      └──────┘      └──────┘      └──────┘      └──────┘       │
│      │              │              │             │             │              │        │
│      └──────────────┴──────────────┴─────────────┴─────────────┴──────────────┴        │
│                                         │                                              │
│                            ┌────────────┴────────────┐                                 │
│                            ▼                         ▼                                 │
│                    ┌──────────────┐          ┌──────────────┐                          │
│                    │ Explainable  │          │   Feedback   │                          │
│                    │ Recommendation│          │   Recording  │                          │
│                    └──────────────┘          └──────────────┘                          │
│                            │                         │                                 │
│                            └────────────┬────────────┘                                 │
│                                         ▼                                              │
│                               ┌──────────────────┐                                     │
│                               │  Online Learning │                                     │
│                               │  Weight Update   │                                     │
│                               │  Strategy Update │                                     │
│                               └──────────────────┘                                     │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Design Principles

| Principle | Implementation | Rationale |
|-----------|----------------|-----------|
| **Separation of Concerns** | 6-layer architecture (Gateway, Conversation, Engine, Learning, Data, Monitoring) | Enables independent testing and deployment |
| **Single Responsibility** | Each module has exactly one reason to change | Reduces coupling, improves maintainability |
| **Repository Pattern** | Data access abstracted through interfaces | Enables database swapping, simplifies testing |
| **Dependency Injection** | Services injected via constructors | Facilitates unit testing with mocks |
| **Online Learning** | Real-time weight/strategy updates from feedback | Continuous improvement without redeployment |
| **Graceful Degradation** | Cold start fallbacks, error handling | System remains functional under edge cases |
| **Explainability First** | All recommendations include reasoning | Builds user trust, aids debugging |

### 1.4 Technology Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Flet 0.80.2 │ Material Design 3 │ Responsive Layout │ State Manager  │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                          API GATEWAY LAYER                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  FastAPI 0.115 │ Pydantic v2 │ JWT Auth │ OpenAPI 3.1 │ Rate Limiting │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                     CONVERSATION INTELLIGENCE LAYER                         │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  ConversationMemory │ EmotionalTrajectory │ SessionReward │ FSM State │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                         BUSINESS/ML LAYER                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  MultiStrategyEngine │ ThompsonSampling │ TextMoodDetector │ TF-IDF   │ │
│  │  ExplainabilityModule │ ColdStartHandler │ PreferenceModel │ VA-Space │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                         DATA & CACHE LAYER                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  SQLite 3 (WAL) │ LRU Cache (L1) │ Persistent Cache (L2) │ Pooling   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                         MONITORING LAYER                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Structured Logging (JSON) │ Metrics Collector │ Decision Audit Trail │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.5 System Capabilities Matrix

| Capability | Status | Implementation |
|------------|--------|----------------|
| Multi-turn Conversation | ✅ | ConversationContextMemory with 10-turn window |
| Emotion Detection (Vietnamese) | ✅ | Rule-based + keyword matching |
| Adaptive Strategy Selection | ✅ | Thompson Sampling / UCB1 bandit |
| Preference Drift Detection | ✅ | 30-day sliding window comparison |
| Explainable Recommendations | ✅ | 4 explanation styles with emotional signals |
| Cold Start Handling | ✅ | Popularity + cluster bootstrap + hybrid fallback |
| A/B Testing Framework | ✅ | Z-test statistical significance |
| Production Deployment | ✅ | Docker + Uvicorn + Nginx |
| Structured Logging | ✅ | JSON logs with correlation IDs |

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

## 6. Conversation Intelligence Layer

### 6.1 Architecture Overview

The Conversation Intelligence Layer bridges user interaction with the recommendation engine, maintaining context across multi-turn conversations and tracking emotional evolution.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONVERSATION INTELLIGENCE LAYER                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  User Message                                                               │
│       │                                                                     │
│       ▼                                                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │              ConversationContextMemory                                 ││
│  │  ┌──────────────────────────────────────────────────────────────────┐ ││
│  │  │  Session ID: abc123                                              │ ││
│  │  │  Turn History: [{turn_1}, {turn_2}, ..., {turn_n}]  (max 10)    │ ││
│  │  │  Accumulated Entities: {artists: [...], moods: [...], genres: [...]}│ ││
│  │  │  Conversation State: FSM state (greeting → mood_elicit → recommend)│ ││
│  │  │  Last Activity: 2026-02-25T10:30:00Z                             │ ││
│  │  └──────────────────────────────────────────────────────────────────┘ ││
│  └───────────────────────────────────────────────────────────────────┬────┘│
│                                                                      │     │
│       ┌──────────────────────────────────────────────────────────────┘     │
│       │                                                                     │
│       ▼                                                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │              EmotionalTrajectoryTracker                                ││
│  │  ┌──────────────────────────────────────────────────────────────────┐ ││
│  │  │  Turn 1: VA(-0.3, -0.2) → sad                                    │ ││
│  │  │  Turn 2: VA(-0.4, -0.1) → melancholy                             │ ││
│  │  │  Turn 3: VA(-0.2, 0.1)  → nostalgic (↑ improving)                │ ││
│  │  │  Trajectory: DECLINING → STABILIZING → IMPROVING                 │ ││
│  │  │  Emotional Momentum: +0.15 (positive shift detected)             │ ││
│  │  └──────────────────────────────────────────────────────────────────┘ ││
│  └───────────────────────────────────────────────────────────────────┬────┘│
│                                                                      │     │
│       ┌──────────────────────────────────────────────────────────────┘     │
│       │                                                                     │
│       ▼                                                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │              SessionRewardCalculator                                   ││
│  │  ┌──────────────────────────────────────────────────────────────────┐ ││
│  │  │  Likes: 3   Dislikes: 1   Skips: 2   Plays: 5                    │ ││
│  │  │  Avg Listen Duration: 75%                                        │ ││
│  │  │  Emotional Improvement: +0.15                                     │ ││
│  │  │  Session Reward Score: 0.72                                       │ ││
│  │  └──────────────────────────────────────────────────────────────────┘ ││
│  └───────────────────────────────────────────────────────────────────┬────┘│
│                                                                      │     │
│       ┌──────────────────────────────────────────────────────────────┘     │
│       ▼                                                                     │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │              Context-Enriched Feature Vector                           ││
│  │  → Passed to Recommendation Engine for strategy selection              ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 ConversationContextMemory

**Purpose:** Maintains multi-turn conversation state with sliding window memory.

```python
@dataclass
class ConversationContextMemory:
    """
    Stores conversation context for a user session.
    Uses a sliding window of 10 turns to balance context richness with memory efficiency.
    """
    session_id: str
    user_id: int
    turns: List[ConversationTurn] = field(default_factory=list)
    max_turns: int = 10
    
    # Accumulated context (entities extracted across turns)
    mentioned_artists: Set[str] = field(default_factory=set)
    mentioned_genres: Set[str] = field(default_factory=set)
    mentioned_moods: List[str] = field(default_factory=list)
    
    # FSM state
    conversation_state: str = "greeting"  # greeting → mood_elicit → recommend → feedback
    
    # Temporal
    created_at: datetime
    last_activity: datetime
    
    def add_turn(self, turn: ConversationTurn) -> None:
        """Add turn with sliding window eviction."""
        self.turns.append(turn)
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)  # FIFO eviction
        
        # Update accumulated entities
        self.mentioned_moods.append(turn.detected_mood)
        self.mentioned_artists.update(turn.extracted_artists)
        self.mentioned_genres.update(turn.extracted_genres)
        self.last_activity = datetime.now()
    
    def get_dominant_mood(self) -> str:
        """Get the most frequently mentioned mood in session."""
        if not self.mentioned_moods:
            return "neutral"
        return Counter(self.mentioned_moods).most_common(1)[0][0]
    
    def get_context_features(self) -> Dict[str, Any]:
        """Extract features for recommendation enrichment."""
        return {
            'session_length': len(self.turns),
            'dominant_mood': self.get_dominant_mood(),
            'mood_consistency': self._calculate_mood_consistency(),
            'mentioned_artists': list(self.mentioned_artists),
            'mentioned_genres': list(self.mentioned_genres),
            'conversation_state': self.conversation_state,
        }
```

**Memory Eviction Strategy:**

| Strategy | Implementation | Trade-off |
|----------|----------------|-----------|
| **FIFO (Current)** | Remove oldest turn when exceeding 10 | Simple, may lose important early context |
| **Importance-weighted** | Score turns by entity density | Complex, better context retention |
| **Recency-decay** | Exponentially weight recent turns | Balances recency vs. richness |

### 6.3 EmotionalTrajectoryTracker

**Purpose:** Tracks mood evolution across conversation turns to detect emotional trends.

```python
@dataclass
class EmotionalState:
    """Single emotional state measurement."""
    valence: float      # -1.0 to 1.0 (negative to positive)
    arousal: float      # -1.0 to 1.0 (calm to energetic)
    mood_label: str     # Categorical mood
    confidence: float   # Detection confidence
    timestamp: datetime

class EmotionalTrajectoryTracker:
    """
    Tracks emotional evolution across conversation turns.
    Detects trends: DECLINING, STABLE, IMPROVING
    """
    
    def __init__(self, window_size: int = 5):
        self.states: List[EmotionalState] = []
        self.window_size = window_size
    
    def add_state(self, state: EmotionalState) -> None:
        self.states.append(state)
    
    def get_trajectory(self) -> str:
        """
        Compute emotional trajectory using linear regression on valence.
        Returns: 'DECLINING', 'STABLE', 'IMPROVING'
        """
        if len(self.states) < 2:
            return "STABLE"
        
        recent = self.states[-self.window_size:]
        valences = [s.valence for s in recent]
        
        # Simple linear trend: slope of valence over turns
        n = len(valences)
        x_mean = (n - 1) / 2
        y_mean = sum(valences) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(valences))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        if slope > 0.05:
            return "IMPROVING"
        elif slope < -0.05:
            return "DECLINING"
        return "STABLE"
    
    def get_emotional_momentum(self) -> float:
        """
        Calculate momentum: rate of emotional change.
        Positive = improving, Negative = declining
        """
        if len(self.states) < 2:
            return 0.0
        
        recent = self.states[-3:]
        if len(recent) < 2:
            return 0.0
        
        delta = recent[-1].valence - recent[0].valence
        return delta / len(recent)
    
    def should_intervene(self) -> bool:
        """
        Determine if system should proactively suggest mood improvement.
        Triggered when: trajectory is DECLINING for >= 3 turns
        """
        if len(self.states) < 3:
            return False
        
        recent_trajectories = [
            self._pairwise_trend(i) for i in range(-3, 0)
            if abs(i) <= len(self.states)
        ]
        return all(t == "DECLINING" for t in recent_trajectories)
```

**Trajectory Visualization:**

```
Valence
  │
1.0│                                    ★ Target
  │                              ╱
  │                        ╱────
  │                  ╱────
0.0│────┐      ╱────
  │    └──╲──
  │        └──╲
-1.0│            ╲
  │──────────────────────────────────── Turns
      1    2    3    4    5    6    7

  Turn 1-3: DECLINING (slope = -0.15)
  Turn 3-5: STABLE (slope = 0.02)
  Turn 5-7: IMPROVING (slope = 0.18)
```

### 6.4 SessionRewardCalculator

**Purpose:** Computes session-level satisfaction score for strategy evaluation.

```python
@dataclass
class SessionMetrics:
    """Raw metrics collected during a session."""
    likes: int = 0
    dislikes: int = 0
    skips: int = 0
    total_plays: int = 0
    total_listen_duration_pct: float = 0.0
    emotional_start: Optional[EmotionalState] = None
    emotional_end: Optional[EmotionalState] = None

class SessionRewardCalculator:
    """
    Calculates session-level reward for bandit strategy updates.
    
    Reward Components:
    1. Engagement Score (40%): likes, plays, listen duration
    2. Satisfaction Score (30%): like/dislike ratio
    3. Emotional Improvement (30%): valence change from start to end
    """
    
    WEIGHTS = {
        'engagement': 0.40,
        'satisfaction': 0.30,
        'emotional': 0.30,
    }
    
    def calculate_reward(self, metrics: SessionMetrics) -> float:
        """
        Calculate composite reward score [0.0, 1.0].
        
        Formula:
        R = w_e * E + w_s * S + w_m * M
        
        Where:
        - E = engagement_score (normalized)
        - S = satisfaction_score (like_ratio)
        - M = emotional_improvement (Δvalence normalized)
        """
        engagement = self._engagement_score(metrics)
        satisfaction = self._satisfaction_score(metrics)
        emotional = self._emotional_score(metrics)
        
        reward = (
            self.WEIGHTS['engagement'] * engagement +
            self.WEIGHTS['satisfaction'] * satisfaction +
            self.WEIGHTS['emotional'] * emotional
        )
        
        return max(0.0, min(1.0, reward))
    
    def _engagement_score(self, m: SessionMetrics) -> float:
        """
        E = 0.5 * (plays / max_plays) + 0.5 * (avg_duration / 100)
        """
        play_score = min(m.total_plays / 10, 1.0)  # Normalize to max 10 plays
        duration_score = (m.total_listen_duration_pct / m.total_plays / 100) if m.total_plays > 0 else 0
        return 0.5 * play_score + 0.5 * duration_score
    
    def _satisfaction_score(self, m: SessionMetrics) -> float:
        """
        S = (likes + 0.5 * neutral) / total_interactions
        """
        total = m.likes + m.dislikes + m.skips
        if total == 0:
            return 0.5  # Neutral baseline
        
        # Weighted: like=1.0, neutral=0.5, dislike=0, skip=-0.25
        score = (m.likes * 1.0 + m.skips * (-0.25) + m.dislikes * 0.0) / total
        return max(0.0, min(1.0, (score + 0.25) / 1.25))  # Normalize to [0,1]
    
    def _emotional_score(self, m: SessionMetrics) -> float:
        """
        M = (end_valence - start_valence + 1) / 2
        Normalized so -1→+1 change maps to 0→1
        """
        if m.emotional_start is None or m.emotional_end is None:
            return 0.5  # Neutral if no emotional data
        
        delta = m.emotional_end.valence - m.emotional_start.valence
        return (delta + 1) / 2  # Map [-1, 1] to [0, 1]
```

**Reward Component Breakdown:**

| Component | Weight | Inputs | Rationale |
|-----------|--------|--------|-----------|
| **Engagement** | 40% | plays, listen duration | Measures behavioral engagement |
| **Satisfaction** | 30% | likes, dislikes, skips | Explicit user preference signal |
| **Emotional** | 30% | Δvalence over session | Captures mood improvement goal |

### 6.5 Context-Aware Feature Enrichment

Before passing to the recommendation engine, conversation context enriches the feature vector:

```python
def enrich_recommendation_context(
    user_id: int,
    memory: ConversationContextMemory,
    trajectory: EmotionalTrajectoryTracker,
    session_metrics: SessionMetrics
) -> RecommendationContext:
    """
    Enrich recommendation context with conversation intelligence.
    """
    # Base user preferences
    base_features = get_user_preferences(user_id)
    
    # Conversation context features
    context_features = memory.get_context_features()
    
    # Emotional trajectory features
    emotional_features = {
        'current_valence': trajectory.states[-1].valence if trajectory.states else 0.0,
        'current_arousal': trajectory.states[-1].arousal if trajectory.states else 0.0,
        'trajectory': trajectory.get_trajectory(),
        'momentum': trajectory.get_emotional_momentum(),
        'should_uplift': trajectory.should_intervene(),
    }
    
    # Session reward signal (for online learning)
    reward_signal = SessionRewardCalculator().calculate_reward(session_metrics)
    
    return RecommendationContext(
        user_id=user_id,
        session_id=memory.session_id,
        base_features=base_features,
        context_features=context_features,
        emotional_features=emotional_features,
        session_reward=reward_signal,
        timestamp=datetime.now(),
    )
```

### 6.6 Conversation Intelligence Sequence Diagram

```
┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐
│ User   │   │  API   │   │Context │   │Emotion │   │Session │   │Recomm. │
│        │   │Gateway │   │Memory  │   │Tracker │   │Reward  │   │Engine  │
└───┬────┘   └───┬────┘   └───┬────┘   └───┬────┘   └───┬────┘   └───┬────┘
    │            │            │            │            │            │
    │ "buồn quá" │            │            │            │            │
    │───────────►│            │            │            │            │
    │            │            │            │            │            │
    │            │ load_session(user_id)   │            │            │
    │            │───────────►│            │            │            │
    │            │ session_ctx│            │            │            │
    │            │◄───────────│            │            │            │
    │            │            │            │            │            │
    │            │ add_turn(text, mood)    │            │            │
    │            │───────────►│            │            │            │
    │            │            │ update()   │            │            │
    │            │            │───────────►│            │            │
    │            │            │            │            │            │
    │            │            │   get_trajectory()      │            │
    │            │            │───────────►│            │            │
    │            │            │ "DECLINING"│            │            │
    │            │            │◄───────────│            │            │
    │            │            │            │            │            │
    │            │            │ get_session_metrics()   │            │
    │            │            │─────────────────────────►            │
    │            │            │            │  metrics   │            │
    │            │            │◄─────────────────────────            │
    │            │            │            │            │            │
    │            │  enrich_context()       │            │            │
    │            │───────────►│            │            │            │
    │            │  enriched_ctx           │            │            │
    │            │◄───────────│            │            │            │
    │            │            │            │            │            │
    │            │            │            │            │ recommend(ctx)
    │            │────────────────────────────────────────────────────►
    │            │            │            │            │   songs    │
    │            │◄────────────────────────────────────────────────────
    │            │            │            │            │            │
    │ {songs}    │            │            │            │            │
    │◄───────────│            │            │            │            │
```

---

## 7. Advanced Recommendation Engine v5.0

### 7.1 System Overview

The Advanced Adaptive AI Recommendation System v5.0 integrates conversation intelligence with multi-strategy recommendation, online learning, and cold start handling.

```
                    Advanced Recommendation Engine v5.0
    ┌──────────────────────────────────────────────────────────────────────┐
    │                                                                       │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │           Conversation-Enriched Context Input                   │ │
    │  │  ┌───────────────────────────────────────────────────────────┐  │ │
    │  │  │ User Features │ Session Context │ Emotional Trajectory    │  │ │
    │  │  └───────────────────────────────────────────────────────────┘  │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                                 │                                     │
    │                                 ▼                                     │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                  Cold Start Decision Gate                       │ │
    │  │  ┌──────────────────────────────────────────────────────────┐  │ │
    │  │  │  IF new_user OR sparse_feedback:                         │  │ │
    │  │  │    → Route to Cold Start Handler                         │  │ │
    │  │  │  ELSE:                                                   │  │ │
    │  │  │    → Route to Multi-Strategy Engine                      │  │ │
    │  │  └──────────────────────────────────────────────────────────┘  │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                                 │                                     │
    │                    ┌────────────┴────────────┐                        │
    │                    ▼                         ▼                        │
    │  ┌────────────────────────┐   ┌────────────────────────────────────┐ │
    │  │   Cold Start Handler   │   │      Multi-Strategy Engine         │ │
    │  │  ┌──────────────────┐  │   │  ┌───────┬───────┬───────┬───────┐ │ │
    │  │  │ Popularity Base  │  │   │  │Emotion│Content│Collab.│Explore│ │ │
    │  │  │ Cluster Bootstrap│  │   │  └───┬───┴───┬───┴───┬───┴───┬───┘ │ │
    │  │  │ Hybrid Fallback  │  │   │      └───────┴───────┴───────┘     │ │
    │  │  └──────────────────┘  │   │              │                      │ │
    │  └───────────┬────────────┘   │  ┌───────────┴───────────┐         │ │
    │              │                │  │ Thompson Sampling     │         │ │
    │              │                │  │ Exploration/Exploit   │         │ │
    │              │                │  └───────────────────────┘         │ │
    │              │                └────────────────┬────────────────────┘ │
    │              │                                 │                      │
    │              └────────────────┬────────────────┘                      │
    │                               ▼                                       │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                   Score Aggregation & Ranking                   │ │
    │  │  ┌──────────────────────────────────────────────────────────┐  │ │
    │  │  │  final_score = Σ(strategy_weight × strategy_score)       │  │ │
    │  │  │  + diversity_penalty + recency_bonus + context_boost     │  │ │
    │  │  └──────────────────────────────────────────────────────────┘  │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                                 │                                     │
    │                                 ▼                                     │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                   Explainability Layer                          │ │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │ │
    │  │  │  Template   │  │  Emotional  │  │    NLG      │              │ │
    │  │  │  Generator  │  │  Signals    │  │  Formatter  │              │ │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘              │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                                 │                                     │
    │                                 ▼                                     │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                Online Learning Feedback Loop                    │ │
    │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │ │
    │  │  │  Contextual │  │  Preference │  │   Weight    │              │ │
    │  │  │  Feedback   │  │  Drift Det. │  │  Adjustment │              │ │
    │  │  └─────────────┘  └─────────────┘  └─────────────┘              │ │
    │  │                          │                                       │ │
    │  │  ┌───────────────────────┴───────────────────────┐              │ │
    │  │  │         Bandit Strategy Reward Update         │              │ │
    │  │  │  Thompson: update(α, β) based on session reward│              │ │
    │  │  └───────────────────────────────────────────────┘              │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                                 │                                     │
    │                                 ▼                                     │
    │  ┌─────────────────────────────────────────────────────────────────┐ │
    │  │                   Evaluation & Metrics                          │ │
    │  │  Precision@K │ NDCG@K │ Session Satisfaction │ A/B Testing      │ │
    │  └─────────────────────────────────────────────────────────────────┘ │
    │                                                                       │
    └──────────────────────────────────────────────────────────────────────┘
```

### 7.2 Multi-Strategy Engine

#### Strategy Types

| Strategy | Purpose | Algorithm |
|----------|---------|-----------|
| **Emotion** | Match songs to emotional state | VA-Space mapping with euclidean distance |
| **Content** | Similar to liked songs | TF-IDF on audio features |
| **Collaborative** | Users with similar preferences | Cosine similarity on feedback vectors |
| **Diversity** | Ensure variety | Genre/artist entropy maximization |
| **Exploration** | Discover new songs | Random sampling with constraints |

#### Exploration/Exploitation Methods

```python
# Thompson Sampling (Bayesian approach)
def thompson_sampling(strategy):
    α = strategy.successes + 1
    β = strategy.failures + 1
    return random.beta(α, β)

# UCB1 (Upper Confidence Bound)
def ucb1(strategy, total_plays):
    exploitation = strategy.avg_reward
    exploration = sqrt(2 * log(total_plays) / strategy.plays)
    return exploitation + exploration

# ε-Greedy
def epsilon_greedy(strategies, epsilon=0.1):
    if random() < epsilon:
        return random_choice(strategies)
    return max(strategies, key=lambda s: s.avg_reward)
```

### 7.3 Explainability Module

#### Explanation Styles

| Style | Example Output |
|-------|----------------|
| **Casual** | "This upbeat track matches your happy mood! 🎵" |
| **Detailed** | "Selected using emotion-based strategy with 0.85 confidence. Valence: 0.8, Energy: 0.7" |
| **Minimal** | "Recommended for happy mood" |
| **Emotional** | "Feeling the joy! This song captures the bright, energetic vibes you're looking for" |

#### Emotional Signals

```
┌─────────────────────────────────────────────┐
│           Emotional Signal Detection         │
├─────────────────────────────────────────────┤
│  User Mood: "happy"                          │
│  ↓                                           │
│  VA Coordinates: (0.8, 0.6)                  │
│  ↓                                           │
│  Detected Signals:                           │
│    • joy (intensity: 0.85)                   │
│    • energy (intensity: 0.72)                │
│    • optimism (intensity: 0.65)              │
│  ↓                                           │
│  Explanation Template Selection              │
│  ↓                                           │
│  "This upbeat track captures the joy and     │
│   energy in your current mood!"              │
└─────────────────────────────────────────────┘
```

### 7.4 Feedback Learning Loop

#### Learning Flow

```
┌─────────┐     ┌─────────────┐     ┌────────────┐     ┌──────────────┐
│ User    │     │  Feedback   │     │  Drift     │     │   Weight     │
│ Action  │────►│  Recording  │────►│  Detection │────►│  Adjustment  │
└─────────┘     └─────────────┘     └────────────┘     └──────────────┘
    │                                                          │
    │                                                          ▼
    │                                                  ┌──────────────┐
    │                                                  │   Strategy   │
    └◄─────────────────────────────────────────────────│   Update     │
                   Next Recommendation                 └──────────────┘
```

#### Preference Drift Detection

Compares recent vs. historical feedback to detect changes:

```python
# Drift magnitude calculation
drift = |avg_recent(attribute) - avg_historical(attribute)|

# Significant drift threshold: > 0.1 (10% change)
if drift > 0.1:
    record_drift(user_id, attribute, drift)
    trigger_weight_adjustment()
```

#### Weight Adjustment

| Feature | Default Weight | Auto-Adjust Range |
|---------|----------------|-------------------|
| mood_match | 1.0 | 0.5 - 2.0 |
| genre_preference | 1.0 | 0.5 - 2.0 |
| artist_familiarity | 0.8 | 0.3 - 1.5 |
| energy_match | 1.0 | 0.5 - 2.0 |
| novelty | 0.5 | 0.1 - 1.0 |

### 7.5 Evaluation Metrics

#### Information Retrieval Metrics

```
Precision@K = |Relevant ∩ Retrieved@K| / K

Recall@K = |Relevant ∩ Retrieved@K| / |Relevant|

DCG@K = Σᵢ₌₁ᵏ (relᵢ / log₂(i+1))

NDCG@K = DCG@K / IDCG@K
```

#### Session Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Completion Rate | Sessions completed / Total sessions | > 70% |
| Skip Rate | Skips / Total plays | < 30% |
| Return Rate | Returning users / Total users | > 60% |

#### A/B Testing

```python
# Z-test for statistical significance
z_score = (mean_A - mean_B) / sqrt(var_A/n_A + var_B/n_B)
p_value = 2 * (1 - norm.cdf(abs(z_score)))

# Winner determination
if p_value < 0.05:
    winner = "A" if mean_A > mean_B else "B"
```

### 7.6 Performance Optimization

#### Multi-Level Cache

```
┌─────────────────────────────────────────────┐
│              Request                         │
│                 │                            │
│                 ▼                            │
│  ┌─────────────────────────────────────┐    │
│  │   L1 Cache (Memory - LRU)           │    │
│  │   TTL: 5 min | Max: 1000 entries    │    │
│  └─────────────────────────────────────┘    │
│                 │ Miss                       │
│                 ▼                            │
│  ┌─────────────────────────────────────┐    │
│  │   L2 Cache (SQLite)                 │    │
│  │   TTL: 1 hour | Max: 10000 entries  │    │
│  └─────────────────────────────────────┘    │
│                 │ Miss                       │
│                 ▼                            │
│  ┌─────────────────────────────────────┐    │
│  │   Compute & Store                   │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

#### Precomputed Emotion Clusters

Songs are grouped into mood clusters for efficient retrieval:

| Cluster | VA Centroid | Representative Mood |
|---------|-------------|---------------------|
| 0 | (0.8, 0.6) | happy |
| 1 | (-0.7, -0.3) | sad |
| 2 | (-0.6, 0.8) | angry |
| 3 | (0.5, -0.5) | calm |
| 4 | (0.7, 0.9) | excited |

### 7.7 Database Schema Extensions

```sql
-- Extended feedback table
ALTER TABLE feedback ADD COLUMN context_data TEXT;
ALTER TABLE feedback ADD COLUMN emotional_response TEXT;
ALTER TABLE feedback ADD COLUMN session_id TEXT;

-- Preference drift tracking
CREATE TABLE preference_drift (
    drift_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    attribute TEXT NOT NULL,
    old_value REAL,
    new_value REAL,
    drift_magnitude REAL,
    detected_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- User feature weights
CREATE TABLE user_weights (
    weight_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    feature TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, feature)
);

-- Weight adjustment history
CREATE TABLE weight_adjustments (
    adjustment_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    feature TEXT NOT NULL,
    old_weight REAL,
    new_weight REAL,
    reason TEXT,
    adjusted_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Experiment tracking
CREATE TABLE experiments (
    experiment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    config_a TEXT,
    config_b TEXT,
    status TEXT DEFAULT 'running',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 7.8 API Endpoints v5.0

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/recommend` | Get personalized recommendations |
| POST | `/api/v1/recommend/explain` | Get recommendations with explanations |
| GET | `/api/v1/recommend/strategies` | List available strategies |
| POST | `/api/v1/recommend/feedback` | Submit detailed feedback |
| GET | `/api/v1/metrics/dashboard` | Get metrics dashboard |
| GET | `/api/v1/metrics/experiments` | List A/B experiments |
| POST | `/api/v1/metrics/experiments` | Create new experiment |
| GET | `/api/v1/learning/drift/{user_id}` | Get preference drift |
| GET | `/api/v1/learning/weights/{user_id}` | Get user weights |
| POST | `/api/v1/learning/weights/{user_id}` | Adjust weights |
| GET | `/api/v1/session/{session_id}/context` | Get conversation context |
| GET | `/api/v1/session/{session_id}/trajectory` | Get emotional trajectory |

---

## 8. Cold Start Strategy

### 8.1 Problem Definition

Cold start is a fundamental challenge when the system lacks sufficient data to make personalized recommendations.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        COLD START SCENARIOS                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Scenario 1: NEW USER                                                   │
│  ────────────────────                                                   │
│  • No listening history                                                 │
│  • No feedback (likes/dislikes)                                         │
│  • Unknown preferences                                                  │
│  Problem: Cannot use collaborative or content-based filtering           │
│                                                                         │
│  Scenario 2: NEW SONG                                                   │
│  ─────────────────────                                                  │
│  • No user feedback yet                                                 │
│  • Unknown popularity                                                   │
│  • Only audio features available                                        │
│  Problem: No collaborative signal, only content features                │
│                                                                         │
│  Scenario 3: SPARSE FEEDBACK USER                                       │
│  ───────────────────────────────                                        │
│  • < 10 interactions in history                                         │
│  • Insufficient data for preference model                               │
│  • High variance in predictions                                         │
│  Problem: Models overfit to limited data                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Decision Tree Logic

```
                              ┌─────────────────────┐
                              │   Recommendation    │
                              │      Request        │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │ Check User History  │
                              │ feedback_count > 10?│
                              └──────────┬──────────┘
                                         │
                         ┌───────────────┼───────────────┐
                         │ NO                            │ YES
                         ▼                               ▼
              ┌─────────────────────┐         ┌─────────────────────┐
              │   COLD START PATH   │         │  STANDARD PATH      │
              │                     │         │  Multi-Strategy     │
              └──────────┬──────────┘         │  Engine             │
                         │                    └─────────────────────┘
                         ▼
              ┌─────────────────────┐
              │ Check if mood given │
              │ in conversation?    │
              └──────────┬──────────┘
                         │
              ┌──────────┼──────────┐
              │ YES                 │ NO
              ▼                     ▼
    ┌─────────────────────┐  ┌─────────────────────┐
    │ CLUSTER BOOTSTRAP   │  │ POPULARITY BASELINE │
    │ Recommend from      │  │ Top songs by global │
    │ mood cluster        │  │ like count          │
    └──────────┬──────────┘  └──────────┬──────────┘
               │                        │
               └───────────┬────────────┘
                           ▼
              ┌─────────────────────┐
              │ HYBRID FALLBACK     │
              │ Blend: 0.6×Strategy │
              │ + 0.4×Popularity    │
              └─────────────────────┘
```

### 8.3 Strategy Implementation

#### 8.3.1 Popularity Baseline

```python
class PopularityBaseline:
    """
    Fallback strategy using global popularity metrics.
    Used when no user-specific data is available.
    """
    
    def __init__(self, db_path: str, decay_days: int = 30):
        self.db_path = db_path
        self.decay_days = decay_days
    
    def get_recommendations(self, limit: int = 10) -> List[Song]:
        """
        Rank songs by popularity score with time decay.
        
        Score = (likes - 0.5 × dislikes) × decay_factor
        decay_factor = exp(-days_since_last_like / decay_days)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    s.song_id, s.song_name, s.artist, s.mood,
                    COUNT(CASE WHEN f.feedback_type = 'like' THEN 1 END) as likes,
                    COUNT(CASE WHEN f.feedback_type = 'dislike' THEN 1 END) as dislikes,
                    MAX(f.created_at) as last_feedback
                FROM songs s
                LEFT JOIN feedback f ON s.song_id = f.song_id
                GROUP BY s.song_id
                HAVING likes > 0
                ORDER BY 
                    (likes - 0.5 * dislikes) * 
                    EXP(-JULIANDAY('now') + JULIANDAY(last_feedback)) / ?
                    DESC
                LIMIT ?
            """, (self.decay_days, limit))
            
            return [Song.from_row(row) for row in cursor.fetchall()]
```

**Popularity Score Formula:**

$$
\text{PopularityScore}(s) = (L_s - 0.5 \times D_s) \times e^{-\frac{\Delta t}{30}}
$$

Where:
- $L_s$ = number of likes for song $s$
- $D_s$ = number of dislikes for song $s$
- $\Delta t$ = days since last like
- 30 = decay constant (songs lose relevance over ~1 month)

#### 8.3.2 Mood Cluster Bootstrap

```python
class MoodClusterBootstrap:
    """
    Bootstrap recommendations using mood-based clustering.
    Used when user provides mood but has no history.
    """
    
    # VA-Space mood centroids
    MOOD_CENTROIDS = {
        'happy':     (0.8, 0.6),
        'sad':       (-0.7, -0.3),
        'angry':     (-0.6, 0.8),
        'calm':      (0.5, -0.5),
        'excited':   (0.7, 0.9),
        'romantic':  (0.6, 0.2),
        'nostalgic': (0.1, -0.2),
        'energetic': (0.5, 0.9),
    }
    
    def get_recommendations(
        self, 
        mood: str, 
        limit: int = 10,
        diversity_factor: float = 0.3
    ) -> List[Song]:
        """
        Get songs from the specified mood cluster.
        
        Algorithm:
        1. Find centroid for given mood
        2. Retrieve songs within radius of centroid
        3. Apply diversity sampling to avoid repetition
        """
        if mood.lower() not in self.MOOD_CENTROIDS:
            mood = 'neutral'
            centroid = (0.0, 0.0)
        else:
            centroid = self.MOOD_CENTROIDS[mood.lower()]
        
        # Retrieve songs within distance threshold
        threshold = 0.5  # VA-space euclidean distance
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT *, 
                    SQRT(POWER(valence - ?, 2) + POWER(energy - ?, 2)) as distance
                FROM songs
                WHERE distance < ?
                ORDER BY distance ASC
                LIMIT ?
            """, (centroid[0], centroid[1], threshold, limit * 3))
            
            candidates = cursor.fetchall()
        
        # Apply diversity sampling
        return self._diversity_sample(candidates, limit, diversity_factor)
    
    def _diversity_sample(
        self, 
        candidates: List, 
        k: int, 
        diversity: float
    ) -> List[Song]:
        """
        Sample k songs maximizing diversity.
        Uses greedy maximin algorithm.
        """
        if len(candidates) <= k:
            return [Song.from_row(c) for c in candidates]
        
        selected = [candidates[0]]  # Start with closest to centroid
        candidates = candidates[1:]
        
        while len(selected) < k and candidates:
            # Score candidates by distance to already-selected songs
            best_idx = 0
            best_min_dist = -1
            
            for i, cand in enumerate(candidates):
                min_dist = min(
                    self._song_distance(cand, sel) 
                    for sel in selected
                )
                if min_dist > best_min_dist:
                    best_min_dist = min_dist
                    best_idx = i
            
            selected.append(candidates.pop(best_idx))
        
        return [Song.from_row(s) for s in selected]
```

#### 8.3.3 Hybrid Fallback Strategy

```python
class HybridFallbackStrategy:
    """
    Combines multiple strategies for cold start scenarios.
    Blends popularity with mood-based recommendations.
    """
    
    def __init__(
        self,
        popularity_weight: float = 0.4,
        cluster_weight: float = 0.6
    ):
        self.popularity = PopularityBaseline()
        self.cluster = MoodClusterBootstrap()
        self.pop_weight = popularity_weight
        self.cluster_weight = cluster_weight
    
    def get_recommendations(
        self,
        mood: Optional[str] = None,
        limit: int = 10
    ) -> List[RecommendedSong]:
        """
        Hybrid recommendation combining popularity and cluster.
        
        Strategy:
        - If mood given: 60% cluster + 40% popularity
        - If no mood: 100% popularity with diversity
        """
        results = []
        
        if mood:
            # Blend cluster and popularity
            n_cluster = int(limit * self.cluster_weight)
            n_popular = limit - n_cluster
            
            cluster_songs = self.cluster.get_recommendations(mood, n_cluster)
            popular_songs = self.popularity.get_recommendations(n_popular)
            
            # Interleave for diversity
            results = self._interleave(cluster_songs, popular_songs)
        else:
            # Pure popularity with diversity sampling
            results = self.popularity.get_recommendations(limit)
        
        return [
            RecommendedSong(
                song=s,
                score=1.0 - (i * 0.05),  # Decay by position
                strategy="cold_start_hybrid",
                explanation=self._generate_explanation(s, mood)
            )
            for i, s in enumerate(results)
        ]
    
    def _generate_explanation(self, song: Song, mood: Optional[str]) -> str:
        if mood:
            return f"Popular {mood} track that others have enjoyed"
        return "Trending song that many users love"
```

### 8.4 Cold Start Transition

As users provide feedback, the system gradually transitions from cold start to personalized recommendations:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COLD START TRANSITION CURVE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Personalization │                                        ____________  │
│  Weight          │                                   ____/              │
│        1.0       │                              ____/                   │
│                  │                         ____/                        │
│        0.8       │                    ____/                             │
│                  │               ____/                                  │
│        0.6       │          ____/                                       │
│                  │     ____/                                            │
│        0.4       │____/                                                 │
│                  │                                                      │
│        0.2       │                                                      │
│                  │                                                      │
│        0.0       │______________________________________________________│
│                  0    5    10   15   20   25   30   35   40   45   50   │
│                               User Feedback Count                       │
│                                                                         │
│  Transition Formula:                                                    │
│  personalization_weight = min(1.0, feedback_count / 30)                │
│                                                                         │
│  final_score = pw × personalized_score + (1-pw) × cold_start_score    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.5 New Song Cold Start

For new songs without feedback:

```python
def handle_new_song_cold_start(song: Song) -> float:
    """
    Score a new song without user feedback.
    
    Uses content-based features only:
    1. Audio feature similarity to user's liked songs (if available)
    2. Artist popularity (if user likes similar artists)
    3. Genre matching with user preferences
    """
    score = 0.0
    
    # Content similarity to user profile (if exists)
    if user_profile.exists():
        content_sim = cosine_similarity(
            song.audio_features,
            user_profile.avg_liked_features
        )
        score += 0.5 * content_sim
    
    # Artist popularity boost
    artist_popularity = get_artist_popularity(song.artist)
    score += 0.3 * normalize(artist_popularity)
    
    # Genre match
    if song.genre in user_profile.preferred_genres:
        score += 0.2
    
    # Exploration bonus for new songs (encourage discovery)
    score += 0.1  # Small bonus to surface new content
    
    return min(1.0, score)
```

---

## 9. Deployment Architecture

### 9.1 Production Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PRODUCTION DEPLOYMENT ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                         LOAD BALANCER                               ││
│  │                     (Nginx / Cloud LB)                              ││
│  │  ┌──────────────────────────────────────────────────────────┐       ││
│  │  │  • SSL Termination (TLS 1.3)                             │       ││
│  │  │  • Rate Limiting (100 req/min/IP)                        │       ││
│  │  │  • Request Routing                                       │       ││
│  │  │  • Health Check Routing                                  │       ││
│  │  └──────────────────────────────────────────────────────────┘       ││
│  └───────────────────────────────┬─────────────────────────────────────┘│
│                                  │                                      │
│                                  ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    APPLICATION TIER (Scaling)                       ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  ││
│  │  │  Container  │  │  Container  │  │  Container  │                  ││
│  │  │  Instance 1 │  │  Instance 2 │  │  Instance N │                  ││
│  │  │             │  │             │  │             │                  ││
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │                  ││
│  │  │ │Uvicorn  │ │  │ │Uvicorn  │ │  │ │Uvicorn  │ │                  ││
│  │  │ │4 workers│ │  │ │4 workers│ │  │ │4 workers│ │                  ││
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │                  ││
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │                  ││
│  │  │ │FastAPI  │ │  │ │FastAPI  │ │  │ │FastAPI  │ │                  ││
│  │  │ │   App   │ │  │ │   App   │ │  │ │   App   │ │                  ││
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │                  ││
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │                  ││
│  │  │ │L1 Cache │ │  │ │L1 Cache │ │  │ │L1 Cache │ │                  ││
│  │  │ │ (Local) │ │  │ │ (Local) │ │  │ │ (Local) │ │                  ││
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │                  ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  ││
│  └───────────────────────────────┬─────────────────────────────────────┘│
│                                  │                                      │
│                                  ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                      DATA TIER (Shared)                             ││
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐           ││
│  │  │     SQLite Database     │  │    Shared L2 Cache      │           ││
│  │  │      (WAL Mode)         │  │      (Optional Redis)   │           ││
│  │  │  • music.db             │  │  • Session state        │           ││
│  │  │  • Persistent volume    │  │  • Recommendation cache │           ││
│  │  └─────────────────────────┘  └─────────────────────────┘           ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Docker Configuration

**Dockerfile:**

```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY backend/ ./backend/
COPY shared/ ./shared/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--loop", "uvloop", "--http", "httptools"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  app:
    build: .
    image: musicmoodbot:latest
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - DATABASE_URL=/data/music.db
      - JWT_SECRET=${JWT_SECRET}
      - LOG_LEVEL=INFO
    volumes:
      - db_data:/data
      - logs:/app/logs
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  db_data:
  logs:
```

### 9.3 Nginx Configuration

```nginx
upstream backend {
    least_conn;
    server app:8000 weight=1 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;
    server_name musicmoodbot.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name musicmoodbot.example.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Gzip Compression
    gzip on;
    gzip_types application/json text/plain;
    
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
}
```

### 9.4 Environment Configuration

```bash
# .env.production
ENV=production
DEBUG=false

# Database
DATABASE_URL=/data/music.db
DATABASE_POOL_SIZE=5

# Security
JWT_SECRET=your-256-bit-secret-key-here
JWT_EXPIRATION_HOURS=24
BCRYPT_ROUNDS=12

# API
API_RATE_LIMIT=100
API_RATE_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/app.log

# Cache
CACHE_L1_SIZE=1000
CACHE_L1_TTL=300
CACHE_L2_ENABLED=true
CACHE_L2_TTL=3600

# ML/Recommendation
THOMPSON_PRIOR_ALPHA=1.0
THOMPSON_PRIOR_BETA=1.0
EXPLORATION_EPSILON=0.1
COLD_START_THRESHOLD=10
```

### 9.5 Horizontal Scaling Considerations

| Component | Scaling Strategy | Considerations |
|-----------|------------------|----------------|
| **API Servers** | Horizontal (add containers) | Stateless, share nothing |
| **L1 Cache** | Per-instance (not shared) | May have cache inconsistency |
| **L2 Cache** | Shared (Redis cluster) | Single source of truth |
| **SQLite DB** | Vertical only | SQLite limitation - consider PostgreSQL for scale |
| **Session State** | External store (Redis) | Required for multi-instance |

**SQLite Scaling Limitation:**

> ⚠️ **Important Trade-off:** SQLite supports concurrent reads but locks on writes. For production beyond ~100 concurrent users, consider migrating to PostgreSQL with connection pooling.

---

## 10. Monitoring & Observability

### 10.1 Logging Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    STRUCTURED LOGGING PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    Application Components                           ││
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                 ││
│  │  │  API    │  │ Recomm. │  │Learning │  │ Session │                 ││
│  │  │ Gateway │  │ Engine  │  │  Loop   │  │ Manager │                 ││
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘                 ││
│  │       │            │            │            │                       ││
│  │       └────────────┴────────────┴────────────┘                       ││
│  │                         │                                            ││
│  │                         ▼                                            ││
│  │              ┌─────────────────────────┐                             ││
│  │              │   Structured Logger     │                             ││
│  │              │   (JSON Format)         │                             ││
│  │              │   + Correlation IDs     │                             ││
│  │              └───────────┬─────────────┘                             ││
│  └──────────────────────────┼──────────────────────────────────────────┘│
│                             │                                           │
│                             ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    Log Destinations                                  ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  ││
│  │  │    File     │  │   stdout    │  │  External   │                  ││
│  │  │  (Rotating) │  │  (Docker)   │  │  (Optional) │                  ││
│  │  │  logs/*.log │  │             │  │  ELK/Loki   │                  ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Structured Log Format

```python
import logging
import json
from datetime import datetime
from typing import Any, Dict
import uuid

class StructuredLogger:
    """
    JSON structured logger with correlation ID tracking.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.correlation_id = None
    
    def set_correlation_id(self, request_id: str = None):
        """Set correlation ID for request tracing."""
        self.correlation_id = request_id or str(uuid.uuid4())[:8]
    
    def _format_log(
        self, 
        level: str, 
        event: str, 
        **kwargs
    ) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "correlation_id": self.correlation_id,
            "event": event,
            "service": "musicmoodbot",
            **kwargs
        }
        return json.dumps(log_entry)
    
    def info(self, event: str, **kwargs):
        self.logger.info(self._format_log("INFO", event, **kwargs))
    
    def error(self, event: str, **kwargs):
        self.logger.error(self._format_log("ERROR", event, **kwargs))
    
    def recommendation_decision(
        self,
        user_id: int,
        session_id: str,
        strategy_selected: str,
        thompson_scores: Dict[str, float],
        candidates_count: int,
        final_songs: list,
        latency_ms: float
    ):
        """Log recommendation decision for audit trail."""
        self.info(
            "recommendation_decision",
            user_id=user_id,
            session_id=session_id,
            strategy=strategy_selected,
            thompson_scores=thompson_scores,
            candidates=candidates_count,
            recommended_song_ids=[s.song_id for s in final_songs],
            latency_ms=round(latency_ms, 2)
        )
    
    def weight_adjustment(
        self,
        user_id: int,
        feature: str,
        old_weight: float,
        new_weight: float,
        reason: str
    ):
        """Log weight adjustment for learning audit."""
        self.info(
            "weight_adjustment",
            user_id=user_id,
            feature=feature,
            old_weight=round(old_weight, 4),
            new_weight=round(new_weight, 4),
            delta=round(new_weight - old_weight, 4),
            reason=reason
        )
    
    def drift_detection(
        self,
        user_id: int,
        attribute: str,
        old_value: float,
        new_value: float,
        magnitude: float
    ):
        """Log preference drift detection."""
        self.info(
            "preference_drift_detected",
            user_id=user_id,
            attribute=attribute,
            old_value=round(old_value, 4),
            new_value=round(new_value, 4),
            magnitude=round(magnitude, 4),
            direction="increase" if magnitude > 0 else "decrease"
        )
```

**Sample Log Output:**

```json
{
  "timestamp": "2026-02-25T10:30:45.123Z",
  "level": "INFO",
  "correlation_id": "abc12345",
  "event": "recommendation_decision",
  "service": "musicmoodbot",
  "user_id": 42,
  "session_id": "sess_789",
  "strategy": "emotion",
  "thompson_scores": {
    "emotion": 0.72,
    "content": 0.65,
    "collaborative": 0.58,
    "diversity": 0.45,
    "exploration": 0.32
  },
  "candidates": 150,
  "recommended_song_ids": [101, 203, 45, 78, 156],
  "latency_ms": 45.23
}
```

### 10.3 Metrics Collection

```python
from dataclasses import dataclass, field
from collections import defaultdict
import time
import threading

@dataclass
class MetricsCollector:
    """
    Collects and aggregates system metrics.
    """
    
    # Counters
    request_count: int = 0
    recommendation_count: int = 0
    feedback_count: defaultdict = field(default_factory=lambda: defaultdict(int))
    error_count: defaultdict = field(default_factory=lambda: defaultdict(int))
    
    # Histograms (latency tracking)
    latencies: list = field(default_factory=list)
    
    # Gauges
    active_sessions: int = 0
    cache_hit_rate: float = 0.0
    
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def record_request(self, endpoint: str, latency_ms: float, status_code: int):
        with self._lock:
            self.request_count += 1
            self.latencies.append(latency_ms)
            if status_code >= 400:
                self.error_count[status_code] += 1
    
    def record_recommendation(self, user_id: int, strategy: str, count: int):
        with self._lock:
            self.recommendation_count += count
    
    def record_feedback(self, feedback_type: str):
        with self._lock:
            self.feedback_count[feedback_type] += 1
    
    def get_latency_percentiles(self) -> Dict[str, float]:
        with self._lock:
            if not self.latencies:
                return {"p50": 0, "p95": 0, "p99": 0}
            
            sorted_lat = sorted(self.latencies)
            n = len(sorted_lat)
            return {
                "p50": sorted_lat[int(n * 0.50)],
                "p95": sorted_lat[int(n * 0.95)],
                "p99": sorted_lat[int(n * 0.99)],
            }
    
    def get_summary(self) -> Dict:
        """Get metrics summary for /metrics endpoint."""
        percentiles = self.get_latency_percentiles()
        
        total_feedback = sum(self.feedback_count.values())
        acceptance_rate = (
            (self.feedback_count['like'] + self.feedback_count['love']) / total_feedback
            if total_feedback > 0 else 0
        )
        
        return {
            "requests": {
                "total": self.request_count,
                "errors": dict(self.error_count),
                "error_rate": sum(self.error_count.values()) / max(self.request_count, 1)
            },
            "recommendations": {
                "total": self.recommendation_count,
            },
            "feedback": {
                "counts": dict(self.feedback_count),
                "acceptance_rate": round(acceptance_rate, 4),
            },
            "latency_ms": percentiles,
            "sessions": {
                "active": self.active_sessions,
            },
            "cache": {
                "hit_rate": round(self.cache_hit_rate, 4),
            }
        }
```

### 10.4 Metrics Dashboard (API Endpoint)

```python
@router.get("/metrics")
async def get_metrics():
    """
    Expose metrics for monitoring systems (Prometheus-compatible).
    """
    metrics = metrics_collector.get_summary()
    
    # Format as Prometheus metrics
    lines = [
        f"# HELP musicmoodbot_requests_total Total HTTP requests",
        f"# TYPE musicmoodbot_requests_total counter",
        f"musicmoodbot_requests_total {metrics['requests']['total']}",
        f"",
        f"# HELP musicmoodbot_latency_ms Request latency in milliseconds",
        f"# TYPE musicmoodbot_latency_ms histogram",
        f"musicmoodbot_latency_ms{{quantile=\"0.5\"}} {metrics['latency_ms']['p50']}",
        f"musicmoodbot_latency_ms{{quantile=\"0.95\"}} {metrics['latency_ms']['p95']}",
        f"musicmoodbot_latency_ms{{quantile=\"0.99\"}} {metrics['latency_ms']['p99']}",
        f"",
        f"# HELP musicmoodbot_acceptance_rate Recommendation acceptance rate",
        f"# TYPE musicmoodbot_acceptance_rate gauge",
        f"musicmoodbot_acceptance_rate {metrics['feedback']['acceptance_rate']}",
    ]
    
    return Response(content="\n".join(lines), media_type="text/plain")
```

### 10.5 Alerting Rules

| Metric | Condition | Severity | Action |
|--------|-----------|----------|--------|
| Error Rate | > 5% for 5 min | CRITICAL | Page on-call |
| P95 Latency | > 500ms for 5 min | WARNING | Investigate |
| P99 Latency | > 1000ms for 5 min | CRITICAL | Scale up |
| Acceptance Rate | < 50% for 1 hour | WARNING | Review model |
| Cache Hit Rate | < 60% for 30 min | WARNING | Check cache config |
| Active Sessions | > 1000 | INFO | Consider scaling |

### 10.6 Monitoring Data for Model Improvement

```
┌─────────────────────────────────────────────────────────────────────────┐
│                FEEDBACK LOOP: MONITORING → MODEL TUNING                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Observation                    Analysis              Action            │
│  ───────────────────────────────────────────────────────────────────── │
│                                                                         │
│  Acceptance rate drops          Low emotion strategy   Increase emotion │
│  from 70% → 55%                 success rate           strategy weight  │
│                                                                         │
│  Skip rate increases            Songs too similar      Increase         │
│  after turn 5                   (diversity issue)      diversity factor │
│                                                                         │
│  P95 latency spikes             Cache miss rate up     Adjust cache TTL │
│  during peak hours              during high load       or warm cache    │
│                                                                         │
│  Exploration strategy           Users prefer safe      Reduce epsilon   │
│  has 20% acceptance             recommendations        or exploration   │
│  vs 75% for emotion                                    weight           │
│                                                                         │
│  New users have 40%             Cold start strategy    Improve cluster  │
│  acceptance vs 70%              underperforming        bootstrap        │
│  for established users                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Security Architecture

### 11.1 Authentication Flow

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

### 11.2 JWT Structure

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

### 11.3 Security Measures

| Measure | Implementation |
|---------|----------------|
| Password Hashing | bcrypt with salt |
| Token Expiration | 24 hours |
| HTTPS | Required in production |
| Input Validation | Pydantic models |

---

## 12. Sequence Diagrams

### 12.1 Smart Recommendation Flow

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

### 12.2 Playlist Generation Flow

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
| Caching | Multi-level cache (L1 memory + L2 SQLite) |
| Clustering | Precomputed emotion clusters |

---

## 13. Risk Analysis & Trade-offs

### 13.1 Technical Risk Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       RISK ASSESSMENT MATRIX                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│              │ Low Impact        │ Medium Impact     │ High Impact      │
│  ────────────┼───────────────────┼───────────────────┼──────────────────│
│  High Prob   │ Cache misses      │ Thompson Sampling │ SQLite write     │
│              │ (mitigate: warm   │ suboptimal early  │ lock contention  │
│              │ cache on startup) │ (accept: online   │ (mitigate: Redis │
│              │                   │ learning)         │ queue writes)    │
│  ────────────┼───────────────────┼───────────────────┼──────────────────│
│  Medium Prob │ Keyword detection │ User preference   │ Cold start       │
│              │ false positives   │ drift undetected  │ poor experience  │
│              │ (mitigate: VA     │ (mitigate: drift  │ (mitigate:       │
│              │ confidence check) │ detector)         │ cluster boot)    │
│  ────────────┼───────────────────┼───────────────────┼──────────────────│
│  Low Prob    │ L2 cache          │ Explainability    │ Complete model   │
│              │ corruption        │ mismatch          │ failure          │
│              │ (mitigate: TTL    │ (mitigate: audit  │ (mitigate:       │
│              │ + validation)     │ logging)          │ fallback rules)  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Design Trade-offs

| Decision | Trade-off | Rationale | Alternative Considered |
|----------|-----------|-----------|----------------------|
| **SQLite vs PostgreSQL** | Write concurrency vs. simplicity | Single-file deployment, suitable for <100 users | PostgreSQL + connection pool |
| **Thompson Sampling vs UCB** | Exploration variance vs. regret bound | Better empirical performance | Upper Confidence Bound |
| **Rule-based mood detection + VA-space** | Interpretability vs. deep learning accuracy | Explainability required for CDIO | BERT/Transformer models |
| **Keyword + TF-IDF search** | Speed vs. semantic understanding | <50ms response requirement | Sentence embeddings |
| **In-memory L1 cache** | Per-instance consistency vs. speed | <10ms cache hit | Distributed cache (Redis) |
| **Fixed strategy weights** | Simplicity vs. hyper-optimization | Avoids overfitting | Bayesian optimization |

### 13.3 Known Limitations

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         KNOWN LIMITATIONS                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. LANGUAGE SUPPORT                                                    │
│     ─────────────────                                                   │
│     • Keyword detection optimized for Vietnamese                        │
│     • English keyword dictionary smaller                                │
│     • Slang/typos may be missed                                         │
│     Mitigation: Fallback to VA-space when keyword confidence < 0.4      │
│                                                                         │
│  2. COLD START LATENCY                                                  │
│     ────────────────────                                                │
│     • First 5-10 recommendations may be suboptimal                      │
│     • Users may churn before model learns                               │
│     Mitigation: Cluster bootstrap + popularity baseline                 │
│                                                                         │
│  3. EVALUATION BIAS                                                     │
│     ─────────────────                                                   │
│     • Offline metrics may not reflect real satisfaction                 │
│     • Position bias in implicit feedback                                │
│     Mitigation: Session reward includes emotional trajectory            │
│                                                                         │
│  4. EXPLOITATION RISK                                                   │
│     ─────────────────                                                   │
│     • Successful strategies may over-exploit                            │
│     • User preferences narrow over time (filter bubble)                 │
│     Mitigation: Diversity strategy + forced exploration (ε=0.1)         │
│                                                                         │
│  5. SCALE CEILING                                                       │
│     ─────────────────                                                   │
│     • SQLite limits concurrent writes                                   │
│     • L1 cache per-instance (inconsistency)                             │
│     Mitigation: Architecture supports PostgreSQL migration              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 13.4 Failure Modes & Fallbacks

| Failure | Detection | Fallback | Recovery |
|---------|-----------|----------|----------|
| **Mood detection fails** | `mood = None` | Use `neutral` mood | N/A |
| **Thompson Sampling returns NaN** | `isnan(score)` | Equal weights (0.2 each) | Reset bandit priors |
| **Database timeout** | `TimeoutError` | Return cached results | Retry with backoff |
| **L1 cache corrupted** | Validation check | Rebuild from L2/DB | Clear + warm |
| **All strategies fail** | `recommendations = []` | Popularity baseline | Log + alert |
| **Emotional tracker empty** | `len(trajectory) == 0` | Skip trajectory analysis | Start fresh |

### 13.5 Overfitting Mitigation

```python
class OverfittingMitigation:
    """
    Techniques to prevent model overfitting to user behavior.
    """
    
    # 1. L2 Regularization on preference weights
    WEIGHT_DECAY = 0.01  # Penalize extreme weights
    
    # 2. Minimum exploration rate
    MIN_EPSILON = 0.05  # Always explore 5% of time
    
    # 3. Weight bounds
    WEIGHT_MIN = 0.1
    WEIGHT_MAX = 2.0  # Prevent single feature domination
    
    # 4. Diversity injection
    MIN_DIVERSITY_RATIO = 0.2  # At least 20% diverse recommendations
    
    # 5. Periodic prior reset
    PRIOR_RESET_INTERVAL = 1000  # Reset Thompson priors every 1000 feedback
    
    def apply_weight_regularization(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Apply L2 regularization to prevent extreme weights."""
        for feature, weight in weights.items():
            # Decay toward mean (1.0)
            weights[feature] = weight - self.WEIGHT_DECAY * (weight - 1.0)
            
            # Enforce bounds
            weights[feature] = max(self.WEIGHT_MIN, 
                                    min(self.WEIGHT_MAX, weights[feature]))
        
        return weights
```

---

## 14. End-to-End Technical Walkthrough

### 14.1 Scenario: Vietnamese User Request

This section traces a complete request through the system to demonstrate integration of all components.

**User Input (Turn 3 of session):**
> "Hôm nay mình hơi buồn và nhớ người cũ, cho mình nghe bài gì đó nhẹ nhàng đi"

*Translation: "Today I'm a bit sad and missing my ex, play me something gentle"*

### 14.2 Step-by-Step Processing

```
┌─────────────────────────────────────────────────────────────────────────┐
│              END-TO-END REQUEST FLOW WITH TECHNICAL DETAILS             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 1: API GATEWAY (Latency: ~2ms)                                    │
│  ════════════════════════════════════                                   │
│  • Receive POST /api/v1/chat/message                                    │
│  • Validate JWT token → user_id = 42                                    │
│  • Extract session_id from request                                      │
│  • Log: correlation_id = "abc12345"                                     │
│                                                                         │
│  Request Body:                                                          │
│  {                                                                      │
│    "session_id": "sess_xyz789",                                         │
│    "message": "Hôm nay mình hơi buồn và nhớ người cũ...",              │
│    "turn": 3                                                            │
│  }                                                                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 2: TEXT MOOD DETECTION (Latency: ~8ms)                            │
│  ════════════════════════════════════════════                           │
│  • Tokenize: ["hôm", "nay", "mình", "hơi", "buồn", "và",               │
│               "nhớ", "người", "cũ", "cho", "mình", "nghe",             │
│               "bài", "gì", "đó", "nhẹ", "nhàng", "đi"]                 │
│                                                                         │
│  • Keyword Matching:                                                    │
│    - "buồn" → sad (weight: 1.0)                                        │
│    - "nhớ" → nostalgic (weight: 0.9)                                   │
│    - "nhẹ nhàng" → calm (weight: 0.8)                                  │
│                                                                         │
│  • VA-Space Calculation:                                                │
│    sad:       V=-0.7, A=-0.3 (weight: 1.0)                             │
│    nostalgic: V=+0.1, A=-0.2 (weight: 0.9)                             │
│    calm:      V=+0.5, A=-0.5 (weight: 0.8)                             │
│                                                                         │
│    Weighted Average:                                                    │
│    V = (-0.7×1.0 + 0.1×0.9 + 0.5×0.8) / 2.7 = -0.13                   │
│    A = (-0.3×1.0 + -0.2×0.9 + -0.5×0.8) / 2.7 = -0.33                  │
│                                                                         │
│  • Result:                                                              │
│    primary_mood = "sad"                                                 │
│    secondary_mood = "nostalgic"                                         │
│    valence = -0.13, arousal = -0.33                                    │
│    intensity = 0.72, confidence = 0.85                                  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 3: CONVERSATION CONTEXT UPDATE (Latency: ~3ms)                    │
│  ════════════════════════════════════════════════════                   │
│  • ConversationContextMemory.add_turn()                                 │
│                                                                         │
│  Current Context (after turn 3):                                        │
│  {                                                                      │
│    "turn_count": 3,                                                     │
│    "accumulated_moods": ["neutral", "calm", "sad"],                     │
│    "accumulated_entities": ["người cũ"],                                │
│    "mood_trajectory": [                                                 │
│      {"turn": 1, "valence": 0.2, "arousal": -0.1},                     │
│      {"turn": 2, "valence": 0.0, "arousal": -0.2},                     │
│      {"turn": 3, "valence": -0.13, "arousal": -0.33}                   │
│    ]                                                                    │
│  }                                                                      │
│                                                                         │
│  • EmotionalTrajectoryTracker.analyze():                                │
│    valence_slope = -0.165 (DECLINING)                                   │
│    arousal_slope = -0.115 (DECLINING)                                   │
│    trend = "DECLINING" (user becoming sadder)                           │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 4: COLD START CHECK (Latency: ~1ms)                               │
│  ═══════════════════════════════════════                                │
│  • Query user feedback count: 45 (> 10 threshold)                       │
│  • Result: Use standard multi-strategy engine (not cold start)          │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 5: THOMPSON SAMPLING STRATEGY SELECTION (Latency: ~5ms)           │
│  ═════════════════════════════════════════════════════════════          │
│  • Load user's bandit state for user_id=42                              │
│  • Sample from Beta distributions:                                      │
│                                                                         │
│    Strategy     | α (successes) | β (failures) | Sample                 │
│    ─────────────┼───────────────┼──────────────┼────────                │
│    emotion      | 28            | 8            | 0.78                   │
│    content      | 15            | 10           | 0.54                   │
│    collaborative| 12            | 6            | 0.61                   │
│    diversity    | 8             | 5            | 0.52                   │
│    exploration  | 5             | 8            | 0.35                   │
│                                                                         │
│  • Winner: EMOTION strategy (highest sample: 0.78)                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 6: EMOTION STRATEGY EXECUTION (Latency: ~25ms)                    │
│  ════════════════════════════════════════════════════                   │
│  • Query candidates within VA-space distance < 0.5:                     │
│    SELECT * FROM songs                                                  │
│    WHERE SQRT((valence - -0.13)² + (energy - -0.33)²) < 0.5            │
│                                                                         │
│  • Retrieved: 47 candidate songs                                        │
│                                                                         │
│  • Load user preference weights (from last learning update):            │
│    {                                                                    │
│      "mood_match": 1.35,                                                │
│      "emotional_resonance": 1.42,                                       │
│      "valence_alignment": 1.28,                                         │
│      "artist_preference": 0.95,                                         │
│      "tempo_comfort": 1.10                                              │
│    }                                                                    │
│                                                                         │
│  • Context-aware feature enrichment:                                    │
│    - Turn 3 → mood_stability_weight = 1.2                              │
│    - Trajectory DECLINING → comfort_music_boost = 0.15                  │
│    - Entity "người cũ" → romance_penalty = -0.1                        │
│                                                                         │
│  • Score calculation for each song:                                     │
│    score = Σ(feature_value × weight × context_modifier)                │
│                                                                         │
│  • Example: Song "Có Chắc Yêu Là Đây" (ID: 203)                        │
│    mood_match: 0.85 × 1.35 × 1.2 = 1.38                                │
│    emotional: 0.78 × 1.42 × 1.15 = 1.27                                │
│    valence: 0.72 × 1.28 × 1.0 = 0.92                                   │
│    artist: 0.60 × 0.95 × 1.0 = 0.57                                    │
│    tempo: 0.80 × 1.10 × 1.0 = 0.88                                     │
│    TOTAL: 5.02 (normalized: 0.84)                                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 7: DIVERSITY FILTER (Latency: ~8ms)                               │
│  ═══════════════════════════════════════                                │
│  • Sort by score, take top 15                                           │
│  • Apply greedy maximin diversification:                                │
│    - Ensure no 2 consecutive same artist                                │
│    - Min genre variety: 3 genres in top 5                               │
│    - VA-space spread: min 0.1 distance between neighbors                │
│                                                                         │
│  • Final top 5 after diversification:                                   │
│    1. "Có Chắc Yêu Là Đây" - Sơn Tùng (score: 0.84)                   │
│    2. "Em Của Ngày Hôm Qua" - Phan Mạnh Quỳnh (score: 0.79)            │
│    3. "Nơi Này Có Anh" - Sơn Tùng (score: 0.76)                        │
│    4. "Bước Qua Đời Nhau" - Lê Bảo Bình (score: 0.73)                  │
│    5. "Chạy Ngay Đi" - Sơn Tùng (excluded - diversity)                 │
│    → "Hãy Trao Cho Anh" - Sơn Tùng (score: 0.71)                       │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 8: EXPLAINABILITY GENERATION (Latency: ~5ms)                      │
│  ═════════════════════════════════════════════════                      │
│  • Generate explanations using ExplainableRecommender:                  │
│                                                                         │
│  Song 1 explanation:                                                    │
│  "Bài này phù hợp với tâm trạng buồn và nhớ nhung của bạn,            │
│   có giai điệu nhẹ nhàng giúp xoa dịu cảm xúc"                        │
│                                                                         │
│  Technical explanation:                                                 │
│  {                                                                      │
│    "primary_factor": "emotional_resonance",                             │
│    "contribution": 0.32,                                                │
│    "secondary_factors": ["mood_match", "valence_alignment"],            │
│    "strategy_used": "emotion",                                          │
│    "confidence": 0.84                                                   │
│  }                                                                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 9: CACHE UPDATE (Latency: ~2ms)                                   │
│  ═══════════════════════════════════                                    │
│  • Store in L1 (in-memory):                                             │
│    key = "rec:42:sess_xyz789:3"                                         │
│    value = [song_ids], TTL = 5 minutes                                  │
│                                                                         │
│  • Store in L2 (SQLite):                                                │
│    key = "rec:42:sad:nostalgic"                                         │
│    value = serialized recommendations, TTL = 1 hour                     │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 10: RESPONSE FORMATTING (Latency: ~2ms)                           │
│  ═════════════════════════════════════════════                          │
│  {                                                                      │
│    "session_id": "sess_xyz789",                                         │
│    "turn": 3,                                                           │
│    "detected_mood": {                                                   │
│      "primary": "sad",                                                  │
│      "secondary": "nostalgic",                                          │
│      "confidence": 0.85                                                 │
│    },                                                                   │
│    "recommendations": [                                                 │
│      {                                                                  │
│        "song_id": 203,                                                  │
│        "title": "Có Chắc Yêu Là Đây",                                  │
│        "artist": "Sơn Tùng M-TP",                                       │
│        "score": 0.84,                                                   │
│        "explanation": "Bài này phù hợp với tâm trạng..."               │
│      },                                                                 │
│      // ... 4 more songs                                                │
│    ],                                                                   │
│    "context": {                                                         │
│      "trajectory": "DECLINING",                                         │
│      "session_reward_so_far": 0.68                                      │
│    }                                                                    │
│  }                                                                      │
│                                                                         │
│  TOTAL LATENCY: ~61ms ✓ (< 500ms target)                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 14.3 Post-Response Learning (Async)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 ASYNC POST-RESPONSE LEARNING LOOP                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  USER ACTION: Liked song #203 "Có Chắc Yêu Là Đây"                     │
│                                                                         │
│  STEP A: BANDIT UPDATE                                                  │
│  ─────────────────────                                                  │
│  • Strategy "emotion" received positive feedback                        │
│  • Update: α_emotion = 28 → 29                                          │
│  • New expected success rate: 29/(29+8) = 0.78                          │
│                                                                         │
│  STEP B: PREFERENCE WEIGHT UPDATE                                       │
│  ─────────────────────────────────                                      │
│  • Song #203 features:                                                  │
│    {valence: -0.15, energy: -0.30, tempo: 75, mood: "sad"}             │
│                                                                         │
│  • Update emotional_resonance weight:                                   │
│    new_weight = 1.42 + 0.05 × (1 - 1.42) × 0.5 = 1.43                  │
│    (positive feedback on high emotional match)                          │
│                                                                         │
│  STEP C: SESSION REWARD UPDATE                                          │
│  ─────────────────────────────                                          │
│  • Engagement: 1.0 (liked)                                              │
│  • Satisfaction: 0.85 (high score song)                                 │
│  • Emotional: trajectory improved? → +0.1 bonus                         │
│                                                                         │
│  • Session reward = 0.4×1.0 + 0.3×0.85 + 0.3×0.75 = 0.88              │
│                                                                         │
│  STEP D: PERSISTENCE                                                    │
│  ─────────────────────                                                  │
│  • Write to feedback table                                              │
│  • Update user_preferences table                                        │
│  • Update user_strategy_stats table                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 14.4 Latency Breakdown

| Step | Component | Time (ms) | % of Total |
|------|-----------|-----------|------------|
| 1 | API Gateway | 2 | 3.3% |
| 2 | Mood Detection | 8 | 13.1% |
| 3 | Context Update | 3 | 4.9% |
| 4 | Cold Start Check | 1 | 1.6% |
| 5 | Thompson Sampling | 5 | 8.2% |
| 6 | Strategy Execution | 25 | 41.0% |
| 7 | Diversity Filter | 8 | 13.1% |
| 8 | Explainability | 5 | 8.2% |
| 9 | Cache Update | 2 | 3.3% |
| 10 | Response Format | 2 | 3.3% |
| **Total** | | **61** | **100%** |

---

## 15. CDIO Mapping

### 15.1 Conceive (C) — Problem Analysis & Requirements

| Aspect | Implementation | Evidence |
|--------|----------------|----------|
| **Problem Statement** | Users need intelligent, personalized music recommendations based on mood and preferences | User research, market analysis |
| **Stakeholder Analysis** | End users (music listeners), operators (system admins), evaluators (academic) | Requirements documented |
| **Requirements Elicitation** | Functional: mood detection, recommendations, learning. Non-functional: <500ms latency, >70% acceptance | Specification document |
| **Design Constraints** | SQLite (single-file), Python ecosystem, academic evaluation criteria | Technology decisions documented |
| **Success Criteria** | Precision@10 > 0.65, NDCG@10 > 0.70, user satisfaction > 70% | Measurable KPIs defined |

### 15.2 Design (D) — Architecture & Algorithm Design

| Component | Design Decision | Rationale | Alternatives Considered |
|-----------|-----------------|-----------|------------------------|
| **Architecture Pattern** | 6-Layer Clean Architecture | Separation of concerns, testability | Monolith, Microservices |
| **Strategy Selection** | Thompson Sampling (Multi-Armed Bandit) | Balances exploration/exploitation, online learning | UCB1, ε-greedy, fixed weights |
| **Emotion Mapping** | VA-Space (Valence-Arousal) | Psychologically grounded, continuous space | Discrete categories, Plutchik wheel |
| **Text Processing** | Rule-based + TF-IDF | Interpretable, fast, sufficient for Vietnamese | BERT, Transformer models |
| **Data Storage** | SQLite with WAL mode | Simple deployment, sufficient for scale | PostgreSQL, MongoDB |
| **Caching Strategy** | 2-Level (L1 memory, L2 SQLite) | Balance speed and persistence | Redis, single-level cache |

### 15.3 Implement (I) — Module Implementation

| Module | Technology | LOC | Key Classes | Test Coverage |
|--------|------------|-----|-------------|---------------|
| **Conversation Intelligence** | Python | ~600 | `ConversationContextMemory`, `EmotionalTrajectoryTracker`, `SessionRewardCalculator` | Unit + Integration |
| **Multi-Strategy Engine** | Python, NumPy | ~850 | `MultiStrategyEngine`, `ThompsonSamplingBandit` | 85% |
| **Explainability Module** | Python | ~500 | `ExplainableRecommender`, `ExplanationGenerator` | 80% |
| **Evaluation Metrics** | Python, SciPy | ~650 | `EvaluationEngine`, `MetricsCalculator` | 90% |
| **Cold Start Handler** | Python | ~400 | `PopularityBaseline`, `MoodClusterBootstrap` | 75% |
| **Performance Cache** | Python, SQLite | ~700 | `MultiLevelCache`, `CacheManager` | 85% |
| **Monitoring** | Python, JSON | ~300 | `StructuredLogger`, `MetricsCollector` | 70% |
| **API Endpoints** | FastAPI, Pydantic | ~600 | Routes, validators, middleware | 80% |

### 15.4 Operate (O) — Deployment & Evaluation

#### 15.4.1 Operational Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Precision@10 | > 0.65 | TBD | Testing |
| NDCG@10 | > 0.70 | TBD | Testing |
| P95 Latency | < 500ms | ~150ms | ✅ Met |
| Acceptance Rate | > 70% | TBD | Testing |
| Cold Start Acceptance | > 50% | TBD | Testing |

#### 15.4.2 Validation Plan

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      EVALUATION METHODOLOGY                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PHASE 1: UNIT TESTING                                                  │
│  ─────────────────────                                                  │
│  • Test individual components in isolation                              │
│  • Mock dependencies for deterministic tests                            │
│  • Coverage target: >80% for core modules                               │
│                                                                         │
│  PHASE 2: INTEGRATION TESTING                                           │
│  ────────────────────────────                                           │
│  • Test component interactions                                          │
│  • API endpoint testing with real database                              │
│  • End-to-end conversation flow tests                                   │
│                                                                         │
│  PHASE 3: OFFLINE EVALUATION                                            │
│  ───────────────────────────                                            │
│  • Train/test split on historical data (80/20)                          │
│  • Calculate Precision@K, Recall@K, NDCG@K                              │
│  • Compare strategies: emotion vs content vs collaborative              │
│                                                                         │
│  PHASE 4: ONLINE A/B TESTING (if deployed)                              │
│  ─────────────────────────────────────────                              │
│  • Split users into control (v4.0) and treatment (v5.0)                 │
│  • Track: acceptance rate, session length, return rate                  │
│  • Statistical significance: p < 0.05, minimum 100 users per group      │
│                                                                         │
│  PHASE 5: USER STUDY (optional, academic)                               │
│  ────────────────────────────────────────                               │
│  • N=20 participants                                                    │
│  • Pre/post questionnaire (SUS, TAM)                                    │
│  • Think-aloud protocol for qualitative feedback                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 15.4.3 Statistical Testing Framework

| Hypothesis | Test | Significance Level |
|------------|------|-------------------|
| v5.0 acceptance > v4.0 | Independent t-test | α = 0.05 |
| Emotion strategy > random | Wilcoxon signed-rank | α = 0.05 |
| P95 latency < 500ms | One-sample t-test | α = 0.01 |
| Session reward correlation | Pearson correlation | ρ > 0.3 |

### 15.5 CDIO Learning Outcomes

| CDIO Skill | Competency Level | Demonstrated Through |
|------------|------------------|---------------------|
| **Technical Knowledge (2.1)** | Proficient | ML algorithms (Thompson Sampling, TF-IDF), NLP, database design |
| **Engineering Reasoning (2.2)** | Proficient | Trade-off analysis (exploration/exploitation, speed/accuracy) |
| **Systematic Problem Solving (2.4)** | Advanced | End-to-end system design, failure mode analysis |
| **Communication (3.1)** | Proficient | Technical documentation, API specification |
| **Teamwork (3.2)** | Proficient | Modular design enabling parallel development |
| **Professional Ethics (4.1)** | Aware | User privacy considerations, data handling |
| **Systems Thinking (4.3)** | Advanced | Multi-component integration, feedback loops |

### 15.6 Academic Contribution Summary

| Contribution | Type | Novelty |
|--------------|------|---------|
| **Multi-turn conversation context for recommendations** | Architecture | Combination of sliding window + emotional trajectory |
| **Hybrid cold start with mood cluster bootstrap** | Algorithm | Integrates popularity + mood-based clustering |
| **Session reward with emotional trajectory** | Metric | Novel composite reward including emotional improvement |
| **Thompson Sampling for strategy selection** | Application | Applied to recommendation strategies (not just items) |
| **Vietnamese mood keyword mapping** | Data | Language-specific emotional keyword dictionary |

---

## Appendix

### A. Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `requirements.txt` | Python dependencies |
| `run_app.py` | Application launcher |
| `docker-compose.yml` | Container orchestration |
| `nginx.conf` | Reverse proxy configuration |

### B. Performance Benchmarks

| Component | Metric | Value |
|-----------|--------|-------|
| Mood Detection | Latency (P95) | 15ms |
| Thompson Sampling | Sample time | 2ms |
| Song Retrieval | 100 songs | 20ms |
| Complete Request | End-to-end P95 | 150ms |
| L1 Cache Hit | Lookup time | <1ms |
| L2 Cache Hit | Lookup time | 5ms |

### C. Glossary

| Term | Definition |
|------|------------|
| **VA-Space** | Valence-Arousal dimensional model of emotion |
| **Thompson Sampling** | Bayesian approach to multi-armed bandit problem |
| **Cold Start** | Scenario when insufficient data exists for personalization |
| **NDCG** | Normalized Discounted Cumulative Gain, ranking quality metric |
| **Precision@K** | Proportion of relevant items in top K recommendations |
| **Exploration/Exploitation** | Trade-off between trying new items vs. using known good items |

---

*Document Version: 5.0.0*
*Architecture: Production-Ready Adaptive AI System*
*Last Updated: February 2025*
