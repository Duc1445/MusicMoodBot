# MusicMoodBot Multi-Turn Conversation System Architecture

**Version**: 3.0.0  
**Last Updated**: 2024  
**Author**: MusicMoodBot Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Database Schema](#3-database-schema)
4. [Component Design](#4-component-design)
5. [State Machine (FSM)](#5-state-machine-fsm)
6. [Conversation Flow](#6-conversation-flow)
7. [API Specification](#7-api-specification)
8. [Integration Guide](#8-integration-guide)
9. [CDIO Phase Mapping](#9-cdio-phase-mapping)

---

## 1. Executive Summary

### 1.1 Purpose

The Multi-Turn Conversation System transforms MusicMoodBot from a single-turn mood detection architecture into a sophisticated dialogue system capable of:

- **Emotional depth tracking**: Accumulating mood signals across multiple turns
- **Clarity scoring**: Quantifying understanding of user's emotional state
- **Context-aware recommendations**: Using activity, time, and social context
- **Adaptive probing**: Asking clarifying questions when needed
- **Session persistence**: Maintaining conversation state across interactions

### 1.2 Key Features

| Feature | Description |
|---------|-------------|
| Multi-Turn Dialogue | Up to 5 turns of conversation to fully understand mood |
| FSM-Based Flow | 10 dialogue states with guard-controlled transitions |
| Emotional Accumulation | Weighted averaging of mood signals over time |
| Clarity Scoring | 5-component weighted formula for confidence |
| Intent Classification | 16 intent types with regex pattern matching |
| Context Extraction | Time, activity, social, and location signals |
| Idempotency | Hash-based duplicate request handling |

### 1.3 Architecture Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **State Isolation**: Session state is contained and transferable
3. **Graceful Degradation**: System continues if components fail
4. **Backwards Compatibility**: Existing APIs remain functional
5. **Testability**: All components support dependency injection

---

## 2. System Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │  Flet UI   │  │  REST API  │  │  WebSocket │  │   CLI      │        │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │
└────────┼───────────────┼───────────────┼───────────────┼────────────────┘
         │               │               │               │
         └───────────────┴───────────────┴───────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API LAYER (FastAPI)                              │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  /conversation/turn    /conversation/start    /conversation/end   │ │
│  │  /chat/message         /chat/feedback         /playlist/*         │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONVERSATION MANAGER (Orchestrator)                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                   │   │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │   │
│  │   │   Intent    │───▶│  Emotion    │───▶│  Clarity    │         │   │
│  │   │ Classifier  │    │  Tracker    │    │   Model     │         │   │
│  │   └─────────────┘    └─────────────┘    └─────────────┘         │   │
│  │          │                  │                  │                  │   │
│  │          │                  │                  │                  │   │
│  │          ▼                  ▼                  ▼                  │   │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │   │
│  │   │  Dialogue   │◀───│  Strategy   │◀───│  Question   │         │   │
│  │   │     FSM     │    │   Engine    │    │    Bank     │         │   │
│  │   └─────────────┘    └─────────────┘    └─────────────┘         │   │
│  │          │                                                        │   │
│  │          ▼                                                        │   │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │   │
│  │   │   Session   │───▶│   Context   │    │  Response   │         │   │
│  │   │    Store    │    │  Extractor  │    │  Generator  │         │   │
│  │   └─────────────┘    └─────────────┘    └─────────────┘         │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      RECOMMENDATION PIPELINE                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ TextMood   │  │   Mood     │  │ Preference │  │  Curator   │        │
│  │ Detector   │  │  Engine    │  │   Model    │  │  Engine    │        │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER (SQLite)                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   users    │  │   songs    │  │ sessions   │  │   turns    │        │
│  │   prefs    │  │  feedback  │  │  contexts  │  │ idempotent │        │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Sequence

```
User Input                    
     │                        
     ▼                        
┌────────────┐               
│   Parse    │               
│   Input    │               
└─────┬──────┘               
      │                       
      ▼                       
┌────────────┐               
│ Idempotency│──Yes──▶ Return Cached Response
│   Check    │               
└─────┬──────┘               
      │No                     
      ▼                       
┌────────────┐               
│  Extract   │               
│  Context   │               
└─────┬──────┘               
      │                       
      ▼                       
┌────────────┐               
│  Classify  │               
│   Intent   │               
└─────┬──────┘               
      │                       
      ├───── EXIT ──────▶ End Session
      │                       
      ▼                       
┌────────────┐               
│   Detect   │               
│    Mood    │               
└─────┬──────┘               
      │                       
      ▼                       
┌────────────┐               
│   Update   │               
│  Tracker   │               
└─────┬──────┘               
      │                       
      ▼                       
┌────────────┐               
│  Calculate │               
│  Clarity   │               
└─────┬──────┘               
      │                       
      ▼                       
┌────────────┐               
│    FSM     │               
│ Transition │               
└─────┬──────┘               
      │                       
      ├───── PROBING ──────▶ Select Question
      │                       
      ├───── RECOMMENDATION ▶ Trigger Pipeline
      │                       
      ▼                       
┌────────────┐               
│  Generate  │               
│  Response  │               
└─────┬──────┘               
      │                       
      ▼                       
┌────────────┐               
│   Save     │               
│   Turn     │               
└─────┬──────┘               
      │                       
      ▼                       
Return Response              
```

---

## 3. Database Schema

### 3.1 New Tables

#### conversation_sessions

```sql
CREATE TABLE conversation_sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    state TEXT DEFAULT 'GREETING',
    started_at TEXT NOT NULL,
    last_activity_at TEXT NOT NULL,
    expires_at TEXT,
    ended_at TEXT,
    turn_count INTEGER DEFAULT 0,
    max_turns INTEGER DEFAULT 5,
    final_mood TEXT,
    final_intensity REAL,
    final_confidence REAL,
    context_snapshot TEXT,  -- JSON
    is_active INTEGER DEFAULT 1,
    early_exit_reason TEXT,
    client_info TEXT,  -- JSON
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_sessions_user ON conversation_sessions(user_id, is_active);
CREATE INDEX idx_sessions_active ON conversation_sessions(is_active, expires_at);
```

#### conversation_turns

```sql
CREATE TABLE conversation_turns (
    turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    
    -- Input
    user_input TEXT NOT NULL,
    input_type TEXT DEFAULT 'text',
    
    -- Mood Detection
    detected_mood TEXT,
    detected_intensity REAL,
    mood_confidence REAL,
    keywords_matched TEXT,  -- JSON array
    
    -- Intent
    intent TEXT,
    intent_confidence REAL,
    
    -- Context
    context_signals TEXT,  -- JSON
    emotional_signals TEXT,  -- JSON
    
    -- Output
    bot_response TEXT NOT NULL,
    response_type TEXT,
    question_asked TEXT,
    
    -- State
    state_before TEXT,
    state_after TEXT,
    
    -- Clarity
    clarity_score_before REAL,
    clarity_score_after REAL,
    clarity_delta REAL,
    
    -- Meta
    created_at TEXT DEFAULT (datetime('now')),
    processing_time_ms INTEGER,
    
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id)
);

CREATE INDEX idx_turns_session ON conversation_turns(session_id, turn_number);
```

#### emotional_contexts

```sql
CREATE TABLE emotional_contexts (
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    captured_at TEXT DEFAULT (datetime('now')),
    
    -- Aggregated emotions
    dominant_mood TEXT,
    average_intensity REAL,
    average_valence REAL,
    average_arousal REAL,
    mood_history TEXT,  -- JSON array
    intensity_history TEXT,  -- JSON array
    
    -- Clarity
    clarity_score REAL,
    
    -- Mood stability
    mood_variance REAL,
    mood_stable INTEGER DEFAULT 0,
    
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id)
);
```

#### probing_questions

```sql
CREATE TABLE probing_questions (
    question_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    depth_level INTEGER NOT NULL,
    question_text_vi TEXT NOT NULL,
    question_text_en TEXT NOT NULL,
    expected_info TEXT,
    response_patterns TEXT,  -- JSON
    usage_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    is_active INTEGER DEFAULT 1
);
```

#### idempotency_keys

```sql
CREATE TABLE idempotency_keys (
    key TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    turn_id INTEGER,
    result_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL
);

CREATE INDEX idx_idempotency_expires ON idempotency_keys(expires_at);
```

### 3.2 Schema Relationships

```
users
  │
  ├──< conversation_sessions
  │       │
  │       ├──< conversation_turns
  │       │
  │       ├──< emotional_contexts
  │       │
  │       └──< idempotency_keys
  │
  ├──< user_preferences
  │
  ├──< listening_history
  │
  └──< feedback
```

---

## 4. Component Design

### 4.1 IntentClassifier

**Purpose**: Classify user intent from input text.

**Pattern Categories**:

| Intent | Pattern Examples |
|--------|------------------|
| GREETING | `xin chào`, `hello`, `hi` |
| MOOD_EXPRESSION | `tôi.*buồn`, `feeling.*happy` |
| MUSIC_REQUEST | `gợi ý`, `recommend`, `play` |
| CONTEXT_SHARING | `đang.*làm việc`, `at.*gym` |
| REFINE_REQUEST | `nhạc.*khác`, `more like` |
| EXIT | `tạm biệt`, `bye`, `quit` |
| HELP | `hướng dẫn`, `help`, `how to` |

**Algorithm**:
```python
def classify(text, current_state):
    # Priority order matters
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text):
                return intent, calculate_confidence(pattern, text)
    
    # State-aware fallback
    if current_state == PROBING_DEPTH:
        return Intent.MOOD_ELABORATION, 0.6
    
    return Intent.UNKNOWN, 0.0
```

### 4.2 EmotionDepthTracker

**Purpose**: Accumulate and aggregate emotional signals over turns.

**Key Data Structures**:
```python
@dataclass
class EmotionalContext:
    dominant_mood: str
    average_intensity: float
    average_valence: float
    average_arousal: float
    mood_history: List[str]
    intensity_history: List[float]
    clarity_score: float = 0.0
```

**Accumulation Formula**:
```
weight[i] = decay^(n-i) where decay=0.8
weighted_intensity = Σ(intensity[i] * weight[i]) / Σ(weight[i])
```

### 4.3 EmotionClarityModel

**Purpose**: Calculate a clarity score representing confidence in mood understanding.

**Scoring Formula**:
```
ClarityScore = 
    w_signals * min(signal_count/2, 1.0) +
    w_consistency * (1 - mood_variance) +
    w_confidence * avg_confidence +
    w_depth * min(turn_count/3, 1.0) +
    w_context * has_context_bonus
```

**Default Weights**:
- Signal count: 0.25
- Consistency: 0.30
- Confidence: 0.25
- Depth: 0.10
- Context: 0.10

### 4.4 ClarificationStrategyEngine

**Purpose**: Determine questioning strategy based on current context.

**Strategy Selection Matrix**:

| Clarity Score | Has Context | Turn Count | Strategy |
|--------------|-------------|------------|----------|
| < 0.5 | No | < 2 | OPEN_ENDED |
| < 0.5 | No | >= 2 | CONTEXT_FIRST |
| 0.5-0.75 | Yes | any | INTENSITY_PROBE |
| >= 0.75 | any | any | CONFIRM_AND_REC |

### 4.5 SessionStore

**Purpose**: Persist and retrieve conversation sessions and turns.

**Key Operations**:
- `create_session(user_id)` → ConversationSession
- `get_session(session_id)` → Optional[ConversationSession]
- `save_turn(session, turn)` → turn_id
- `check_idempotency(key)` → Optional[cached_response]
- `cleanup_expired()` → count

---

## 5. State Machine (FSM)

### 5.1 Dialogue States

| State | Code | Purpose |
|-------|------|---------|
| GREETING | 0 | Initial state, welcome user |
| INITIAL_QUERY | 1 | First mood expression received |
| ACKNOWLEDGING | 2 | Bot acknowledges mood |
| PROBING_DEPTH | 3 | Ask for elaboration |
| EXPLORING_CONTEXT | 4 | Ask about activity/situation |
| CONFIRMING_MOOD | 5 | Verify understanding |
| RECOMMENDATION | 6 | Ready to recommend |
| DELIVERY | 7 | Sending recommendations |
| REFINING | 8 | Adjusting recommendations |
| ENDED | 9 | Session complete |
| TIMEOUT | 10 | Session expired |

### 5.2 State Transition Diagram

```
                    ┌──────────┐
                    │ GREETING │
                    └────┬─────┘
                         │ user_input
                         ▼
                 ┌───────────────┐
                 │ INITIAL_QUERY │
                 └───────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │ ACKNOWLEDGING  │
                └───────┬────────┘
                        │
          ┌─────────────┴─────────────┐
          │                           │
    clarity < 0.75              clarity >= 0.75
          │                           │
          ▼                           ▼
   ┌─────────────┐           ┌─────────────────┐
   │PROBING_DEPTH│           │ CONFIRMING_MOOD │
   └──────┬──────┘           └────────┬────────┘
          │                           │
          ▼                           │
   ┌──────────────────┐              │
   │EXPLORING_CONTEXT │              │
   └────────┬─────────┘              │
            │                         │
            └─────────────────────────┤
                                      │ confirmed
                                      ▼
                            ┌─────────────────┐
                            │ RECOMMENDATION  │
                            └────────┬────────┘
                                     │
                                     ▼
                              ┌──────────┐
                              │ DELIVERY │
                              └────┬─────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
              want_more                     satisfied/exit
                    │                             │
                    ▼                             ▼
             ┌──────────┐                   ┌─────────┐
             │ REFINING │                   │  ENDED  │
             └──────────┘                   └─────────┘
```

### 5.3 Guard Functions

```python
guards = {
    'is_high_clarity': lambda ctx: ctx['clarity_score'] >= CLARITY_THRESHOLD,
    'needs_more_depth': lambda ctx: ctx['clarity_score'] < 0.5,
    'has_context': lambda ctx: ctx.get('has_context', False),
    'max_turns_reached': lambda ctx: ctx['turn_count'] >= MAX_TURNS,
    'is_exit_intent': lambda ctx: ctx['intent'] == Intent.EXIT,
    'wants_refinement': lambda ctx: ctx['intent'] == Intent.REFINE_REQUEST,
}
```

---

## 6. Conversation Flow

### 6.1 Typical Happy Path

```
Turn 1:
  User: "Hôm nay tôi buồn quá"
  Bot: "Mình hiểu bạn đang buồn 💙 Bạn buồn vì chuyện gì vậy?"
  State: GREETING → PROBING_DEPTH
  Clarity: 0.35

Turn 2:
  User: "Chuyện tình cảm..."
  Bot: "Mình hiểu. Bạn đang ở đâu/làm gì vậy?"
  State: PROBING_DEPTH → EXPLORING_CONTEXT
  Clarity: 0.55

Turn 3:
  User: "Đang ở nhà một mình"
  Bot: "Vậy là bạn đang buồn vì tình cảm đúng không? Mình sẽ tìm nhạc phù hợp!"
  State: EXPLORING_CONTEXT → CONFIRMING_MOOD
  Clarity: 0.78

Turn 4:
  User: "Đúng rồi"
  Bot: "Đây là những bài hát mình chọn cho bạn... [songs]"
  State: CONFIRMING_MOOD → DELIVERY
  Clarity: 0.92
```

### 6.2 Early Exit Path

```
Turn 1:
  User: "Gợi ý nhạc buồn đi"
  Bot: "Đây là nhạc buồn cho bạn..."
  State: GREETING → DELIVERY (clarity=0.8, direct request intent)
```

### 6.3 Timeout Path

```
Turn 1:
  User: "Tôi không biết"
  State: GREETING → PROBING_DEPTH

[5 minutes pass]

Next Turn:
  State: TIMEOUT, session ended
```

---

## 7. API Specification

### 7.1 Endpoints

#### POST /conversation/turn

Process a conversation turn.

**Request**:
```json
{
  "message": "Hôm nay tôi buồn quá",
  "session_id": null,
  "input_type": "text",
  "client_info": {"device": "mobile"}
}
```

**Response**:
```json
{
  "session_id": "abc-123-def",
  "turn_number": 1,
  "bot_response": "Mình hiểu bạn đang buồn 💙 Bạn buồn vì chuyện gì vậy?",
  "response_type": "probing",
  "detected_mood": "sad",
  "detected_intensity": 0.7,
  "clarity_score": 0.35,
  "current_state": "PROBING_DEPTH",
  "should_recommend": false,
  "processing_time_ms": 120
}
```

#### POST /conversation/start

Start a new session with optional greeting.

#### GET /conversation/session/{session_id}

Get session status and context.

#### POST /conversation/end/{session_id}

End session manually.

#### GET /conversation/recommend/{session_id}

Get enriched request data for recommendation pipeline.

---

## 8. Integration Guide

### 8.1 Integration with ChatOrchestrator

The conversation system integrates with the existing recommendation pipeline via:

```python
# In ChatOrchestrator
def process_enriched_request(self, user_id, enriched_data, session_id, limit):
    """
    Process accumulated emotional context from conversation.
    """
    # Extract mood data
    mood = enriched_data['final_mood']
    intensity = enriched_data['final_intensity']
    context = enriched_data['context']
    
    # Get candidates with context awareness
    candidates = self._get_candidates_enriched(
        mood=mood,
        intensity=intensity,
        valence=enriched_data['valence'],
        arousal=enriched_data['arousal'],
        context=context
    )
    
    # Run standard pipeline
    personalized = self._personalize(candidates, user_id, mood)
    curated = self._curate_playlist(personalized, mood)
    
    return ChatResponse(songs=curated)
```

### 8.2 Frontend Integration

```python
# In Flet frontend
class ConversationScreen:
    def __init__(self):
        self.session_id = None
        self.api = ConversationAPI()
    
    async def send_message(self, text):
        response = await self.api.process_turn(
            message=text,
            session_id=self.session_id
        )
        
        self.session_id = response.session_id
        self.display_response(response.bot_response)
        
        if response.should_recommend:
            recommendations = await self.api.get_recommendations(
                self.session_id
            )
            self.display_songs(recommendations)
```

---

## 9. CDIO Phase Mapping

### 9.1 CDIO Framework Overview

The Multi-Turn Conversation System follows the CDIO (Conceive, Design, Implement, Operate) framework:

| Phase | Focus | Deliverables |
|-------|-------|--------------|
| **C - Conceive** | Problem understanding, requirements | System requirements, user stories |
| **D - Design** | Architecture, component design | Schema, FSM, API spec |
| **I - Implement** | Code development, testing | Python modules, tests |
| **O - Operate** | Deployment, monitoring | Metrics, logging, maintenance |

### 9.2 Phase Details

#### Conceive (C) - Requirements Analysis

**Problem Statement**:
- Single-turn mood detection lacks depth
- Users cannot elaborate on emotions
- Context (activity, time) not considered
- No conversation continuity

**Requirements Identified**:

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | Multi-turn dialogue support | HIGH |
| R2 | Emotional depth probing | HIGH |
| R3 | Context-aware recommendations | MEDIUM |
| R4 | Session persistence | HIGH |
| R5 | Idempotent request handling | MEDIUM |
| R6 | Graceful degradation | MEDIUM |

**User Stories**:
1. As a user, I want to describe my mood in multiple messages so the bot understands me better
2. As a user, I want the bot to ask follow-up questions when my mood description is vague
3. As a user, I want my conversation context preserved if I switch devices

#### Design (D) - System Architecture

**Architecture Decisions**:

| Decision | Rationale |
|----------|-----------|
| FSM for dialogue | Predictable flow, easy to test |
| SQLite persistence | Lightweight, existing infrastructure |
| Weighted clarity formula | Combines multiple confidence signals |
| Repository pattern | Separation of data access |
| Session-based tracking | Natural conversation unit |

**Component Mapping**:

```
Requirement → Component(s)
─────────────────────────────
R1 (Multi-turn) → DialogueFSM, SessionStore, ConversationTurn
R2 (Depth probing) → ProbeQuestionBank, ClarificationStrategyEngine
R3 (Context) → ContextSignalExtractor, EmotionalContext
R4 (Persistence) → SessionStore, conversation_sessions table
R5 (Idempotency) → idempotency_keys table, hash-based keys
R6 (Degradation) → try/catch wrappers, fallback responses
```

#### Implement (I) - Development

**Module Implementation Order**:

1. **types.py** - Data classes and enums (foundation)
2. **state_machine.py** - DialogueFSM (core flow logic)
3. **emotion_tracker.py** - Signal accumulation
4. **clarity_scorer.py** - Understanding confidence
5. **intent_classifier.py** - User intent detection
6. **strategy_engine.py** - Question strategy
7. **question_bank.py** - Probing questions
8. **session_store.py** - Persistence layer
9. **context_extractor.py** - Context signals
10. **manager.py** - Main orchestrator
11. **conversation.py** - API endpoints
12. **chat_orchestrator.py** - Integration methods

**Test Coverage Targets**:

| Component | Coverage Target |
|-----------|-----------------|
| DialogueFSM | 95% (all transitions) |
| EmotionClarityModel | 90% (formula verification) |
| IntentClassifier | 85% (pattern matching) |
| SessionStore | 90% (CRUD operations) |
| ConversationManager | 80% (integration) |

#### Operate (O) - Deployment & Monitoring

**Metrics to Monitor**:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Average clarity score | > 0.70 | < 0.50 |
| Turns to recommendation | < 3 | > 5 |
| Session completion rate | > 80% | < 60% |
| Intent classification accuracy | > 85% | < 70% |
| Response latency (p95) | < 200ms | > 500ms |

**Logging Strategy**:

```python
# Structured logging points
logger.info("session_created", extra={
    "session_id": session.session_id,
    "user_id": user_id,
})

logger.info("turn_processed", extra={
    "session_id": session.session_id,
    "turn_number": turn.turn_number,
    "intent": turn.intent.name,
    "clarity_delta": turn.clarity_delta,
    "processing_time_ms": turn.processing_time_ms,
})

logger.info("state_transition", extra={
    "session_id": session.session_id,
    "from_state": old_state.name,
    "to_state": new_state.name,
    "guard_results": guards,
})
```

**Maintenance Tasks**:

| Task | Frequency |
|------|-----------|
| Cleanup expired sessions | Hourly |
| Analyze intent accuracy | Weekly |
| Review question effectiveness | Monthly |
| Update question bank | Quarterly |

### 9.3 CDIO Learning Outcomes

| Outcome | Evidence |
|---------|----------|
| Systems thinking | Multi-component architecture design |
| Technical depth | FSM design, clarity scoring formula |
| Implementation skills | 12+ Python modules |
| Professional practice | Idempotency, logging, metrics |

---

## Appendix A: File Structure

```
backend/
├── services/
│   ├── conversation/
│   │   ├── __init__.py          # Package exports
│   │   ├── types.py             # Data classes and enums
│   │   ├── state_machine.py     # DialogueFSM
│   │   ├── emotion_tracker.py   # EmotionDepthTracker
│   │   ├── clarity_scorer.py    # EmotionClarityModel
│   │   ├── intent_classifier.py # IntentClassifier
│   │   ├── strategy_engine.py   # ClarificationStrategyEngine
│   │   ├── question_bank.py     # ProbeQuestionBank
│   │   ├── session_store.py     # SessionStore
│   │   ├── context_extractor.py # ContextSignalExtractor
│   │   └── manager.py           # ConversationManager
│   └── chat_orchestrator.py     # Updated with integration
├── api/v1/
│   └── conversation.py          # API endpoints
└── src/database/migrations/
    └── migrate_conversation_v3.py  # Schema migration
```

---

## Appendix B: Configuration

```python
# Default configuration values
SESSION_TIMEOUT_SECONDS = 300      # 5 minutes
MAX_TURNS_PER_SESSION = 5          # Maximum dialogue turns
CLARITY_THRESHOLD = 0.75           # Minimum clarity for recommendation
MIN_CONFIDENCE_THRESHOLD = 0.3     # Minimum mood detection confidence
IDEMPOTENCY_KEY_EXPIRY_SECONDS = 60  # Idempotency cache TTL
```

---

*Document End*
