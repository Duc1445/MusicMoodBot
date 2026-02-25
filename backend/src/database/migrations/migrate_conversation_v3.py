"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - DATABASE MIGRATION V3
=============================================================================

Migration Script for MusicMoodBot Multi-Turn Conversation System

This script implements the database schema changes required for the 
multi-turn conversation architecture as specified in the system design document.

Migration Version: 3.0.0
Author: MusicMoodBot Team
Date: 2025-02-25

SCHEMA CHANGES:
1. NEW TABLES:
   - conversation_sessions: Track multi-turn conversation sessions
   - conversation_turns: Store individual conversation turns with emotional signals
   - emotional_contexts: Accumulated emotional state per session
   - probing_questions: Question bank with usage tracking
   - idempotency_keys: Prevent duplicate turn processing

2. TABLE MODIFICATIONS:
   - recommendations: Add conversation_session_id, context_json
   - feedback: Add conversation_session_id, emotional_context_snapshot
   - users: Add conversation_style, probing_preference

3. CLEANUP (deferred):
   - Backup and optionally drop: chat_history, recommendation_history, user_preferences_old

USAGE:
    python -m backend.src.database.migrations.migrate_conversation_v3

=============================================================================
"""

from __future__ import annotations

import os
import sys
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Tuple
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default database path
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "music.db"
)

# Migration version tracking
MIGRATION_VERSION = "3.0.0"
MIGRATION_NAME = "multi_turn_conversation_system"


# =============================================================================
# DATABASE CONNECTION UTILITIES
# =============================================================================

@contextmanager
def get_connection(db_path: Optional[str] = None):
    """Get database connection with Row factory and WAL mode."""
    path = db_path or os.environ.get("MMB_DB_PATH", DEFAULT_DB_PATH)
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def execute_sql(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute SQL with error handling and logging."""
    try:
        cursor = conn.execute(sql, params)
        return cursor
    except sqlite3.Error as e:
        logger.error(f"SQL Error: {e}")
        logger.error(f"SQL: {sql[:200]}...")
        raise


# =============================================================================
# SCHEMA AUDIT - REDUNDANCY ANALYSIS
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SCHEMA REDUNDANCY MAP                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  chat_history ──────┐                                                       │
│    (mood, song_id)  │                                                       │
│                     ├──► MERGE INTO listening_history                       │
│  listening_history ─┘                                                       │
│    (mood, song_id, session_id, input_text)                                 │
│                                                                             │
│  recommendation_history ───┐                                                │
│    (song_id, session_id)   │                                               │
│                            ├──► MERGE INTO recommendations                  │
│  recommendations ──────────┘                                                │
│    (user_id, song_id, mood)                                                │
│                                                                             │
│  user_preferences_old ──────► DELETE (backup first)                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Tables That Must Remain Unchanged:
| Table         | Reason                                                      |
|---------------|-------------------------------------------------------------|
| songs         | Core song catalog; 40+ audio features; no modification     |
| users         | Auth foundation; only add optional fields                  |
| feedback      | Training data for PreferenceModel; critical for ML pipeline|
| user_preferences | Dynamic preference weights; used by recommendation engine|
| playlists, playlist_songs, playlist_follows | Playlist management system  |
"""


SCHEMA_AUDIT = {
    "keep_unchanged": [
        "songs",
        "playlists", 
        "playlist_songs",
        "playlist_follows"
    ],
    "modify": [
        "users",
        "recommendations",
        "feedback"
    ],
    "backup_and_cleanup": [
        "chat_history",
        "recommendation_history",
        "user_preferences_old"
    ],
    "create_new": [
        "conversation_sessions",
        "conversation_turns",
        "emotional_contexts",
        "probing_questions",
        "idempotency_keys",
        "migration_history"
    ]
}


# =============================================================================
# MIGRATION TRACKING TABLE
# =============================================================================

CREATE_MIGRATION_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS migration_history (
    migration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT,
    rollback_sql TEXT,
    status TEXT DEFAULT 'applied' CHECK(status IN ('applied', 'rolled_back', 'failed'))
);
"""


# =============================================================================
# NEW TABLES DDL
# =============================================================================

