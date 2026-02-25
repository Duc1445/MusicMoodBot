"""
=============================================================================
ANALYTICS ENGINE
=============================================================================

System-wide metrics and evaluation for the recommendation system.

Metrics Categories:
==================

1. Conversation Metrics:
   - Average turns per session
   - Average clarity before recommendation
   - Session completion rate

2. Recommendation Metrics:
   - Recommendation acceptance rate
   - Like ratio
   - Skip ratio
   - Diversity score

3. System Performance:
   - Response latency
   - Error rate
   - Active users

Author: MusicMoodBot Team
Version: 3.1.0
=============================================================================
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SessionMetrics:
    """Metrics for conversation sessions."""
    
    total_sessions: int = 0
    completed_sessions: int = 0
    abandoned_sessions: int = 0
    timeout_sessions: int = 0
    
    average_turns: float = 0.0
    median_turns: float = 0.0
    max_turns: int = 0
    
    average_clarity_at_recommendation: float = 0.0
    average_session_duration_seconds: float = 0.0
    
    completion_rate: float = 0.0  # completed / total
    
    # By state breakdown
    sessions_by_final_state: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_sessions': self.total_sessions,
            'completed_sessions': self.completed_sessions,
            'abandoned_sessions': self.abandoned_sessions,
            'timeout_sessions': self.timeout_sessions,
            'average_turns': round(self.average_turns, 2),
            'median_turns': round(self.median_turns, 2),
            'max_turns': self.max_turns,
            'average_clarity_at_recommendation': round(self.average_clarity_at_recommendation, 3),
            'average_session_duration_seconds': round(self.average_session_duration_seconds, 1),
            'completion_rate': round(self.completion_rate, 3),
            'sessions_by_final_state': self.sessions_by_final_state,
        }


@dataclass
class RecommendationMetrics:
    """Metrics for recommendations."""
    
    total_recommendations: int = 0
    total_feedback: int = 0
    
    likes: int = 0
    dislikes: int = 0
    skips: int = 0
    
    like_ratio: float = 0.0      # likes / total_feedback
    dislike_ratio: float = 0.0  # dislikes / total_feedback
    skip_ratio: float = 0.0     # skips / total_feedback
    
    acceptance_rate: float = 0.0  # (likes + plays) / recommendations
    
    # Advanced metrics
    average_listen_duration_seconds: float = 0.0
    completion_rate: float = 0.0  # Songs played > 80%
    
    # By category breakdown
    feedback_by_mood: Dict[str, Dict[str, int]] = field(default_factory=dict)
    feedback_by_genre: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_recommendations': self.total_recommendations,
            'total_feedback': self.total_feedback,
            'likes': self.likes,
            'dislikes': self.dislikes,
            'skips': self.skips,
            'like_ratio': round(self.like_ratio, 3),
            'dislike_ratio': round(self.dislike_ratio, 3),
            'skip_ratio': round(self.skip_ratio, 3),
            'acceptance_rate': round(self.acceptance_rate, 3),
            'average_listen_duration_seconds': round(self.average_listen_duration_seconds, 1),
            'completion_rate': round(self.completion_rate, 3),
            'feedback_by_mood': self.feedback_by_mood,
            'feedback_by_genre': self.feedback_by_genre,
        }


@dataclass
class SystemMetrics:
    """Combined system metrics."""
    
    # Time range
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    # User metrics
    total_users: int = 0
    active_users_24h: int = 0
    active_users_7d: int = 0
    new_users_7d: int = 0
    
    # Conversation metrics
    session_metrics: SessionMetrics = field(default_factory=SessionMetrics)
    
    # Recommendation metrics
    recommendation_metrics: RecommendationMetrics = field(default_factory=RecommendationMetrics)
    
    # Performance metrics
    average_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    error_rate: float = 0.0
    
    # Content metrics
    total_songs: int = 0
    songs_recommended_at_least_once: int = 0
    catalog_coverage: float = 0.0  # recommended / total
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat(),
            },
            'users': {
                'total': self.total_users,
                'active_24h': self.active_users_24h,
                'active_7d': self.active_users_7d,
                'new_7d': self.new_users_7d,
            },
            'sessions': self.session_metrics.to_dict(),
            'recommendations': self.recommendation_metrics.to_dict(),
            'performance': {
                'average_response_time_ms': round(self.average_response_time_ms, 1),
                'p95_response_time_ms': round(self.p95_response_time_ms, 1),
                'error_rate': round(self.error_rate, 4),
            },
            'content': {
                'total_songs': self.total_songs,
                'songs_recommended': self.songs_recommended_at_least_once,
                'catalog_coverage': round(self.catalog_coverage, 3),
            },
        }


# =============================================================================
# ANALYTICS ENGINE
# =============================================================================

class AnalyticsEngine:
    """
    Analytics and metrics engine for the recommendation system.
    
    Provides:
    - Session metrics computation
    - Recommendation metrics computation
    - System-wide statistics
    - SQL-based aggregation
    
    Usage:
        engine = AnalyticsEngine(db_path)
        
        # Get all metrics
        metrics = engine.compute_system_metrics(days=7)
        
        # Get specific metrics
        session_metrics = engine.compute_session_metrics(days=7)
        rec_metrics = engine.compute_recommendation_metrics(days=7)
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize analytics engine.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or self._get_default_db_path()
    
    def _get_default_db_path(self) -> str:
        """Get default database path."""
        import os
        return os.path.join(
            os.path.dirname(__file__), 
            "..", "src", "database", "music.db"
        )
    
    @contextmanager
    def _connection(self):
        """Get database connection context."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
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
    # MAIN METRICS COMPUTATION
    # =========================================================================
    
    def compute_system_metrics(
        self,
        days: int = 7,
        end_date: datetime = None
    ) -> SystemMetrics:
        """
        Compute all system metrics for a time period.
        
        Args:
            days: Number of days to analyze
            end_date: End date (defaults to now)
            
        Returns:
            SystemMetrics with all computed values
        """
        end_date = end_date or datetime.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = SystemMetrics(
            period_start=start_date,
            period_end=end_date,
        )
        
        # Compute individual metric categories
        metrics.session_metrics = self.compute_session_metrics(days, end_date)
        metrics.recommendation_metrics = self.compute_recommendation_metrics(days, end_date)
        
        # User metrics
        user_metrics = self._compute_user_metrics(start_date, end_date)
        metrics.total_users = user_metrics.get('total', 0)
        metrics.active_users_24h = user_metrics.get('active_24h', 0)
        metrics.active_users_7d = user_metrics.get('active_7d', 0)
        metrics.new_users_7d = user_metrics.get('new_7d', 0)
        
        # Content metrics
        content_metrics = self._compute_content_metrics(start_date, end_date)
        metrics.total_songs = content_metrics.get('total_songs', 0)
        metrics.songs_recommended_at_least_once = content_metrics.get('recommended', 0)
        if metrics.total_songs > 0:
            metrics.catalog_coverage = metrics.songs_recommended_at_least_once / metrics.total_songs
        
        # Performance metrics
        perf_metrics = self._compute_performance_metrics(start_date, end_date)
        metrics.average_response_time_ms = perf_metrics.get('avg_response_ms', 0.0)
        metrics.p95_response_time_ms = perf_metrics.get('p95_response_ms', 0.0)
        metrics.error_rate = perf_metrics.get('error_rate', 0.0)
        
        return metrics
    
    def compute_session_metrics(
        self,
        days: int = 7,
        end_date: datetime = None
    ) -> SessionMetrics:
        """
        Compute conversation session metrics.
        
        SQL Queries:
        - Session counts by state
        - Turn distribution
        - Clarity scores
        - Duration statistics
        """
        end_date = end_date or datetime.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = SessionMetrics()
        
        with self._connection() as conn:
            if not self._table_exists(conn, 'conversation_sessions'):
                return metrics
            
            # Total sessions
            cursor = conn.execute("""
                SELECT COUNT(*) as total
                FROM conversation_sessions
                WHERE started_at >= ?
            """, (start_date.isoformat(),))
            row = cursor.fetchone()
            metrics.total_sessions = row['total'] if row else 0
            
            # Sessions by final state
            cursor = conn.execute("""
                SELECT state, COUNT(*) as count
                FROM conversation_sessions
                WHERE started_at >= ?
                GROUP BY state
            """, (start_date.isoformat(),))
            
            for row in cursor.fetchall():
                state = row['state'] or 'UNKNOWN'
                metrics.sessions_by_final_state[state] = row['count']
                
                # Categorize
                if state in ('ENDED', 'DELIVERY'):
                    metrics.completed_sessions += row['count']
                elif state == 'TIMEOUT':
                    metrics.timeout_sessions += row['count']
                else:
                    metrics.abandoned_sessions += row['count']
            
            # Turn statistics
            cursor = conn.execute("""
                SELECT 
                    AVG(turn_count) as avg_turns,
                    MAX(turn_count) as max_turns
                FROM conversation_sessions
                WHERE started_at >= ?
            """, (start_date.isoformat(),))
            row = cursor.fetchone()
            if row:
                metrics.average_turns = row['avg_turns'] or 0
                metrics.max_turns = row['max_turns'] or 0
            
            # Median turns (SQLite doesn't have built-in median)
            cursor = conn.execute("""
                SELECT turn_count
                FROM conversation_sessions
                WHERE started_at >= ?
                ORDER BY turn_count
            """, (start_date.isoformat(),))
            turns = [r['turn_count'] for r in cursor.fetchall()]
            if turns:
                mid = len(turns) // 2
                metrics.median_turns = turns[mid] if len(turns) % 2 == 1 else (turns[mid-1] + turns[mid]) / 2
            
            # Clarity at recommendation
            cursor = conn.execute("""
                SELECT AVG(final_confidence) as avg_clarity
                FROM conversation_sessions
                WHERE started_at >= ?
                AND state IN ('DELIVERY', 'RECOMMENDATION', 'ENDED')
                AND final_confidence IS NOT NULL
            """, (start_date.isoformat(),))
            row = cursor.fetchone()
            metrics.average_clarity_at_recommendation = row['avg_clarity'] or 0.0
            
            # Duration statistics
            cursor = conn.execute("""
                SELECT 
                    AVG(
                        CASE 
                            WHEN ended_at IS NOT NULL 
                            THEN (julianday(ended_at) - julianday(started_at)) * 86400
                            ELSE (julianday(last_activity_at) - julianday(started_at)) * 86400
                        END
                    ) as avg_duration
                FROM conversation_sessions
                WHERE started_at >= ?
            """, (start_date.isoformat(),))
            row = cursor.fetchone()
            metrics.average_session_duration_seconds = row['avg_duration'] or 0.0
        
        # Completion rate
        if metrics.total_sessions > 0:
            metrics.completion_rate = metrics.completed_sessions / metrics.total_sessions
        
        return metrics
    
    def compute_recommendation_metrics(
        self,
        days: int = 7,
        end_date: datetime = None
    ) -> RecommendationMetrics:
        """
        Compute recommendation and feedback metrics.
        
        SQL Queries:
        - Feedback counts by type
        - Listen durations
        - Category breakdowns
        """
        end_date = end_date or datetime.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = RecommendationMetrics()
        
        with self._connection() as conn:
            # Check for feedback table
            if not self._table_exists(conn, 'feedback'):
                return metrics
            
            # Feedback counts
            cursor = conn.execute("""
                SELECT 
                    feedback_type,
                    COUNT(*) as count
                FROM feedback
                WHERE created_at >= ?
                GROUP BY feedback_type
            """, (start_date.isoformat(),))
            
            for row in cursor.fetchall():
                fb_type = row['feedback_type']
                count = row['count']
                metrics.total_feedback += count
                
                if fb_type == 'like':
                    metrics.likes = count
                elif fb_type == 'dislike':
                    metrics.dislikes = count
                elif fb_type == 'skip':
                    metrics.skips = count
            
            # Calculate ratios
            if metrics.total_feedback > 0:
                metrics.like_ratio = metrics.likes / metrics.total_feedback
                metrics.dislike_ratio = metrics.dislikes / metrics.total_feedback
                metrics.skip_ratio = metrics.skips / metrics.total_feedback
            
            # Total recommendations from history
            if self._table_exists(conn, 'listening_history'):
                cursor = conn.execute("""
                    SELECT COUNT(*) as total
                    FROM listening_history
                    WHERE listened_at >= ?
                """, (start_date.isoformat(),))
                row = cursor.fetchone()
                metrics.total_recommendations = row['total'] if row else 0
                
                # Listen duration stats
                cursor = conn.execute("""
                    SELECT 
                        AVG(listened_duration_seconds) as avg_duration,
                        SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
                    FROM listening_history
                    WHERE listened_at >= ?
                    AND listened_duration_seconds IS NOT NULL
                """, (start_date.isoformat(),))
                row = cursor.fetchone()
                if row:
                    metrics.average_listen_duration_seconds = row['avg_duration'] or 0
                    completed = row['completed'] or 0
                    if metrics.total_recommendations > 0:
                        metrics.completion_rate = completed / metrics.total_recommendations
            
            # Acceptance rate
            if metrics.total_recommendations > 0:
                # Consider likes and completions as acceptances
                acceptances = metrics.likes + int(metrics.completion_rate * metrics.total_recommendations)
                metrics.acceptance_rate = min(1.0, acceptances / metrics.total_recommendations)
            
            # Feedback by mood
            cursor = conn.execute("""
                SELECT 
                    s.mood,
                    f.feedback_type,
                    COUNT(*) as count
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.created_at >= ?
                GROUP BY s.mood, f.feedback_type
            """, (start_date.isoformat(),))
            
            for row in cursor.fetchall():
                mood = row['mood'] or 'unknown'
                fb_type = row['feedback_type']
                count = row['count']
                
                if mood not in metrics.feedback_by_mood:
                    metrics.feedback_by_mood[mood] = {}
                metrics.feedback_by_mood[mood][fb_type] = count
            
            # Feedback by genre
            cursor = conn.execute("""
                SELECT 
                    s.genre,
                    f.feedback_type,
                    COUNT(*) as count
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.created_at >= ?
                GROUP BY s.genre, f.feedback_type
            """, (start_date.isoformat(),))
            
            for row in cursor.fetchall():
                genre = row['genre'] or 'unknown'
                fb_type = row['feedback_type']
                count = row['count']
                
                if genre not in metrics.feedback_by_genre:
                    metrics.feedback_by_genre[genre] = {}
                metrics.feedback_by_genre[genre][fb_type] = count
        
        return metrics
    
    # =========================================================================
    # HELPER METRICS
    # =========================================================================
    
    def _compute_user_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """Compute user-related metrics."""
        metrics = {'total': 0, 'active_24h': 0, 'active_7d': 0, 'new_7d': 0}
        
        with self._connection() as conn:
            if not self._table_exists(conn, 'users'):
                return metrics
            
            # Total users
            cursor = conn.execute("SELECT COUNT(*) as total FROM users")
            row = cursor.fetchone()
            metrics['total'] = row['total'] if row else 0
            
            # Active users (24h)
            cutoff_24h = (end_date - timedelta(hours=24)).isoformat()
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM listening_history
                WHERE listened_at >= ?
            """, (cutoff_24h,))
            row = cursor.fetchone()
            metrics['active_24h'] = row['count'] if row else 0
            
            # Active users (7d)
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT user_id) as count
                FROM listening_history
                WHERE listened_at >= ?
            """, (start_date.isoformat(),))
            row = cursor.fetchone()
            metrics['active_7d'] = row['count'] if row else 0
            
            # New users (7d)
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM users
                WHERE created_at >= ?
            """, (start_date.isoformat(),))
            row = cursor.fetchone()
            metrics['new_7d'] = row['count'] if row else 0
        
        return metrics
    
    def _compute_content_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """Compute content-related metrics."""
        metrics = {'total_songs': 0, 'recommended': 0}
        
        with self._connection() as conn:
            if not self._table_exists(conn, 'songs'):
                return metrics
            
            # Total songs
            cursor = conn.execute("SELECT COUNT(*) as total FROM songs")
            row = cursor.fetchone()
            metrics['total_songs'] = row['total'] if row else 0
            
            # Songs recommended at least once
            if self._table_exists(conn, 'listening_history'):
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT song_id) as count
                    FROM listening_history
                    WHERE listened_at >= ?
                """, (start_date.isoformat(),))
                row = cursor.fetchone()
                metrics['recommended'] = row['count'] if row else 0
        
        return metrics
    
    def _compute_performance_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Compute performance-related metrics."""
        metrics = {'avg_response_ms': 0.0, 'p95_response_ms': 0.0, 'error_rate': 0.0}
        
        with self._connection() as conn:
            if not self._table_exists(conn, 'conversation_turns'):
                return metrics
            
            # Response time stats
            cursor = conn.execute("""
                SELECT 
                    AVG(processing_time_ms) as avg_time
                FROM conversation_turns
                WHERE created_at >= ?
                AND processing_time_ms IS NOT NULL
            """, (start_date.isoformat(),))
            row = cursor.fetchone()
            metrics['avg_response_ms'] = row['avg_time'] or 0.0
            
            # P95 (approximate)
            cursor = conn.execute("""
                SELECT processing_time_ms
                FROM conversation_turns
                WHERE created_at >= ?
                AND processing_time_ms IS NOT NULL
                ORDER BY processing_time_ms
            """, (start_date.isoformat(),))
            times = [r['processing_time_ms'] for r in cursor.fetchall()]
            if times:
                p95_idx = int(len(times) * 0.95)
                metrics['p95_response_ms'] = times[min(p95_idx, len(times) - 1)]
        
        return metrics
    
    # =========================================================================
    # SPECIALIZED ANALYTICS
    # =========================================================================
    
    def get_mood_distribution(self, days: int = 7) -> Dict[str, int]:
        """Get distribution of detected moods."""
        start_date = datetime.now() - timedelta(days=days)
        
        distribution = {}
        
        with self._connection() as conn:
            if self._table_exists(conn, 'conversation_sessions'):
                cursor = conn.execute("""
                    SELECT final_mood, COUNT(*) as count
                    FROM conversation_sessions
                    WHERE started_at >= ?
                    AND final_mood IS NOT NULL
                    GROUP BY final_mood
                    ORDER BY count DESC
                """, (start_date.isoformat(),))
                
                for row in cursor.fetchall():
                    distribution[row['final_mood']] = row['count']
        
        return distribution
    
    def get_hourly_activity(self, days: int = 7) -> Dict[int, int]:
        """Get activity distribution by hour of day."""
        start_date = datetime.now() - timedelta(days=days)
        
        activity = {h: 0 for h in range(24)}
        
        with self._connection() as conn:
            if self._table_exists(conn, 'conversation_sessions'):
                cursor = conn.execute("""
                    SELECT 
                        CAST(strftime('%H', started_at) AS INTEGER) as hour,
                        COUNT(*) as count
                    FROM conversation_sessions
                    WHERE started_at >= ?
                    GROUP BY hour
                """, (start_date.isoformat(),))
                
                for row in cursor.fetchall():
                    activity[row['hour']] = row['count']
        
        return activity
    
    def get_top_recommended_songs(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get most recommended songs."""
        start_date = datetime.now() - timedelta(days=days)
        
        songs = []
        
        with self._connection() as conn:
            if not self._table_exists(conn, 'listening_history'):
                return songs
            
            cursor = conn.execute("""
                SELECT 
                    h.song_id,
                    s.song_name,
                    s.artist,
                    COUNT(*) as recommend_count,
                    SUM(CASE WHEN f.feedback_type = 'like' THEN 1 ELSE 0 END) as likes
                FROM listening_history h
                JOIN songs s ON h.song_id = s.song_id
                LEFT JOIN feedback f ON h.song_id = f.song_id AND h.user_id = f.user_id
                WHERE h.listened_at >= ?
                GROUP BY h.song_id
                ORDER BY recommend_count DESC
                LIMIT ?
            """, (start_date.isoformat(), limit))
            
            for row in cursor.fetchall():
                songs.append({
                    'song_id': row['song_id'],
                    'song_name': row['song_name'],
                    'artist': row['artist'],
                    'recommend_count': row['recommend_count'],
                    'likes': row['likes'] or 0,
                })
        
        return songs


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_analytics_engine(db_path: str = None) -> AnalyticsEngine:
    """Create an AnalyticsEngine instance."""
    return AnalyticsEngine(db_path)
