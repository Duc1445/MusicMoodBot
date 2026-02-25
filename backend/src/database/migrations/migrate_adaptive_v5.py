"""
=============================================================================
ADAPTIVE RECOMMENDATION v5.0 - DATABASE MIGRATION
=============================================================================

Migration Script for MusicMoodBot v5.0 Adaptive Recommendation System

This script implements the database schema changes required for:
- Conversation context memory
- Emotional trajectory tracking
- Session reward calculation
- Adaptive weight learning
- Cold start handling

Migration Version: 5.0.0
Author: MusicMoodBot Team
Date: 2025

SCHEMA CHANGES:
1. NEW TABLES:
   - conversation_context: Store conversation context with sliding window
   - emotional_trajectory: Track VA-space emotional trajectory
   - session_rewards: Store session reward calculations
   - user_weights: Per-user adaptive feature weights
   - weight_adjustments: History of weight adjustments
   - cold_start_status: Track user cold start progression

2. NEW INDEXES:
   - idx_conversation_context_user
   - idx_emotional_trajectory_user_timestamp
   - idx_session_rewards_user
   - idx_user_weights_user

USAGE:
    python -m backend.src.database.migrations.migrate_adaptive_v5

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

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "music.db"
)

MIGRATION_VERSION = "5.0.0"

# Default feature weights
DEFAULT_WEIGHTS = {
    "valence": 1.0,
    "energy": 1.0,
    "danceability": 1.0,
    "acousticness": 1.0,
    "instrumentalness": 1.0,
    "tempo_match": 1.0,
    "mood_match": 1.0,
    "artist_familiarity": 1.0,
    "genre_match": 1.0,
}


# =============================================================================
# SQL SCHEMA DEFINITIONS
# =============================================================================

SQL_CREATE_CONVERSATION_CONTEXT = """
CREATE TABLE IF NOT EXISTS conversation_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    turn_id INTEGER NOT NULL,
    user_input TEXT NOT NULL,
    input_type TEXT DEFAULT 'text',
    detected_mood TEXT,
    mood_confidence REAL DEFAULT 0.0,
    extracted_entities_json TEXT,
    context_modifiers_json TEXT,
    bot_response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

SQL_CREATE_EMOTIONAL_TRAJECTORY = """
CREATE TABLE IF NOT EXISTS emotional_trajectory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    valence REAL NOT NULL,
    arousal REAL NOT NULL,
    mood_label TEXT,
    source TEXT DEFAULT 'conversation',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

SQL_CREATE_SESSION_REWARDS = """
CREATE TABLE IF NOT EXISTS session_rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    song_id INTEGER NOT NULL,
    feedback_type TEXT NOT NULL,
    play_progress REAL,
    engagement_score REAL DEFAULT 0.0,
    satisfaction_score REAL DEFAULT 0.0,
    emotional_alignment REAL DEFAULT 0.0,
    total_reward REAL DEFAULT 0.0,
    context_json TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (song_id) REFERENCES songs(song_id)
);
"""

SQL_CREATE_USER_WEIGHTS = """
CREATE TABLE IF NOT EXISTS user_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    weights_json TEXT NOT NULL,
    total_adjustments INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

SQL_CREATE_WEIGHT_ADJUSTMENTS = """
CREATE TABLE IF NOT EXISTS weight_adjustments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    adjustment_type TEXT NOT NULL,
    feedback_type TEXT,
    old_weights_json TEXT,
    new_weights_json TEXT,
    delta_magnitude REAL DEFAULT 0.0,
    song_features_json TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

SQL_CREATE_COLD_START_STATUS = """
CREATE TABLE IF NOT EXISTS cold_start_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    feedback_count INTEGER DEFAULT 0,
    is_cold_start BOOLEAN DEFAULT 1,
    personalization_weight REAL DEFAULT 0.0,
    first_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
    cold_start_completed DATETIME,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

SQL_CREATE_BANDIT_STATS = """
CREATE TABLE IF NOT EXISTS bandit_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    strategy_name TEXT NOT NULL,
    alpha REAL DEFAULT 1.0,
    beta REAL DEFAULT 1.0,
    total_pulls INTEGER DEFAULT 0,
    total_reward REAL DEFAULT 0.0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, strategy_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
"""