CREATE_CONVERSATION_SESSIONS_TABLE = """
-- =============================================================================
-- TABLE: conversation_sessions
-- Purpose: Track multi-turn conversation sessions
-- =============================================================================
CREATE TABLE IF NOT EXISTS conversation_sessions (
    -- Primary key
    session_id TEXT PRIMARY KEY,                    -- UUID format: uuid4()
    
    -- Foreign keys
    user_id INTEGER NOT NULL,                       -- Links to users.user_id
    
    -- Session state
    state TEXT NOT NULL DEFAULT 'GREETING'          -- FSM state (DialogueState enum)
        CHECK(state IN (
            'GREETING', 'PROBING_MOOD', 'PROBING_INTENSITY', 
            'PROBING_CONTEXT', 'CONFIRMING', 'RECOMMENDING', 
            'FEEDBACK', 'ENDED', 'TIMEOUT', 'ABORTED'
        )),
    
    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,                           -- TTL for session cleanup
    ended_at TIMESTAMP,
    
    -- Session metadata
    turn_count INTEGER DEFAULT 0,
    max_turns INTEGER DEFAULT 5,                    -- Configurable max turns
    
    -- Accumulated context (JSON snapshots)
    final_mood TEXT,                                -- Confirmed mood for recommendation
    final_intensity TEXT,                           -- Confirmed intensity
    final_confidence REAL,                          -- Final clarity score
    context_snapshot TEXT,                          -- JSON: Full EmotionalContext
    
    -- Session flags
    is_active INTEGER DEFAULT 1,                    -- Boolean: 1=active, 0=ended
    early_exit_reason TEXT,                         -- 'user_abort', 'timeout', 'max_turns', 'confident'
    
    -- Metadata
    client_info TEXT,                               -- JSON: client type, version, etc.
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for conversation_sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_active 
    ON conversation_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_expires 
    ON conversation_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_state 
    ON conversation_sessions(state) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity 
    ON conversation_sessions(last_activity_at DESC);
"""


CREATE_CONVERSATION_TURNS_TABLE = """
-- =============================================================================
-- TABLE: conversation_turns
-- Purpose: Store individual conversation turns with emotional signals
-- =============================================================================
CREATE TABLE IF NOT EXISTS conversation_turns (
    -- Primary key
    turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign keys
    session_id TEXT NOT NULL,                       -- Links to conversation_sessions
    
    -- Turn sequence
    turn_number INTEGER NOT NULL,                   -- 0-indexed turn in session
    
    -- User input
    user_input TEXT NOT NULL,                       -- Raw user text
    input_type TEXT DEFAULT 'text'                  -- 'text', 'chip', 'voice'
        CHECK(input_type IN ('text', 'chip', 'voice', 'correction', 'confirmation')),
    
    -- Detected signals (from NLP/ML)
    detected_mood TEXT,                             -- e.g., 'Buồn', 'Vui'
    detected_intensity TEXT,                        -- 'Nhẹ', 'Vừa', 'Mạnh'
    mood_confidence REAL,                           -- 0.0 - 1.0
    keywords_matched TEXT,                          -- JSON array of matched keywords
    
    -- Classification
    intent TEXT,                                    -- IntentClassifier output
    intent_confidence REAL,                         -- 0.0 - 1.0
    
    -- Contextual signals (JSON)
    context_signals TEXT,                           -- JSON: time_of_day, activity, etc.
    emotional_signals TEXT,                         -- JSON: EmotionalSignals snapshot
    
    -- Bot response
    bot_response TEXT,                              -- What the bot said
    response_type TEXT                              -- 'probing', 'confirmation', 'recommendation'
        CHECK(response_type IN (
            'greeting', 'probing', 'confirmation', 
            'recommendation', 'error', 'clarification'
        )),
    question_asked TEXT,                            -- Question ID if probing
    
    -- State transition
    state_before TEXT,                              -- FSM state before this turn
    state_after TEXT,                               -- FSM state after this turn
    
    -- Clarity metrics (for analysis)
    clarity_score_before REAL,                      -- Clarity before this turn
    clarity_score_after REAL,                       -- Clarity after this turn
    clarity_delta REAL,                             -- Change in clarity
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,                     -- How long to process this turn
    
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id) ON DELETE CASCADE
);

-- Indexes for conversation_turns
CREATE INDEX IF NOT EXISTS idx_turns_session 
    ON conversation_turns(session_id, turn_number);
CREATE INDEX IF NOT EXISTS idx_turns_mood 
    ON conversation_turns(detected_mood);
CREATE INDEX IF NOT EXISTS idx_turns_intent 
    ON conversation_turns(intent);
CREATE INDEX IF NOT EXISTS idx_turns_created 
    ON conversation_turns(created_at DESC);
"""


