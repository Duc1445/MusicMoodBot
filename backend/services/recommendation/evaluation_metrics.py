"""
=============================================================================
EVALUATION & METRICS LAYER
=============================================================================

Comprehensive evaluation framework for the recommendation system.

Metrics:
========
1. Precision@K          - Accuracy of top-K recommendations
2. Recall@K             - Coverage of relevant items
3. NDCG@K               - Ranking quality metric
4. Session Satisfaction - User satisfaction per session
5. Emotion Accuracy     - Mood prediction accuracy
6. Acceptance Rate      - Recommendation acceptance ratio
7. Diversity Metrics    - Catalog coverage and variety
8. A/B Test Framework   - Experiment tracking

Mathematical Definitions:
========================
Precision@K = |{relevant} ∩ {recommended@K}| / K
Recall@K = |{relevant} ∩ {recommended@K}| / |{relevant}|
NDCG@K = DCG@K / IDCG@K
Session Satisfaction = Σ(positive_signals) / total_signals

Author: MusicMoodBot Team
Version: 4.0.0
=============================================================================
"""

from __future__ import annotations

import math
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict
from contextlib import contextmanager
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class PrecisionRecallMetrics:
    """Precision and recall metrics at K."""
    k: int
    precision: float
    recall: float
    f1_score: float
    
    relevant_count: int = 0
    recommended_count: int = 0
    hits: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'k': self.k,
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1_score': round(self.f1_score, 4),
            'relevant_count': self.relevant_count,
            'recommended_count': self.recommended_count,
            'hits': self.hits,
        }


@dataclass
class NDCGMetrics:
    """NDCG (Normalized Discounted Cumulative Gain) metrics."""
    k: int
    dcg: float
    idcg: float
    ndcg: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'k': self.k,
            'dcg': round(self.dcg, 4),
            'idcg': round(self.idcg, 4),
            'ndcg': round(self.ndcg, 4),
        }


@dataclass
class SessionSatisfaction:
    """Satisfaction metrics for a session."""
    session_id: str
    user_id: int
    
    total_recommendations: int = 0
    likes: int = 0
    dislikes: int = 0
    skips: int = 0
    listens: int = 0
    completions: int = 0
    
    # Computed metrics
    satisfaction_score: float = 0.0
    engagement_rate: float = 0.0
    completion_rate: float = 0.0
    
    def compute(self):
        """Compute derived metrics."""
        total = self.likes + self.dislikes + self.skips + self.listens
        
        if total > 0:
            # Satisfaction: weighted positive signals
            positive = self.likes * 1.0 + self.completions * 0.7 + self.listens * 0.3
            negative = self.dislikes * 1.0 + self.skips * 0.5
            self.satisfaction_score = positive / (positive + negative) if (positive + negative) > 0 else 0.5
            
            # Engagement: any interaction
            self.engagement_rate = (self.likes + self.listens + self.completions) / total
            
        if self.listens > 0:
            self.completion_rate = self.completions / self.listens
    
    def to_dict(self) -> Dict[str, Any]:
        self.compute()
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'total_recommendations': self.total_recommendations,
            'likes': self.likes,
            'dislikes': self.dislikes,
            'skips': self.skips,
            'listens': self.listens,
            'completions': self.completions,
            'satisfaction_score': round(self.satisfaction_score, 4),
            'engagement_rate': round(self.engagement_rate, 4),
            'completion_rate': round(self.completion_rate, 4),
        }


@dataclass
class EmotionAccuracy:
    """Emotion prediction accuracy metrics."""
    total_predictions: int = 0
    correct_predictions: int = 0
    
    # Per-mood accuracy
    mood_accuracies: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # mood -> (correct, total)
    
    # Confusion matrix data
    confusion_matrix: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))
    
    @property
    def overall_accuracy(self) -> float:
        if self.total_predictions == 0:
            return 0.0
        return self.correct_predictions / self.total_predictions
    
    def add_prediction(self, predicted: str, actual: str):
        """Record a prediction."""
        self.total_predictions += 1
        
        if predicted == actual:
            self.correct_predictions += 1
        
        # Update mood-specific tracking
        if actual not in self.mood_accuracies:
            self.mood_accuracies[actual] = (0, 0)
        
        correct, total = self.mood_accuracies[actual]
        self.mood_accuracies[actual] = (
            correct + (1 if predicted == actual else 0),
            total + 1
        )
        
        # Update confusion matrix
        self.confusion_matrix[actual][predicted] += 1
    
    def to_dict(self) -> Dict[str, Any]:
        per_mood = {}
        for mood, (correct, total) in self.mood_accuracies.items():
            per_mood[mood] = {
                'accuracy': round(correct / total, 4) if total > 0 else 0.0,
                'correct': correct,
                'total': total,
            }
        
        return {
            'overall_accuracy': round(self.overall_accuracy, 4),
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions,
            'per_mood_accuracy': per_mood,
        }