# Index creation SQL
SQL_CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_conversation_context_user 
    ON conversation_context(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_conversation_context_session 
    ON conversation_context(session_id, turn_id);

CREATE INDEX IF NOT EXISTS idx_emotional_trajectory_user_timestamp 
    ON emotional_trajectory(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_session_rewards_user 
    ON session_rewards(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_session_rewards_session 
    ON session_rewards(session_id);

CREATE INDEX IF NOT EXISTS idx_user_weights_user 
    ON user_weights(user_id);

CREATE INDEX IF NOT EXISTS idx_weight_adjustments_user 
    ON weight_adjustments(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_cold_start_user 
    ON cold_start_status(user_id);

CREATE INDEX IF NOT EXISTS idx_bandit_stats_user 
    ON bandit_stats(user_id, strategy_name);
"""


# =============================================================================
# MIGRATION FUNCTIONS
# =============================================================================

@contextmanager
def get_db_connection(db_path: str):
    """Context manager for database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    """Check if a table exists."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def get_migration_version(db_path: str) -> Optional[str]:
    """Get current migration version from database."""
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            if not table_exists(cursor, "migration_history"):
                return None
            cursor.execute(
                "SELECT version FROM migration_history ORDER BY applied_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"Error checking migration version: {e}")
        return None


def record_migration(conn: sqlite3.Connection):
    """Record migration in history table."""
    cursor = conn.cursor()
    
    # Create migration history table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            description TEXT,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute(
        "INSERT INTO migration_history (version, description) VALUES (?, ?)",
        (MIGRATION_VERSION, "Adaptive Recommendation v5.0 - Context, Trajectory, Rewards, Weights")
    )


def run_migration(db_path: str, dry_run: bool = False) -> bool:
    """
    Run the v5.0 migration.
    
    Args:
        db_path: Path to SQLite database
        dry_run: If True, only show what would be done
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting v5.0 migration on: {db_path}")
    logger.info(f"Dry run: {dry_run}")
    
    # Check if already migrated
    current_version = get_migration_version(db_path)
    if current_version and current_version >= MIGRATION_VERSION:
        logger.info(f"Database already at version {current_version}, skipping migration")
        return True
    
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables
            tables = [
                ("conversation_context", SQL_CREATE_CONVERSATION_CONTEXT),
                ("emotional_trajectory", SQL_CREATE_EMOTIONAL_TRAJECTORY),
                ("session_rewards", SQL_CREATE_SESSION_REWARDS),
                ("user_weights", SQL_CREATE_USER_WEIGHTS),
                ("weight_adjustments", SQL_CREATE_WEIGHT_ADJUSTMENTS),
                ("cold_start_status", SQL_CREATE_COLD_START_STATUS),
                ("bandit_stats", SQL_CREATE_BANDIT_STATS),
            ]
            
            for table_name, sql in tables:
                if table_exists(cursor, table_name):
                    logger.info(f"Table {table_name} already exists, skipping")
                else:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would create table: {table_name}")
                    else:
                        logger.info(f"Creating table: {table_name}")
                        cursor.execute(sql)
            
            # Create indexes
            if not dry_run:
                logger.info("Creating indexes...")
                for sql in SQL_CREATE_INDEXES.strip().split(";"):
                    sql = sql.strip()
                    if sql:
                        try:
                            cursor.execute(sql)
                        except sqlite3.OperationalError as e:
                            # Index might already exist
                            if "already exists" not in str(e):
                                raise
            
            # Record migration
            if not dry_run:
                record_migration(conn)
                logger.info(f"Migration v{MIGRATION_VERSION} completed successfully")
            else:
                logger.info(f"[DRY RUN] Would record migration v{MIGRATION_VERSION}")
            
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def initialize_default_weights(db_path: str, user_id: int) -> bool:
    """Initialize default weights for a user."""
    import json
    
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if user already has weights
            cursor.execute(
                "SELECT id FROM user_weights WHERE user_id = ?",
                (user_id,)
            )
            if cursor.fetchone():
                return True
            
            # Insert default weights
            cursor.execute(
                """
                INSERT INTO user_weights (user_id, weights_json, total_adjustments)
                VALUES (?, ?, 0)
                """,
                (user_id, json.dumps(DEFAULT_WEIGHTS))
            )
            
            # Initialize cold start status
            cursor.execute(
                """
                INSERT OR IGNORE INTO cold_start_status 
                (user_id, feedback_count, is_cold_start, personalization_weight)
                VALUES (?, 0, 1, 0.0)
                """,
                (user_id,)
            )
            
            return True
            
    except Exception as e:
        logger.error(f"Error initializing weights for user {user_id}: {e}")
        return False


def rollback_migration(db_path: str) -> bool:
    """
    Rollback the v5.0 migration (drop new tables).
    
    WARNING: This will delete all data in these tables!
    """
    logger.warning("Rolling back v5.0 migration - THIS WILL DELETE DATA")
    
    tables_to_drop = [
        "conversation_context",
        "emotional_trajectory",
        "session_rewards",
        "user_weights",
        "weight_adjustments",
        "cold_start_status",
        "bandit_stats",
    ]
    
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            
            for table in tables_to_drop:
                if table_exists(cursor, table):
                    logger.info(f"Dropping table: {table}")
                    cursor.execute(f"DROP TABLE {table}")
            
            # Remove migration record
            cursor.execute(
                "DELETE FROM migration_history WHERE version = ?",
                (MIGRATION_VERSION,)
            )
            
            logger.info("Rollback completed")
            return True
            
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return False


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MusicMoodBot v5.0 Database Migration"
    )
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help="Path to SQLite database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback the migration (WARNING: deletes data)"
    )
    
    args = parser.parse_args()
    
    # Resolve path
    db_path = os.path.abspath(args.db_path)
    
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        sys.exit(1)
    
    if args.rollback:
        confirm = input("This will DELETE data. Type 'YES' to confirm: ")
        if confirm != "YES":
            logger.info("Rollback cancelled")
            sys.exit(0)
        success = rollback_migration(db_path)
    else:
        success = run_migration(db_path, dry_run=args.dry_run)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