CREATE_EMOTIONAL_CONTEXTS_TABLE = """
-- =============================================================================
-- TABLE: emotional_contexts
-- Purpose: Accumulated emotional state per session
-- =============================================================================
CREATE TABLE IF NOT EXISTS emotional_contexts (
    -- Primary key
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign keys
    session_id TEXT NOT NULL UNIQUE,                -- One context per session
    
    -- Primary mood detection
    primary_mood TEXT,                              -- Current best mood guess
    primary_intensity TEXT,                         -- Current intensity
    mood_confidence REAL DEFAULT 0.0,               -- Confidence in primary_mood
    
    -- Mood history (JSON array)
    mood_history TEXT,                              -- JSON: [{mood, confidence, turn}]
    
    -- Emotional signals aggregate
    valence_estimate REAL,                          -- -1.0 to 1.0 (negative to positive)
    arousal_estimate REAL,                          -- 0.0 to 1.0 (calm to excited)
    
    -- Context factors (JSON)
    time_context TEXT,                              -- JSON: time_of_day, day_of_week
    activity_context TEXT,                          -- JSON: working, relaxing, commuting
    social_context TEXT,                            -- JSON: alone, with_friends, etc.
    
    -- Clarity components (for EmotionClarityModel)
    mood_specified INTEGER DEFAULT 0,               -- Boolean: mood explicitly stated
    intensity_specified INTEGER DEFAULT 0,          -- Boolean: intensity stated
    context_richness REAL DEFAULT 0.0,              -- 0.0 - 1.0
    consistency_score REAL DEFAULT 1.0,             -- 0.0 - 1.0 (mood stability)
    
    -- Accumulated keywords/phrases
    all_keywords TEXT,                              -- JSON array of all matched keywords
    
    -- Flags
    requires_clarification INTEGER DEFAULT 1,       -- Boolean
    clarification_attempts INTEGER DEFAULT 0,       -- How many times we've asked
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id) ON DELETE CASCADE
);

-- Index for emotional_contexts
CREATE INDEX IF NOT EXISTS idx_emotional_contexts_session 
    ON emotional_contexts(session_id);
"""


CREATE_PROBING_QUESTIONS_TABLE = """
-- =============================================================================
-- TABLE: probing_questions
-- Purpose: Question bank with usage tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS probing_questions (
    -- Primary key
    question_id TEXT PRIMARY KEY,                   -- e.g., 'mood_general_01'
    
    -- Question content
    question_text_vi TEXT NOT NULL,                 -- Vietnamese version
    question_text_en TEXT,                          -- English version (optional)
    
    -- Classification
    category TEXT NOT NULL                          -- 'mood', 'intensity', 'context', 'confirmation'
        CHECK(category IN ('mood', 'intensity', 'context', 'confirmation', 'activity', 'time')),
    target_state TEXT,                              -- Target FSM state after asking
    
    -- Usage conditions (JSON)
    conditions TEXT,                                -- JSON: when to use this question
    exclude_after_moods TEXT,                       -- JSON: don't ask if these moods detected
    
    -- Response mapping (JSON)
    response_mappings TEXT,                         -- JSON: keyword -> mood/intensity mappings
    
    -- Priority and ordering
    priority INTEGER DEFAULT 5,                     -- 1=highest, 10=lowest
    depth_level INTEGER DEFAULT 1                   -- 1=surface, 2=deeper, 3=specific
        CHECK(depth_level BETWEEN 1 AND 3),
    
    -- Usage tracking
    times_asked INTEGER DEFAULT 0,
    times_helpful INTEGER DEFAULT 0,                -- Led to mood detection
    avg_clarity_gain REAL DEFAULT 0.0,              -- Average clarity improvement
    
    -- Metadata
    is_active INTEGER DEFAULT 1,                    -- Boolean: can be used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for probing_questions
CREATE INDEX IF NOT EXISTS idx_questions_category 
    ON probing_questions(category, is_active);
CREATE INDEX IF NOT EXISTS idx_questions_priority 
    ON probing_questions(priority, depth_level);
"""