@dataclass
class AcceptanceMetrics:
    """Recommendation acceptance rate metrics."""
    total_shown: int = 0
    accepted: int = 0  # Like or play
    rejected: int = 0  # Dislike
    ignored: int = 0   # Skip or no action
    
    # Time-based acceptance
    hourly_acceptance: Dict[int, Tuple[int, int]] = field(default_factory=dict)  # hour -> (accepted, total)
    
    @property
    def acceptance_rate(self) -> float:
        if self.total_shown == 0:
            return 0.0
        return self.accepted / self.total_shown
    
    @property
    def rejection_rate(self) -> float:
        if self.total_shown == 0:
            return 0.0
        return self.rejected / self.total_shown
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_shown': self.total_shown,
            'accepted': self.accepted,
            'rejected': self.rejected,
            'ignored': self.ignored,
            'acceptance_rate': round(self.acceptance_rate, 4),
            'rejection_rate': round(self.rejection_rate, 4),
            'ignore_rate': round(self.ignored / self.total_shown, 4) if self.total_shown > 0 else 0.0,
        }


@dataclass
class DiversityMetrics:
    """Catalog diversity and coverage metrics."""
    total_catalog_size: int = 0
    unique_recommended: int = 0
    
    # Distribution metrics
    genre_distribution: Dict[str, int] = field(default_factory=dict)
    artist_distribution: Dict[str, int] = field(default_factory=dict)
    mood_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Gini coefficient (0 = perfect equality, 1 = perfect inequality)
    gini_coefficient: float = 0.0
    
    @property
    def catalog_coverage(self) -> float:
        if self.total_catalog_size == 0:
            return 0.0
        return self.unique_recommended / self.total_catalog_size
    
    def compute_gini(self):
        """Compute Gini coefficient of recommendation distribution."""
        if not self.genre_distribution:
            return
        
        values = sorted(self.genre_distribution.values())
        n = len(values)
        
        if n == 0 or sum(values) == 0:
            self.gini_coefficient = 0.0
            return
        
        # Gini formula
        cumsum = 0
        for i, val in enumerate(values):
            cumsum += (2 * (i + 1) - n - 1) * val
        
        self.gini_coefficient = cumsum / (n * sum(values))
    
    def to_dict(self) -> Dict[str, Any]:
        self.compute_gini()
        return {
            'catalog_coverage': round(self.catalog_coverage, 4),
            'total_catalog_size': self.total_catalog_size,
            'unique_recommended': self.unique_recommended,
            'gini_coefficient': round(self.gini_coefficient, 4),
            'genre_distribution': self.genre_distribution,
            'top_artists': dict(sorted(
                self.artist_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
        }


@dataclass
class ExperimentResult:
    """Result of an A/B test experiment."""
    experiment_id: str
    variant: str
    
    # Sample size
    sample_size: int = 0
    
    # Primary metric
    primary_metric_value: float = 0.0
    primary_metric_variance: float = 0.0
    
    # Secondary metrics
    secondary_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Statistical significance
    p_value: Optional[float] = None
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    is_significant: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'experiment_id': self.experiment_id,
            'variant': self.variant,
            'sample_size': self.sample_size,
            'primary_metric': round(self.primary_metric_value, 4),
            'secondary_metrics': {k: round(v, 4) for k, v in self.secondary_metrics.items()},
            'p_value': round(self.p_value, 4) if self.p_value else None,
            'confidence_interval': [round(x, 4) for x in self.confidence_interval],
            'is_significant': self.is_significant,
        }


# =============================================================================
# EVALUATION ENGINE
# =============================================================================

class EvaluationEngine:
    """
    Comprehensive evaluation engine for recommendation quality.
    
    Provides:
    - Precision/Recall@K computation
    - NDCG@K computation
    - Session satisfaction analysis
    - Emotion prediction accuracy
    - Acceptance rate tracking
    - Diversity metrics
    - A/B test framework
    
    Usage:
        engine = EvaluationEngine(db_path)
        
        # Compute precision@k
        precision = engine.compute_precision_at_k(user_id, k=10)
        
        # Get session satisfaction
        satisfaction = engine.compute_session_satisfaction(session_id)
        
        # Get overall metrics
        dashboard = engine.get_metrics_dashboard(days=7)
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or self._get_default_db_path()
    
    def _get_default_db_path(self) -> str:
        import os
        return os.path.join(
            os.path.dirname(__file__),
            "..", "src", "database", "music.db"
        )
    
    @contextmanager
    def _connection(self):
        """Database connection context."""
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
    # PRECISION & RECALL
    # =========================================================================
    
    def compute_precision_at_k(
        self,
        user_id: int,
        k: int = 10,
        days: int = 30
    ) -> PrecisionRecallMetrics:
        """
        Compute Precision@K for a user.
        
        Precision@K = |{relevant} ∩ {recommended@K}| / K
        
        Relevant items = songs the user liked
        """
        with self._connection() as conn:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get recommended songs (top K per session)
            cursor = conn.execute("""
                SELECT DISTINCT song_id
                FROM listening_history
                WHERE user_id = ? AND listened_at >= ?
                ORDER BY listened_at DESC
                LIMIT ?
            """, (user_id, start_date, k))
            recommended = {row['song_id'] for row in cursor.fetchall()}
            
            # Get relevant songs (liked)
            cursor = conn.execute("""
                SELECT DISTINCT song_id
                FROM feedback
                WHERE user_id = ? AND feedback_type = 'like'
                AND created_at >= ?
            """, (user_id, start_date))
            relevant = {row['song_id'] for row in cursor.fetchall()}
        
        hits = len(recommended & relevant)
        precision = hits / k if k > 0 else 0.0
        recall = hits / len(relevant) if relevant else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return PrecisionRecallMetrics(
            k=k,
            precision=precision,
            recall=recall,
            f1_score=f1,
            relevant_count=len(relevant),
            recommended_count=len(recommended),
            hits=hits,
        )
    
    def compute_recall_at_k(
        self,
        user_id: int,
        k: int = 10,
        days: int = 30
    ) -> PrecisionRecallMetrics:
        """Compute Recall@K - same as precision_at_k but focuses on recall."""
        return self.compute_precision_at_k(user_id, k, days)
    
    # =========================================================================
    # NDCG
    # =========================================================================
    
    def compute_ndcg_at_k(
        self,
        user_id: int,
        k: int = 10,
        days: int = 30
    ) -> NDCGMetrics:
        """
        Compute NDCG@K (Normalized Discounted Cumulative Gain).
        
        DCG@K = Σ (rel_i / log2(i + 1)) for i in 1..K
        NDCG@K = DCG@K / IDCG@K
        
        Relevance scores:
        - like = 3
        - play/complete = 2
        - skip = 0
        - dislike = -1 (treated as 0 for DCG)
        """
        with self._connection() as conn:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get recommendations with feedback
            cursor = conn.execute("""
                SELECT 
                    h.song_id,
                    h.listened_at,
                    f.feedback_type,
                    h.completed
                FROM listening_history h
                LEFT JOIN feedback f ON h.song_id = f.song_id AND h.user_id = f.user_id
                WHERE h.user_id = ? AND h.listened_at >= ?
                ORDER BY h.listened_at DESC
                LIMIT ?
            """, (user_id, start_date, k))
            
            # Compute relevance scores
            relevances = []
            for row in cursor.fetchall():
                feedback = row['feedback_type']
                completed = row['completed']
                
                if feedback == 'like':
                    rel = 3
                elif feedback == 'dislike':
                    rel = 0
                elif completed:
                    rel = 2
                else:
                    rel = 1
                
                relevances.append(rel)
        
        # Pad with zeros if fewer than k items
        while len(relevances) < k:
            relevances.append(0)
        
        # Compute DCG
        dcg = sum(
            rel / math.log2(i + 2)  # i + 2 because log2(1) = 0
            for i, rel in enumerate(relevances[:k])
        )
        
        # Compute IDCG (ideal ranking)
        ideal_relevances = sorted(relevances, reverse=True)
        idcg = sum(
            rel / math.log2(i + 2)
            for i, rel in enumerate(ideal_relevances[:k])
        )
        
        ndcg = dcg / idcg if idcg > 0 else 0.0
        
        return NDCGMetrics(
            k=k,
            dcg=dcg,
            idcg=idcg,
            ndcg=ndcg,
        )
    
    # =========================================================================
    # SESSION SATISFACTION
    # =========================================================================
    
    def compute_session_satisfaction(
        self,
        session_id: str
    ) -> SessionSatisfaction:
        """Compute satisfaction metrics for a session."""
        satisfaction = SessionSatisfaction(session_id=session_id, user_id=0)
        
        with self._connection() as conn:
            # Get session info
            cursor = conn.execute("""
                SELECT user_id FROM conversation_sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row:
                satisfaction.user_id = row['user_id']
            
            # Get recommendations in session
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM listening_history
                WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            satisfaction.total_recommendations = row['count'] if row else 0
            
            # Get feedback distribution
            cursor = conn.execute("""
                SELECT 
                    feedback_type,
                    COUNT(*) as count
                FROM feedback f
                JOIN listening_history h ON f.song_id = h.song_id AND f.user_id = h.user_id
                WHERE h.session_id = ?
                GROUP BY feedback_type
            """, (session_id,))
            
            for row in cursor.fetchall():
                ft = row['feedback_type']
                count = row['count']
                
                if ft == 'like':
                    satisfaction.likes = count
                elif ft == 'dislike':
                    satisfaction.dislikes = count
                elif ft == 'skip':
                    satisfaction.skips = count
            
            # Get listen/completion counts
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as listens,
                    SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completions
                FROM listening_history
                WHERE session_id = ?
                AND listened_duration_seconds > 30
            """, (session_id,))
            row = cursor.fetchone()
            if row:
                satisfaction.listens = row['listens'] or 0
                satisfaction.completions = row['completions'] or 0
        
        satisfaction.compute()
        return satisfaction
    
    def compute_average_session_satisfaction(
        self,
        days: int = 7
    ) -> Dict[str, float]:
        """Compute average satisfaction across all sessions."""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        satisfactions = []
        
        with self._connection() as conn:
            cursor = conn.execute("""
                SELECT session_id
                FROM conversation_sessions
                WHERE started_at >= ?
                AND state IN ('ENDED', 'DELIVERY')
            """, (start_date,))
            
            for row in cursor.fetchall():
                sat = self.compute_session_satisfaction(row['session_id'])
                satisfactions.append(sat)
        
        if not satisfactions:
            return {
                'average_satisfaction': 0.0,
                'average_engagement': 0.0,
                'average_completion': 0.0,
                'session_count': 0,
            }
        
        return {
            'average_satisfaction': sum(s.satisfaction_score for s in satisfactions) / len(satisfactions),
            'average_engagement': sum(s.engagement_rate for s in satisfactions) / len(satisfactions),
            'average_completion': sum(s.completion_rate for s in satisfactions) / len(satisfactions),
            'session_count': len(satisfactions),
        }
    
    # =========================================================================
    # EMOTION ACCURACY
    # =========================================================================
    
    def compute_emotion_accuracy(
        self,
        days: int = 30
    ) -> EmotionAccuracy:
        """
        Compute emotion prediction accuracy.
        
        Compares detected mood with user feedback to assess accuracy.
        """
        accuracy = EmotionAccuracy()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._connection() as conn:
            if not self._table_exists(conn, 'conversation_sessions'):
                return accuracy
            
            # Get sessions with mood predictions and feedback
            cursor = conn.execute("""
                SELECT 
                    cs.final_mood as predicted_mood,
                    s.mood as song_mood,
                    f.feedback_type
                FROM conversation_sessions cs
                JOIN listening_history h ON cs.session_id = h.session_id
                JOIN songs s ON h.song_id = s.song_id
                LEFT JOIN feedback f ON h.song_id = f.song_id AND h.user_id = f.user_id
                WHERE cs.started_at >= ?
                AND cs.final_mood IS NOT NULL
                AND f.feedback_type = 'like'
            """, (start_date,))
            
            for row in cursor.fetchall():
                predicted = row['predicted_mood']
                actual = row['song_mood']
                
                if predicted and actual:
                    accuracy.add_prediction(predicted.lower(), actual.lower())
        
        return accuracy
    
    # =========================================================================
    # ACCEPTANCE RATE
    # =========================================================================
    
    def compute_acceptance_rate(
        self,
        days: int = 7,
        user_id: int = None
    ) -> AcceptanceMetrics:
        """Compute recommendation acceptance rate."""
        metrics = AcceptanceMetrics()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._connection() as conn:
            # Build query
            query = """
                SELECT 
                    h.song_id,
                    h.listened_at,
                    f.feedback_type
                FROM listening_history h
                LEFT JOIN feedback f ON h.song_id = f.song_id AND h.user_id = f.user_id
                WHERE h.listened_at >= ?
            """
            params = [start_date]
            
            if user_id:
                query += " AND h.user_id = ?"
                params.append(user_id)
            
            cursor = conn.execute(query, params)
            
            for row in cursor.fetchall():
                metrics.total_shown += 1
                
                feedback = row['feedback_type']
                
                if feedback == 'like':
                    metrics.accepted += 1
                elif feedback == 'dislike':
                    metrics.rejected += 1
                elif feedback == 'skip':
                    metrics.ignored += 1
                else:
                    # Played but no explicit feedback
                    metrics.accepted += 1
                
                # Track hourly
                listened_at = row['listened_at']
                if listened_at:
                    try:
                        dt = datetime.fromisoformat(listened_at)
                        hour = dt.hour
                        
                        if hour not in metrics.hourly_acceptance:
                            metrics.hourly_acceptance[hour] = (0, 0)
                        
                        accepted, total = metrics.hourly_acceptance[hour]
                        is_accepted = feedback in ('like', None)
                        metrics.hourly_acceptance[hour] = (
                            accepted + (1 if is_accepted else 0),
                            total + 1
                        )
                    except:
                        pass
        
        return metrics
    
    # =========================================================================
    # DIVERSITY METRICS
    # =========================================================================
    
    def compute_diversity_metrics(
        self,
        days: int = 7
    ) -> DiversityMetrics:
        """Compute catalog diversity and coverage metrics."""
        metrics = DiversityMetrics()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._connection() as conn:
            # Total catalog size
            cursor = conn.execute("SELECT COUNT(*) as count FROM songs")
            row = cursor.fetchone()
            metrics.total_catalog_size = row['count'] if row else 0
            
            # Unique recommended
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT song_id) as count
                FROM listening_history
                WHERE listened_at >= ?
            """, (start_date,))
            row = cursor.fetchone()
            metrics.unique_recommended = row['count'] if row else 0
            
            # Genre distribution
            cursor = conn.execute("""
                SELECT s.genre, COUNT(*) as count
                FROM listening_history h
                JOIN songs s ON h.song_id = s.song_id
                WHERE h.listened_at >= ?
                GROUP BY s.genre
            """, (start_date,))
            
            for row in cursor.fetchall():
                genre = row['genre'] or 'unknown'
                metrics.genre_distribution[genre] = row['count']
            
            # Artist distribution
            cursor = conn.execute("""
                SELECT s.artist, COUNT(*) as count
                FROM listening_history h
                JOIN songs s ON h.song_id = s.song_id
                WHERE h.listened_at >= ?
                GROUP BY s.artist
                ORDER BY count DESC
                LIMIT 50
            """, (start_date,))
            
            for row in cursor.fetchall():
                artist = row['artist'] or 'unknown'
                metrics.artist_distribution[artist] = row['count']
            
            # Mood distribution
            cursor = conn.execute("""
                SELECT s.mood, COUNT(*) as count
                FROM listening_history h
                JOIN songs s ON h.song_id = s.song_id
                WHERE h.listened_at >= ?
                GROUP BY s.mood
            """, (start_date,))
            
            for row in cursor.fetchall():
                mood = row['mood'] or 'unknown'
                metrics.mood_distribution[mood] = row['count']
        
        return metrics
    
    # =========================================================================
    # DASHBOARD
    # =========================================================================
    
    def get_metrics_dashboard(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get comprehensive metrics dashboard."""
        
        # Compute all metrics
        acceptance = self.compute_acceptance_rate(days)
        diversity = self.compute_diversity_metrics(days)
        emotion = self.compute_emotion_accuracy(days)
        satisfaction = self.compute_average_session_satisfaction(days)
        
        return {
            'period_days': days,
            'computed_at': datetime.now().isoformat(),
            'acceptance': acceptance.to_dict(),
            'diversity': diversity.to_dict(),
            'emotion_accuracy': emotion.to_dict(),
            'session_satisfaction': satisfaction,
            'summary': {
                'acceptance_rate': round(acceptance.acceptance_rate, 4),
                'catalog_coverage': round(diversity.catalog_coverage, 4),
                'emotion_accuracy': round(emotion.overall_accuracy, 4),
                'average_satisfaction': round(satisfaction.get('average_satisfaction', 0), 4),
            }
        }
    
    # =========================================================================
    # A/B TESTING
    # =========================================================================
    
    def create_experiment(
        self,
        experiment_id: str,
        variants: List[str],
        primary_metric: str = "acceptance_rate"
    ) -> bool:
        """Create a new A/B test experiment."""
        with self._connection() as conn:
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS experiments (
                        experiment_id TEXT PRIMARY KEY,
                        variants TEXT,
                        primary_metric TEXT,
                        created_at TEXT,
                        status TEXT DEFAULT 'active'
                    )
                """)
                
                conn.execute("""
                    INSERT INTO experiments (experiment_id, variants, primary_metric, created_at)
                    VALUES (?, ?, ?, ?)
                """, (experiment_id, ",".join(variants), primary_metric, datetime.now().isoformat()))
                
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Failed to create experiment: {e}")
                return False
    
    def record_experiment_event(
        self,
        experiment_id: str,
        variant: str,
        user_id: int,
        metric_value: float
    ):
        """Record an event in an experiment."""
        with self._connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiment_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    experiment_id TEXT,
                    variant TEXT,
                    user_id INTEGER,
                    metric_value REAL,
                    created_at TEXT
                )
            """)
            
            conn.execute("""
                INSERT INTO experiment_events (experiment_id, variant, user_id, metric_value, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (experiment_id, variant, user_id, metric_value, datetime.now().isoformat()))
            
            conn.commit()
    
    def analyze_experiment(
        self,
        experiment_id: str
    ) -> Dict[str, ExperimentResult]:
        """Analyze results of an A/B test."""
        results = {}
        
        with self._connection() as conn:
            if not self._table_exists(conn, 'experiment_events'):
                return results
            
            cursor = conn.execute("""
                SELECT 
                    variant,
                    COUNT(*) as sample_size,
                    AVG(metric_value) as avg_value,
                    SUM(metric_value * metric_value) as sum_sq
                FROM experiment_events
                WHERE experiment_id = ?
                GROUP BY variant
            """, (experiment_id,))
            
            for row in cursor.fetchall():
                variant = row['variant']
                n = row['sample_size']
                mean = row['avg_value']
                sum_sq = row['sum_sq']
                
                # Compute variance
                variance = (sum_sq / n - mean * mean) if n > 1 else 0
                std_dev = math.sqrt(variance)
                
                # 95% confidence interval
                margin = 1.96 * std_dev / math.sqrt(n) if n > 0 else 0
                
                results[variant] = ExperimentResult(
                    experiment_id=experiment_id,
                    variant=variant,
                    sample_size=n,
                    primary_metric_value=mean,
                    primary_metric_variance=variance,
                    confidence_interval=(mean - margin, mean + margin),
                )
        
        # Compute statistical significance between variants
        if len(results) == 2:
            variants = list(results.values())
            # Simple z-test for proportions
            p1, p2 = variants[0].primary_metric_value, variants[1].primary_metric_value
            n1, n2 = variants[0].sample_size, variants[1].sample_size
            
            if n1 > 0 and n2 > 0:
                pooled = (p1 * n1 + p2 * n2) / (n1 + n2)
                se = math.sqrt(pooled * (1 - pooled) * (1/n1 + 1/n2)) if 0 < pooled < 1 else 1
                z = abs(p1 - p2) / se if se > 0 else 0
                
                # p-value approximation (two-tailed)
                p_value = 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))
                
                for result in results.values():
                    result.p_value = p_value
                    result.is_significant = p_value < 0.05
        
        return results


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_evaluation_engine(db_path: str = None) -> EvaluationEngine:
    """Create an EvaluationEngine instance."""
    return EvaluationEngine(db_path)
