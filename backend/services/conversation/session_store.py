"""
=============================================================================
MULTI-TURN CONVERSATION SYSTEM - SESSION STORE
=============================================================================

Persistence layer for conversation sessions and turns.

The SessionStore provides:
- Session creation and retrieval
- Turn persistence
- Idempotency key management
- Session cleanup for expired sessions

Supports SQLite backend with optional Redis caching (future).

Author: MusicMoodBot Team
Version: 3.0.0
=============================================================================
"""

from __future__ import annotations

import os
import json
import uuid
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from .types import (
    ConversationSession,
    ConversationTurn,
    EmotionalContext,
    DialogueState,
    InputType,
    ResponseType,
    SESSION_TIMEOUT_SECONDS,
    IDEMPOTENCY_KEY_EXPIRY_SECONDS,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), 
    "..", "..", "src", "database", "music.db"
)


# =============================================================================
# SESSION STORE
# =============================================================================

class SessionStore:
    """
    Persistence layer for conversation sessions.
    
    Handles:
    - Creating new sessions
    - Loading existing sessions
    - Saving turns
    - Managing idempotency keys
    - Cleaning up expired sessions
    
    Usage:
        store = SessionStore()
        
        # Create session
        session = store.create_session(user_id=123)
        
        # Save turn
        store.save_turn(session, turn)
        
        # Load session
        session = store.get_session(session_id)
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize session store.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or os.environ.get("MMB_DB_PATH", DEFAULT_DB_PATH)
    
    @contextmanager
    def _connection(self):
        """Get database connection context."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()
    
    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        """Check if table exists."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None
    
    # =========================================================================
    # SESSION OPERATIONS
    # =========================================================================
    
    def create_session(self, user_id: int,
                       max_turns: int = 5,
                       client_info: Optional[Dict] = None) -> ConversationSession:
        """
        Create a new conversation session.
        
        Args:
            user_id: User ID
            max_turns: Maximum turns allowed
            client_info: Optional client metadata
            
        Returns:
            New ConversationSession
        """
        session_id = str(uuid.uuid4())
        now = datetime.now()
        expires_at = now + timedelta(seconds=SESSION_TIMEOUT_SECONDS)
        
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            state=DialogueState.GREETING,
            started_at=now,
            last_activity_at=now,
            expires_at=expires_at,
            max_turns=max_turns,
            client_info=client_info or {},
        )
        
        # Persist to database
        self._save_session(session)
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session
    
    def _save_session(self, session: ConversationSession):
        """Save session to database."""
        with self._connection() as conn:
            if not self._table_exists(conn, 'conversation_sessions'):
                logger.warning("conversation_sessions table does not exist. Session will not be persisted.")
                return
            
            context_json = json.dumps(session.emotional_context.to_dict())
            client_json = json.dumps(session.client_info)
            
            conn.execute("""
                INSERT OR REPLACE INTO conversation_sessions (
                    session_id, user_id, state, started_at, last_activity_at,
                    expires_at, ended_at, turn_count, max_turns,
                    final_mood, final_intensity, final_confidence,
                    context_snapshot, is_active, early_exit_reason, client_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.state.name if session.state else 'GREETING',
                session.started_at.isoformat(),
                session.last_activity_at.isoformat(),
                session.expires_at.isoformat() if session.expires_at else None,
                session.ended_at.isoformat() if session.ended_at else None,
                session.turn_count,
                session.max_turns,
                session.final_mood,
                session.final_intensity,
                session.final_confidence,
                context_json,
                1 if session.is_active else 0,
                session.early_exit_reason,
                client_json,
            ))
            conn.commit()
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        Load session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            ConversationSession or None if not found
        """
        with self._connection() as conn:
            if not self._table_exists(conn, 'conversation_sessions'):
                return None
            
            cursor = conn.execute(
                "SELECT * FROM conversation_sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_session(dict(row), conn)
    
    def _row_to_session(self, row: Dict, conn: sqlite3.Connection) -> ConversationSession:
        """Convert database row to ConversationSession."""
        # Parse emotional context
        context = EmotionalContext()
        if row.get('context_snapshot'):
            try:
                context_data = json.loads(row['context_snapshot'])
                context = EmotionalContext.from_dict(context_data)
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Parse client info
        client_info = {}
        if row.get('client_info'):
            try:
                client_info = json.loads(row['client_info'])
            except json.JSONDecodeError:
                pass
        
        # Parse state
        state = DialogueState.GREETING
        if row.get('state'):
            try:
                state = DialogueState[row['state']]
            except KeyError:
                pass
        
        session = ConversationSession(
            session_id=row['session_id'],
            user_id=row['user_id'],
            state=state,
            started_at=datetime.fromisoformat(row['started_at']) if row.get('started_at') else datetime.now(),
            last_activity_at=datetime.fromisoformat(row['last_activity_at']) if row.get('last_activity_at') else datetime.now(),
            expires_at=datetime.fromisoformat(row['expires_at']) if row.get('expires_at') else None,
            ended_at=datetime.fromisoformat(row['ended_at']) if row.get('ended_at') else None,
            turn_count=row.get('turn_count', 0),
            max_turns=row.get('max_turns', 5),
            final_mood=row.get('final_mood'),
            final_intensity=row.get('final_intensity'),
            final_confidence=row.get('final_confidence', 0.0),
            emotional_context=context,
            is_active=bool(row.get('is_active', 1)),
            early_exit_reason=row.get('early_exit_reason'),
            client_info=client_info,
        )
        
        # Load turns
        session.turns = self._load_turns(conn, session.session_id)
        
        return session
    
    def get_active_session(self, user_id: int) -> Optional[ConversationSession]:
        """
        Get active session for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Active ConversationSession or None
        """
        with self._connection() as conn:
            if not self._table_exists(conn, 'conversation_sessions'):
                return None
            
            cursor = conn.execute("""
                SELECT * FROM conversation_sessions 
                WHERE user_id = ? AND is_active = 1
                ORDER BY last_activity_at DESC
                LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            session = self._row_to_session(dict(row), conn)
            
            # Check if expired
            if session.expires_at and datetime.now() > session.expires_at:
                self.end_session(session.session_id, reason='timeout')
                return None
            
            return session
    
    def update_session(self, session: ConversationSession):
        """
        Update session in database.
        
        Args:
            session: Session to update
        """
        session.last_activity_at = datetime.now()
        self._save_session(session)
    
    def end_session(self, session_id: str, reason: Optional[str] = None):
        """
        End a session.
        
        Args:
            session_id: Session ID
            reason: Optional end reason
        """
        with self._connection() as conn:
            if not self._table_exists(conn, 'conversation_sessions'):
                return
            
            conn.execute("""
                UPDATE conversation_sessions 
                SET is_active = 0, ended_at = ?, early_exit_reason = ?, state = 'ENDED'
                WHERE session_id = ?
            """, (datetime.now().isoformat(), reason, session_id))
            conn.commit()
        
        logger.info(f"Ended session {session_id}: {reason}")
    
    # =========================================================================
    # TURN OPERATIONS
    # =========================================================================
    
    def save_turn(self, session: ConversationSession, turn: ConversationTurn) -> int:
        """
        Save a conversation turn.
        
        Args:
            session: Parent session
            turn: Turn to save
            
        Returns:
            Turn ID
        """
        with self._connection() as conn:
            if not self._table_exists(conn, 'conversation_turns'):
                logger.warning("conversation_turns table does not exist. Turn will not be persisted.")
                return 0
            
            # Serialize signals
            emotional_json = json.dumps(turn.emotional_signals.to_dict()) if turn.emotional_signals else None
            context_json = json.dumps(turn.context_signals.to_dict()) if turn.context_signals else None
            keywords_json = json.dumps(turn.keywords_matched) if turn.keywords_matched else None
            
            cursor = conn.execute("""
                INSERT INTO conversation_turns (
                    session_id, turn_number, user_input, input_type,
                    detected_mood, detected_intensity, mood_confidence, keywords_matched,
                    intent, intent_confidence,
                    context_signals, emotional_signals,
                    bot_response, response_type, question_asked,
                    state_before, state_after,
                    clarity_score_before, clarity_score_after, clarity_delta,
                    processing_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                turn.turn_number,
                turn.user_input,
                turn.input_type.value if turn.input_type else 'text',
                turn.detected_mood,
                turn.detected_intensity,
                turn.mood_confidence,
                keywords_json,
                turn.intent.name if turn.intent else None,
                turn.intent_confidence,
                context_json,
                emotional_json,
                turn.bot_response,
                turn.response_type.value if turn.response_type else 'probing',
                turn.question_asked,
                turn.state_before.name if turn.state_before else 'GREETING',
                turn.state_after.name if turn.state_after else 'GREETING',
                turn.clarity_score_before,
                turn.clarity_score_after,
                turn.clarity_delta,
                turn.processing_time_ms,
            ))
            conn.commit()
            
            turn_id = cursor.lastrowid
            turn.turn_id = turn_id
            
            # Update session
            session.add_turn(turn)
            self.update_session(session)
            
            return turn_id
    
    def _load_turns(self, conn: sqlite3.Connection, session_id: str) -> List[ConversationTurn]:
        """Load turns for a session."""
        if not self._table_exists(conn, 'conversation_turns'):
            return []
        
        cursor = conn.execute("""
            SELECT * FROM conversation_turns 
            WHERE session_id = ?
            ORDER BY turn_number
        """, (session_id,))
        
        turns = []
        for row in cursor.fetchall():
            turn = self._row_to_turn(dict(row))
            turns.append(turn)
        
        return turns
    
    def _row_to_turn(self, row: Dict) -> ConversationTurn:
        """Convert database row to ConversationTurn."""
        from .types import EmotionalSignals, ContextSignals
        
        # Parse JSON fields
        emotional_signals = None
        if row.get('emotional_signals'):
            try:
                data = json.loads(row['emotional_signals'])
                emotional_signals = EmotionalSignals.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass
        
        context_signals = None
        if row.get('context_signals'):
            try:
                data = json.loads(row['context_signals'])
                context_signals = ContextSignals.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass
        
        keywords = []
        if row.get('keywords_matched'):
            try:
                keywords = json.loads(row['keywords_matched'])
            except json.JSONDecodeError:
                pass
        
        # Parse enums
        from .types import Intent
        intent = None
        if row.get('intent'):
            try:
                intent = Intent[row['intent']]
            except KeyError:
                pass
        
        input_type = InputType.TEXT
        if row.get('input_type'):
            try:
                input_type = InputType(row['input_type'])
            except ValueError:
                pass
        
        response_type = ResponseType.PROBING
        if row.get('response_type'):
            try:
                response_type = ResponseType(row['response_type'])
            except ValueError:
                pass
        
        state_before = DialogueState.GREETING
        if row.get('state_before'):
            try:
                state_before = DialogueState[row['state_before']]
            except KeyError:
                pass
        
        state_after = DialogueState.GREETING
        if row.get('state_after'):
            try:
                state_after = DialogueState[row['state_after']]
            except KeyError:
                pass
        
        return ConversationTurn(
            turn_id=row.get('turn_id'),
            session_id=row.get('session_id', ''),
            turn_number=row.get('turn_number', 0),
            user_input=row.get('user_input', ''),
            input_type=input_type,
            detected_mood=row.get('detected_mood'),
            detected_intensity=row.get('detected_intensity'),
            mood_confidence=row.get('mood_confidence', 0.0),
            keywords_matched=keywords,
            intent=intent,
            intent_confidence=row.get('intent_confidence', 0.0),
            emotional_signals=emotional_signals,
            context_signals=context_signals,
            bot_response=row.get('bot_response', ''),
            response_type=response_type,
            question_asked=row.get('question_asked'),
            state_before=state_before,
            state_after=state_after,
            clarity_score_before=row.get('clarity_score_before', 0.0),
            clarity_score_after=row.get('clarity_score_after', 0.0),
            clarity_delta=row.get('clarity_delta', 0.0),
            processing_time_ms=row.get('processing_time_ms', 0),
        )
    
    # =========================================================================
    # IDEMPOTENCY
    # =========================================================================
    
    def check_idempotency(self, key: str) -> Optional[Dict]:
        """
        Check if idempotency key exists.
        
        Args:
            key: Idempotency key (hash of session + turn + input)
            
        Returns:
            Cached result if exists, None otherwise
        """
        with self._connection() as conn:
            if not self._table_exists(conn, 'idempotency_keys'):
                return None
            
            cursor = conn.execute("""
                SELECT result_json FROM idempotency_keys
                WHERE key = ? AND expires_at > ?
            """, (key, datetime.now().isoformat()))
            
            row = cursor.fetchone()
            if row and row['result_json']:
                try:
                    return json.loads(row['result_json'])
                except json.JSONDecodeError:
                    pass
        
        return None
    
    def save_idempotency(self, key: str, session_id: str,
                         turn_id: int, result: Dict):
        """
        Save idempotency key with result.
        
        Args:
            key: Idempotency key
            session_id: Session ID
            turn_id: Turn ID
            result: Result to cache
        """
        with self._connection() as conn:
            if not self._table_exists(conn, 'idempotency_keys'):
                return
            
            expires_at = datetime.now() + timedelta(seconds=IDEMPOTENCY_KEY_EXPIRY_SECONDS)
            
            conn.execute("""
                INSERT OR REPLACE INTO idempotency_keys (key, session_id, turn_id, result_json, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (key, session_id, turn_id, json.dumps(result), expires_at.isoformat()))
            conn.commit()
    
    def generate_idempotency_key(self, session_id: str, turn_number: int, user_input: str) -> str:
        """
        Generate idempotency key from parameters.
        
        Args:
            session_id: Session ID
            turn_number: Turn number
            user_input: User input text
            
        Returns:
            Idempotency key string
        """
        import hashlib
        content = f"{session_id}:{turn_number}:{user_input}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    # =========================================================================
    # CLEANUP
    # =========================================================================
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions and idempotency keys.
        
        Returns:
            Number of sessions cleaned up
        """
        count = 0
        now = datetime.now().isoformat()
        
        with self._connection() as conn:
            # End expired sessions
            if self._table_exists(conn, 'conversation_sessions'):
                cursor = conn.execute("""
                    UPDATE conversation_sessions 
                    SET is_active = 0, ended_at = ?, state = 'TIMEOUT', early_exit_reason = 'timeout'
                    WHERE is_active = 1 AND expires_at < ?
                """, (now, now))
                count = cursor.rowcount
            
            # Delete old idempotency keys
            if self._table_exists(conn, 'idempotency_keys'):
                conn.execute("DELETE FROM idempotency_keys WHERE expires_at < ?", (now,))
            
            conn.commit()
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")
        
        return count
    
    def get_user_session_count(self, user_id: int) -> int:
        """Get total session count for user."""
        with self._connection() as conn:
            if not self._table_exists(conn, 'conversation_sessions'):
                return 0
            
            cursor = conn.execute(
                "SELECT COUNT(*) FROM conversation_sessions WHERE user_id = ?",
                (user_id,)
            )
            return cursor.fetchone()[0]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_session_store(db_path: Optional[str] = None) -> SessionStore:
    """
    Create a SessionStore instance.
    
    Args:
        db_path: Optional database path
        
    Returns:
        SessionStore instance
    """
    return SessionStore(db_path)