CREATE_IDEMPOTENCY_KEYS_TABLE = """
-- =============================================================================
-- TABLE: idempotency_keys
-- Purpose: Prevent duplicate turn processing
-- =============================================================================
CREATE TABLE IF NOT EXISTS idempotency_keys (
    -- Primary key
    key TEXT PRIMARY KEY,                           -- Hash of session_id + turn_number + input
    
    -- Reference data
    session_id TEXT NOT NULL,
    turn_id INTEGER,                                -- Result turn_id if processed
    
    -- Result caching
    result_json TEXT,                               -- Cached response for duplicate requests
    
    -- Timing
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,                  -- Auto-cleanup after expiry
    
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id) ON DELETE CASCADE
);

-- Indexes for idempotency_keys
CREATE INDEX IF NOT EXISTS idx_idempotency_expires 
    ON idempotency_keys(expires_at);
CREATE INDEX IF NOT EXISTS idx_idempotency_session 
    ON idempotency_keys(session_id);
"""


# =============================================================================
# SCHEMA MODIFICATIONS DDL
# =============================================================================

ALTER_RECOMMENDATIONS_TABLE = """
-- =============================================================================
-- MODIFY: recommendations
-- Add conversation context
-- =============================================================================

-- Add conversation_session_id column if not exists
ALTER TABLE recommendations 
ADD COLUMN conversation_session_id TEXT 
REFERENCES conversation_sessions(session_id);

-- Add context_json column for full context snapshot
ALTER TABLE recommendations 
ADD COLUMN context_json TEXT;

-- Add created_from column to track source
ALTER TABLE recommendations 
ADD COLUMN created_from TEXT DEFAULT 'single_turn';

-- Index for conversation lookups
CREATE INDEX IF NOT EXISTS idx_recommendations_session 
    ON recommendations(conversation_session_id);
"""


ALTER_FEEDBACK_TABLE = """
-- =============================================================================
-- MODIFY: feedback
-- Add emotional context for ML training
-- =============================================================================

-- Add conversation_session_id column
ALTER TABLE feedback 
ADD COLUMN conversation_session_id TEXT 
REFERENCES conversation_sessions(session_id);

-- Add emotional_context_snapshot for ML features
ALTER TABLE feedback 
ADD COLUMN emotional_context_snapshot TEXT;

-- Add turn information
ALTER TABLE feedback 
ADD COLUMN turn_id INTEGER 
REFERENCES conversation_turns(turn_id);

-- Index for conversation lookups
CREATE INDEX IF NOT EXISTS idx_feedback_session 
    ON feedback(conversation_session_id);
"""


ALTER_USERS_TABLE = """
-- =============================================================================
-- MODIFY: users
-- Add conversation preferences
-- =============================================================================

-- Add conversation_style preference
ALTER TABLE users 
ADD COLUMN conversation_style TEXT DEFAULT 'balanced'
CHECK(conversation_style IN ('brief', 'balanced', 'detailed'));

-- Add probing depth preference (1-5)
ALTER TABLE users 
ADD COLUMN probing_preference INTEGER DEFAULT 3
CHECK(probing_preference BETWEEN 1 AND 5);

-- Add last_conversation_session for quick resume
ALTER TABLE users 
ADD COLUMN last_conversation_session TEXT;

-- Add conversation stats
ALTER TABLE users 
ADD COLUMN total_conversations INTEGER DEFAULT 0;

-- Add avg_turns_per_conversation for analysis
ALTER TABLE users 
ADD COLUMN avg_turns_per_conversation REAL DEFAULT 0.0;
"""


# =============================================================================
# CLEANUP / BACKUP DDL
# =============================================================================

BACKUP_REDUNDANT_TABLES = """
-- =============================================================================
-- CLEANUP: Backup redundant tables before removal
-- =============================================================================

-- Step 1: Backup chat_history
CREATE TABLE IF NOT EXISTS _backup_chat_history AS 
SELECT * FROM chat_history WHERE 1=0;

INSERT OR IGNORE INTO _backup_chat_history 
SELECT * FROM chat_history;

-- Step 2: Backup recommendation_history (if exists)
-- Only run if table exists (handled in migration code)

-- Step 3: Backup user_preferences_old (if exists)
-- Only run if table exists (handled in migration code)
"""


MIGRATE_CHAT_HISTORY_TO_LISTENING_HISTORY = """
-- =============================================================================
-- MIGRATE: chat_history data to listening_history (if listening_history exists)
-- =============================================================================

-- Ensure listening_history has required columns
-- (This assumes listening_history table exists with compatible schema)

INSERT INTO listening_history 
    (user_id, song_id, mood, input_type, created_at)
SELECT 
    user_id, 
    song_id, 
    mood, 
    'text' as input_type, 
    timestamp as created_at
FROM chat_history 
WHERE song_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM listening_history lh 
    WHERE lh.user_id = chat_history.user_id 
    AND lh.song_id = chat_history.song_id 
    AND lh.created_at = chat_history.timestamp
);
"""


# =============================================================================
# SEED DATA - PROBING QUESTIONS
# =============================================================================

SEED_PROBING_QUESTIONS = """
INSERT OR IGNORE INTO probing_questions 
    (question_id, question_text_vi, question_text_en, category, target_state, conditions, priority, depth_level) 
VALUES
    -- Mood probing questions (Level 1 - Surface)
    ('mood_general_01', 
     'Hôm nay bạn cảm thấy thế nào?', 
     'How are you feeling today?',
     'mood', 'PROBING_MOOD', '{"turn_number": 0}', 1, 1),
    
    ('mood_general_02', 
     'Bạn đang có tâm trạng gì lúc này?', 
     'What mood are you in right now?',
     'mood', 'PROBING_MOOD', '{"turn_number": 0}', 2, 1),
    
    ('mood_general_03', 
     'Tâm trạng của bạn hôm nay ra sao?', 
     'How would you describe your mood today?',
     'mood', 'PROBING_MOOD', '{"turn_number": 0}', 3, 1),
    
    -- Mood probing questions (Level 2 - Deeper)
    ('mood_deeper_01', 
     'Có chuyện gì khiến bạn cảm thấy như vậy không?', 
     'Is there something that makes you feel this way?',
     'mood', 'PROBING_MOOD', '{"has_mood": true}', 1, 2),
    
    ('mood_deeper_02', 
     'Bạn có thể mô tả thêm về cảm xúc hiện tại không?', 
     'Can you describe your current emotions more?',
     'mood', 'PROBING_MOOD', '{"has_mood": true, "confidence_below": 0.6}', 2, 2),
    
    -- Intensity probing questions
    ('intensity_01', 
     'Bạn đang cảm nhận điều này mạnh mẽ đến mức nào?', 
     'How strongly are you feeling this?',
     'intensity', 'PROBING_INTENSITY', '{"has_mood": true, "needs_intensity": true}', 1, 1),
    
    ('intensity_02', 
     'Cảm xúc này có mãnh liệt không hay chỉ nhẹ nhàng thôi?', 
     'Is this feeling intense or subtle?',
     'intensity', 'PROBING_INTENSITY', '{"has_mood": true, "needs_intensity": true}', 2, 1),
    
    ('intensity_03', 
     'Nếu cho điểm từ 1-10, bạn sẽ đánh giá cường độ cảm xúc này như thế nào?', 
     'On a scale of 1-10, how would you rate this feeling?',
     'intensity', 'PROBING_INTENSITY', '{"has_mood": true, "needs_intensity": true}', 3, 2),
    
    -- Context probing questions
    ('context_activity_01', 
     'Bạn đang làm gì vậy? Làm việc, thư giãn hay đang di chuyển?', 
     'What are you doing? Working, relaxing, or commuting?',
     'context', 'PROBING_CONTEXT', '{"needs_context": true}', 1, 1),
    
    ('context_activity_02', 
     'Bạn muốn nghe nhạc để tập trung làm việc hay để thư giãn?', 
     'Do you want music to focus on work or to relax?',
     'activity', 'PROBING_CONTEXT', '{"needs_context": true}', 2, 1),
    
    ('context_time_01', 
     'Đây có phải là buổi sáng để bắt đầu ngày mới không?', 
     'Is this morning to start your day?',
     'time', 'PROBING_CONTEXT', '{"needs_time_context": true}', 3, 1),
    
    ('context_social_01', 
     'Bạn đang ở một mình hay cùng bạn bè?', 
     'Are you alone or with friends?',
     'context', 'PROBING_CONTEXT', '{"needs_social_context": true}', 4, 2),
    
    -- Confirmation questions
    ('confirm_mood_01', 
     'Vậy là bạn đang muốn nghe nhạc {mood} {intensity} đúng không?', 
     'So you want to listen to {mood} {intensity} music, right?',
     'confirmation', 'CONFIRMING', '{"ready_to_confirm": true}', 1, 1),
    
    ('confirm_mood_02', 
     'Tôi hiểu bạn đang cảm thấy {mood}. Bạn muốn nhạc giúp duy trì hay thay đổi tâm trạng?', 
     'I understand you are feeling {mood}. Do you want music to maintain or change your mood?',
     'confirmation', 'CONFIRMING', '{"ready_to_confirm": true}', 2, 2),
    
    -- Early exit / Skip questions
    ('skip_01', 
     'Bạn có muốn tôi gợi ý nhạc ngay không? Hay muốn chat thêm?', 
     'Do you want me to suggest music now? Or chat more?',
     'confirmation', 'CONFIRMING', '{"can_recommend": true}', 5, 1);
"""


# =============================================================================
# MIGRATION FUNCTIONS
# =============================================================================

def check_table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def check_column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = [row['name'] for row in cursor.fetchall()]
    return column_name in columns


def safe_alter_table(conn: sqlite3.Connection, table_name: str, 
                     column_name: str, column_def: str) -> bool:
    """Safely add column to table if it doesn't exist."""
    if not check_table_exists(conn, table_name):
        logger.warning(f"Table {table_name} does not exist, skipping column add")
        return False
    
    if check_column_exists(conn, table_name, column_name):
        logger.info(f"Column {table_name}.{column_name} already exists, skipping")
        return True
    
    try:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
        logger.info(f"Added column {table_name}.{column_name}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Failed to add column {table_name}.{column_name}: {e}")
        return False


def check_migration_applied(conn: sqlite3.Connection, version: str) -> bool:
    """Check if a migration version has been applied."""
    if not check_table_exists(conn, 'migration_history'):
        return False
    
    cursor = conn.execute(
        "SELECT 1 FROM migration_history WHERE version = ? AND status = 'applied'",
        (version,)
    )
    return cursor.fetchone() is not None


def record_migration(conn: sqlite3.Connection, version: str, name: str, 
                     status: str = 'applied', rollback_sql: str = None):
    """Record migration in history table."""
    try:
        conn.execute("""
            INSERT INTO migration_history (version, name, status, rollback_sql)
            VALUES (?, ?, ?, ?)
        """, (version, name, status, rollback_sql))
        logger.info(f"Recorded migration {version}: {name} ({status})")
    except sqlite3.IntegrityError:
        # Already recorded
        conn.execute("""
            UPDATE migration_history 
            SET status = ?, applied_at = CURRENT_TIMESTAMP
            WHERE version = ?
        """, (status, version))


# =============================================================================
# MAIN MIGRATION RUNNER
# =============================================================================

class ConversationMigration:
    """
    Migration runner for Multi-Turn Conversation System.
    
    Implements the following migration steps:
    1. Create migration history table
    2. Create new conversation tables
    3. Modify existing tables
    4. Backup redundant tables
    5. Seed probing questions
    6. Create indexes
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("MMB_DB_PATH", DEFAULT_DB_PATH)
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def run(self, dry_run: bool = False) -> bool:
        """
        Execute the full migration.
        
        Args:
            dry_run: If True, only validate without applying changes
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Starting migration {MIGRATION_VERSION}: {MIGRATION_NAME}")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Dry run: {dry_run}")
        
        try:
            with get_connection(self.db_path) as conn:
                # Check if already applied
                if check_migration_applied(conn, MIGRATION_VERSION):
                    logger.info(f"Migration {MIGRATION_VERSION} already applied, skipping")
                    return True
                
                if dry_run:
                    logger.info("Dry run mode - validating only")
                    return self._validate(conn)
                
                # Start transaction
                conn.execute("BEGIN TRANSACTION")
                
                try:
                    # Step 1: Create migration history table
                    self._create_migration_history(conn)
                    
                    # Step 2: Create new tables
                    self._create_new_tables(conn)
                    
                    # Step 3: Modify existing tables
                    self._modify_existing_tables(conn)
                    
                    # Step 4: Backup redundant tables
                    self._backup_redundant_tables(conn)
                    
                    # Step 5: Seed probing questions
                    self._seed_probing_questions(conn)
                    
                    # Step 6: Create additional indexes
                    self._create_indexes(conn)
                    
                    # Record successful migration
                    record_migration(conn, MIGRATION_VERSION, MIGRATION_NAME)
                    
                    # Commit transaction
                    conn.commit()
                    logger.info(f"Migration {MIGRATION_VERSION} completed successfully")
                    return True
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Migration failed, rolling back: {e}")
                    self.errors.append(str(e))
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.errors.append(str(e))
            return False
    
    def _validate(self, conn: sqlite3.Connection) -> bool:
        """Validate migration prerequisites."""
        logger.info("Validating migration prerequisites...")
        
        # Check required tables exist
        required_tables = ['users', 'songs', 'feedback', 'recommendations']
        for table in required_tables:
            if not check_table_exists(conn, table):
                self.errors.append(f"Required table '{table}' does not exist")
        
        # Check for potential conflicts
        new_tables = SCHEMA_AUDIT['create_new']
        for table in new_tables:
            if check_table_exists(conn, table):
                self.warnings.append(f"Table '{table}' already exists")
        
        if self.errors:
            logger.error(f"Validation failed with {len(self.errors)} errors")
            for error in self.errors:
                logger.error(f"  - {error}")
            return False
        
        if self.warnings:
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        logger.info("Validation passed")
        return True
    
    def _create_migration_history(self, conn: sqlite3.Connection):
        """Step 1: Create migration history table."""
        logger.info("Step 1: Creating migration history table...")
        conn.executescript(CREATE_MIGRATION_HISTORY_TABLE)
    
    def _create_new_tables(self, conn: sqlite3.Connection):
        """Step 2: Create new conversation tables."""
        logger.info("Step 2: Creating new conversation tables...")
        
        tables_sql = [
            ("conversation_sessions", CREATE_CONVERSATION_SESSIONS_TABLE),
            ("conversation_turns", CREATE_CONVERSATION_TURNS_TABLE),
            ("emotional_contexts", CREATE_EMOTIONAL_CONTEXTS_TABLE),
            ("probing_questions", CREATE_PROBING_QUESTIONS_TABLE),
            ("idempotency_keys", CREATE_IDEMPOTENCY_KEYS_TABLE),
        ]
        
        for table_name, sql in tables_sql:
            if not check_table_exists(conn, table_name):
                logger.info(f"  Creating table: {table_name}")
                conn.executescript(sql)
            else:
                logger.info(f"  Table {table_name} already exists, skipping")
    
    def _modify_existing_tables(self, conn: sqlite3.Connection):
        """Step 3: Modify existing tables with new columns."""
        logger.info("Step 3: Modifying existing tables...")
        
        # Modify recommendations table
        safe_alter_table(conn, 'recommendations', 'conversation_session_id', 
                        'TEXT REFERENCES conversation_sessions(session_id)')
        safe_alter_table(conn, 'recommendations', 'context_json', 'TEXT')
        safe_alter_table(conn, 'recommendations', 'created_from', "TEXT DEFAULT 'single_turn'")
        
        # Modify feedback table
        safe_alter_table(conn, 'feedback', 'conversation_session_id',
                        'TEXT REFERENCES conversation_sessions(session_id)')
        safe_alter_table(conn, 'feedback', 'emotional_context_snapshot', 'TEXT')
        safe_alter_table(conn, 'feedback', 'turn_id',
                        'INTEGER REFERENCES conversation_turns(turn_id)')
        
        # Modify users table
        safe_alter_table(conn, 'users', 'conversation_style', "TEXT DEFAULT 'balanced'")
        safe_alter_table(conn, 'users', 'probing_preference', 'INTEGER DEFAULT 3')
        safe_alter_table(conn, 'users', 'last_conversation_session', 'TEXT')
        safe_alter_table(conn, 'users', 'total_conversations', 'INTEGER DEFAULT 0')
        safe_alter_table(conn, 'users', 'avg_turns_per_conversation', 'REAL DEFAULT 0.0')
    
    def _backup_redundant_tables(self, conn: sqlite3.Connection):
        """Step 4: Backup potentially redundant tables."""
        logger.info("Step 4: Backing up redundant tables...")
        
        redundant_tables = SCHEMA_AUDIT['backup_and_cleanup']
        
        for table in redundant_tables:
            if check_table_exists(conn, table):
                backup_table = f"_backup_{table}"
                if not check_table_exists(conn, backup_table):
                    logger.info(f"  Backing up {table} to {backup_table}")
                    conn.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM {table}")
                else:
                    logger.info(f"  Backup {backup_table} already exists, skipping")
    
    def _seed_probing_questions(self, conn: sqlite3.Connection):
        """Step 5: Seed probing questions."""
        logger.info("Step 5: Seeding probing questions...")
        
        # Check if questions already exist
        cursor = conn.execute("SELECT COUNT(*) FROM probing_questions")
        count = cursor.fetchone()[0]
        
        if count == 0:
            conn.executescript(SEED_PROBING_QUESTIONS)
            cursor = conn.execute("SELECT COUNT(*) FROM probing_questions")
            new_count = cursor.fetchone()[0]
            logger.info(f"  Seeded {new_count} probing questions")
        else:
            logger.info(f"  Probing questions already seeded ({count} questions)")
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """Step 6: Create additional optimization indexes."""
        logger.info("Step 6: Creating indexes...")
        
        additional_indexes = [
            # Recommendations conversation lookup
            ("idx_recommendations_session", 
             "recommendations(conversation_session_id)"),
            # Feedback conversation lookup
            ("idx_feedback_session", 
             "feedback(conversation_session_id)"),
            # Composite index for session + user active status
            ("idx_sessions_user_state", 
             "conversation_sessions(user_id, state) WHERE is_active = 1"),
        ]
        
        for idx_name, idx_def in additional_indexes:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
                logger.info(f"  Created index: {idx_name}")
            except sqlite3.Error as e:
                logger.warning(f"  Could not create index {idx_name}: {e}")
    
    def rollback(self) -> bool:
        """
        Rollback the migration.
        
        WARNING: This will drop all new tables and remove added columns.
        """
        logger.warning("Rolling back migration...")
        
        try:
            with get_connection(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                
                try:
                    # Drop new tables
                    new_tables = [
                        'idempotency_keys',
                        'probing_questions', 
                        'emotional_contexts',
                        'conversation_turns',
                        'conversation_sessions',
                    ]
                    
                    for table in new_tables:
                        if check_table_exists(conn, table):
                            logger.info(f"Dropping table: {table}")
                            conn.execute(f"DROP TABLE {table}")
                    
                    # Note: SQLite doesn't support DROP COLUMN easily
                    # Would need to recreate tables to remove columns
                    logger.warning("Note: Added columns to existing tables cannot be automatically removed in SQLite")
                    
                    # Update migration status
                    if check_table_exists(conn, 'migration_history'):
                        conn.execute("""
                            UPDATE migration_history 
                            SET status = 'rolled_back'
                            WHERE version = ?
                        """, (MIGRATION_VERSION,))
                    
                    conn.commit()
                    logger.info("Rollback completed")
                    return True
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Rollback failed: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Rollback connection failed: {e}")
            return False


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Main entry point for migration CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MusicMoodBot Multi-Turn Conversation System Migration"
    )
    parser.add_argument(
        '--db', '-d',
        help='Database path (default: music.db)',
        default=None
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate only, do not apply changes'
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback the migration'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    migration = ConversationMigration(args.db)
    
    if args.rollback:
        success = migration.rollback()
    else:
        success = migration.run(dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
