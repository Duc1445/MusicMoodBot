"""
Feedback Repository (Enhanced)
==============================
Data access for feedback table with advanced learning loop support.

Enhancements v4.0:
- Preference drift tracking
- Dynamic weight adjustment
- Extended feedback types
- Contextual feedback storage
- Learning loop integration

Author: MusicMoodBot Team
Version: 4.0.0
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import math
import json
from .base import BaseRepository


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FeedbackContext:
    """Contextual information for feedback."""
    mood: str = None
    time_of_day: str = None  # morning, afternoon, evening, night
    day_of_week: str = None
    activity: str = None  # workout, work, relaxing, commute
    weather: str = None
    listen_duration_pct: float = None  # How much of song was played (0-100)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FeedbackContext':
        if not json_str:
            return cls()
        try:
            return cls(**json.loads(json_str))
        except:
            return cls()


@dataclass
class PreferenceDrift:
    """Tracks changes in user preferences over time."""
    user_id: int
    attribute: str  # genre, mood, energy, valence, tempo, etc.
    old_value: float
    new_value: float
    drift_magnitude: float
    detected_at: datetime = field(default_factory=datetime.now)
    
    @property
    def direction(self) -> str:
        """Direction of drift: 'increase', 'decrease', or 'stable'."""
        if self.drift_magnitude > 0.05:
            return 'increase'
        elif self.drift_magnitude < -0.05:
            return 'decrease'
        return 'stable'


@dataclass
class WeightAdjustment:
    """Record of weight adjustment for a user."""
    user_id: int
    feature: str
    old_weight: float
    new_weight: float
    reason: str
    adjusted_at: datetime = field(default_factory=datetime.now)


class FeedbackRepository(BaseRepository):
    """Repository for user feedback on songs."""
    
    TABLE = "feedback"
    PRIMARY_KEY = "feedback_id"
    
    def add(self, user_id: int, song_id: int, feedback_type: str, 
            history_id: int = None) -> Optional[int]:
        """
        Add feedback entry.
        
        Args:
            user_id: User ID
            song_id: Song ID
            feedback_type: 'like', 'dislike', or 'skip'
            history_id: Optional listening history entry ID
            
        Returns:
            feedback_id if successful, None otherwise
        """
        if feedback_type not in ('like', 'dislike', 'skip'):
            raise ValueError(f"Invalid feedback_type: {feedback_type}")
        
        with self.connection() as conn:
            cursor = conn.execute("""
                INSERT INTO feedback (user_id, song_id, feedback_type, history_id)
                VALUES (?, ?, ?, ?)
            """, (user_id, song_id, feedback_type, history_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_feedback(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get all feedback from a user."""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT f.*, s.song_name, s.artist, s.genre, s.mood
                FROM feedback f
                LEFT JOIN songs s ON f.song_id = s.song_id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_likes(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get songs user has liked."""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT f.*, s.song_name, s.artist, s.genre, s.mood,
                       s.energy, s.valence, s.tempo
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.user_id = ? AND f.feedback_type = 'like'
                ORDER BY f.created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_dislikes(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get songs user has disliked."""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT f.*, s.song_name, s.artist, s.genre, s.mood
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.user_id = ? AND f.feedback_type = 'dislike'
                ORDER BY f.created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_song_feedback_stats(self, song_id: int) -> Dict:
        """Get feedback statistics for a song."""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(CASE WHEN feedback_type = 'like' THEN 1 END) as likes,
                    COUNT(CASE WHEN feedback_type = 'dislike' THEN 1 END) as dislikes,
                    COUNT(CASE WHEN feedback_type = 'skip' THEN 1 END) as skips,
                    COUNT(*) as total
                FROM feedback
                WHERE song_id = ?
            """, (song_id,))
            row = cursor.fetchone()
            return dict(row) if row else {"likes": 0, "dislikes": 0, "skips": 0, "total": 0}
    
    def has_user_feedback(self, user_id: int, song_id: int) -> Optional[str]:
        """Check if user has given feedback on a song. Returns feedback_type or None."""
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT feedback_type FROM feedback
                WHERE user_id = ? AND song_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id, song_id))
            row = cursor.fetchone()
            return row['feedback_type'] if row else None
    
    def update_feedback(self, user_id: int, song_id: int, 
                        new_feedback_type: str) -> bool:
        """Update existing feedback or insert new one."""
        if new_feedback_type not in ('like', 'dislike', 'skip'):
            raise ValueError(f"Invalid feedback_type: {new_feedback_type}")
        
        with self.connection() as conn:
            # Try to update existing
            cursor = conn.execute("""
                UPDATE feedback 
                SET feedback_type = ?, created_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND song_id = ?
            """, (new_feedback_type, user_id, song_id))
            
            if cursor.rowcount == 0:
                # Insert new
                conn.execute("""
                    INSERT INTO feedback (user_id, song_id, feedback_type)
                    VALUES (?, ?, ?)
                """, (user_id, song_id, new_feedback_type))
            
            conn.commit()
            return True
    
    def get_feedback_for_training(self, user_id: int, limit: int = 500) -> List[Dict]:
        """
        Get feedback data formatted for preference model training.
        
        Returns:
            List of dicts with song features and label (1=like, 0=dislike/skip)
        """
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    s.song_id, s.song_name, s.artist, s.genre, s.mood,
                    s.energy, s.valence, s.tempo, s.loudness,
                    s.danceability, s.acousticness,
                    f.feedback_type,
                    CASE 
                        WHEN f.feedback_type = 'like' THEN 1
                        ELSE 0
                    END as label
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.user_id = ? AND f.feedback_type IN ('like', 'dislike')
                ORDER BY f.created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # =========================================================================
    # EXTENDED FEEDBACK TYPES (v4.0)
    # =========================================================================
    
    def add_with_context(
        self,
        user_id: int,
        song_id: int,
        feedback_type: str,
        context: FeedbackContext = None,
        emotional_response: Dict = None,
        session_id: str = None
    ) -> Optional[int]:
        """
        Add feedback with rich contextual information.
        
        Args:
            user_id: User ID
            song_id: Song ID
            feedback_type: 'like', 'dislike', 'skip', 'love', 'neutral'
            context: Contextual information
            emotional_response: Detected emotional state
            session_id: Session identifier
            
        Returns:
            feedback_id if successful
        """
        valid_types = ('like', 'dislike', 'skip', 'love', 'neutral')
        if feedback_type not in valid_types:
            raise ValueError(f"Invalid feedback_type: {feedback_type}")
        
        context_json = context.to_json() if context else None
        emotional_json = json.dumps(emotional_response) if emotional_response else None
        
        with self.connection() as conn:
            cursor = conn.execute("""
                INSERT INTO feedback (
                    user_id, song_id, feedback_type, 
                    context_data, emotional_response, session_id
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, song_id, feedback_type, context_json, emotional_json, session_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_contextual_patterns(self, user_id: int) -> Dict[str, Dict]:
        """
        Analyze feedback patterns by context.
        
        Returns patterns like:
        - "User likes energetic music in the morning"
        - "User prefers calmer music in the evening"
        """
        patterns = {
            'time_of_day': {},
            'activity': {},
            'mood': {},
        }
        
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT f.feedback_type, f.context_data, s.energy, s.valence, 
                       s.genre, s.mood as song_mood
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.user_id = ? AND f.context_data IS NOT NULL
                ORDER BY f.created_at DESC
                LIMIT 200
            """, (user_id,))
            
            for row in cursor.fetchall():
                context = FeedbackContext.from_json(row['context_data'])
                is_positive = row['feedback_type'] in ('like', 'love')
                
                # Aggregate by time of day
                if context.time_of_day:
                    if context.time_of_day not in patterns['time_of_day']:
                        patterns['time_of_day'][context.time_of_day] = {
                            'avg_energy': [], 'avg_valence': [], 
                            'genres': [], 'moods': [], 'positive_count': 0, 'total': 0
                        }
                    p = patterns['time_of_day'][context.time_of_day]
                    if row['energy']:
                        p['avg_energy'].append(row['energy'] if is_positive else -row['energy'])
                    if row['valence']:
                        p['avg_valence'].append(row['valence'] if is_positive else -row['valence'])
                    if row['genre'] and is_positive:
                        p['genres'].append(row['genre'])
                    if row['song_mood'] and is_positive:
                        p['moods'].append(row['song_mood'])
                    p['positive_count'] += 1 if is_positive else 0
                    p['total'] += 1
                
                # Aggregate by activity
                if context.activity:
                    if context.activity not in patterns['activity']:
                        patterns['activity'][context.activity] = {
                            'avg_energy': [], 'avg_valence': [],
                            'genres': [], 'moods': [], 'positive_count': 0, 'total': 0
                        }
                    p = patterns['activity'][context.activity]
                    if row['energy']:
                        p['avg_energy'].append(row['energy'] if is_positive else -row['energy'])
                    if row['valence']:
                        p['avg_valence'].append(row['valence'] if is_positive else -row['valence'])
                    if row['genre'] and is_positive:
                        p['genres'].append(row['genre'])
                    if row['song_mood'] and is_positive:
                        p['moods'].append(row['song_mood'])
                    p['positive_count'] += 1 if is_positive else 0
                    p['total'] += 1
        
        # Compute averages and find top items
        for category in patterns.values():
            for key, data in category.items():
                if data['avg_energy']:
                    data['avg_energy'] = sum(data['avg_energy']) / len(data['avg_energy'])
                else:
                    data['avg_energy'] = None
                if data['avg_valence']:
                    data['avg_valence'] = sum(data['avg_valence']) / len(data['avg_valence'])
                else:
                    data['avg_valence'] = None
                # Top genres and moods
                from collections import Counter
                if data['genres']:
                    data['top_genres'] = [g for g, _ in Counter(data['genres']).most_common(3)]
                if data['moods']:
                    data['top_moods'] = [m for m, _ in Counter(data['moods']).most_common(3)]
        
        return patterns
    
    # =========================================================================
    # PREFERENCE DRIFT TRACKING (v4.0)
    # =========================================================================
    
    def _ensure_drift_table(self):
        """Ensure preference_drift table exists."""
        with self.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS preference_drift (
                    drift_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    attribute TEXT NOT NULL,
                    old_value REAL,
                    new_value REAL,
                    drift_magnitude REAL,
                    detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_drift_user 
                ON preference_drift(user_id, detected_at)
            """)
            conn.commit()
    
    def detect_preference_drift(self, user_id: int, window_days: int = 30) -> List[PreferenceDrift]:
        """
        Detect shifts in user preferences by comparing recent vs. historical feedback.
        
        Compares the average liked song attributes from:
        - Recent period (last window_days / 3)
        - Historical period (before that)
        """
        self._ensure_drift_table()
        
        drifts = []
        attributes = ['energy', 'valence', 'tempo', 'danceability', 'acousticness']
        
        recent_cutoff = datetime.now() - timedelta(days=window_days // 3)
        historical_cutoff = datetime.now() - timedelta(days=window_days)
        
        with self.connection() as conn:
            # Get recent averages
            cursor_recent = conn.execute("""
                SELECT 
                    AVG(s.energy) as avg_energy,
                    AVG(s.valence) as avg_valence,
                    AVG(s.tempo) as avg_tempo,
                    AVG(s.danceability) as avg_danceability,
                    AVG(s.acousticness) as avg_acousticness,
                    COUNT(*) as count
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.user_id = ? 
                  AND f.feedback_type IN ('like', 'love')
                  AND f.created_at > ?
            """, (user_id, recent_cutoff.isoformat()))
            recent = cursor_recent.fetchone()
            
            # Get historical averages
            cursor_hist = conn.execute("""
                SELECT 
                    AVG(s.energy) as avg_energy,
                    AVG(s.valence) as avg_valence,
                    AVG(s.tempo) as avg_tempo,
                    AVG(s.danceability) as avg_danceability,
                    AVG(s.acousticness) as avg_acousticness,
                    COUNT(*) as count
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.user_id = ? 
                  AND f.feedback_type IN ('like', 'love')
                  AND f.created_at > ?
                  AND f.created_at <= ?
            """, (user_id, historical_cutoff.isoformat(), recent_cutoff.isoformat()))
            historical = cursor_hist.fetchone()
            
            # Need sufficient data
            if recent['count'] < 5 or historical['count'] < 5:
                return drifts
            
            # Compare and detect drift
            for attr in attributes:
                old_val = historical[f'avg_{attr}']
                new_val = recent[f'avg_{attr}']
                
                if old_val is None or new_val is None:
                    continue
                
                magnitude = new_val - old_val
                
                # Significant drift threshold (> 10% change)
                if abs(magnitude) > 0.1:
                    drift = PreferenceDrift(
                        user_id=user_id,
                        attribute=attr,
                        old_value=old_val,
                        new_value=new_val,
                        drift_magnitude=magnitude,
                    )
                    drifts.append(drift)
                    
                    # Store in database
                    conn.execute("""
                        INSERT INTO preference_drift 
                        (user_id, attribute, old_value, new_value, drift_magnitude)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, attr, old_val, new_val, magnitude))
            
            conn.commit()
        
        return drifts
    
    def get_drift_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get history of detected preference drifts."""
        self._ensure_drift_table()
        
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM preference_drift
                WHERE user_id = ?
                ORDER BY detected_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # WEIGHT ADJUSTMENT (v4.0)
    # =========================================================================
    
    def _ensure_weights_table(self):
        """Ensure user_weights table exists."""
        with self.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_weights (
                    weight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    feature TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, feature)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weight_adjustments (
                    adjustment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    feature TEXT NOT NULL,
                    old_weight REAL,
                    new_weight REAL,
                    reason TEXT,
                    adjusted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            conn.commit()
    
    def get_user_weights(self, user_id: int) -> Dict[str, float]:
        """Get current feature weights for a user."""
        self._ensure_weights_table()
        
        # Default weights
        default_weights = {
            'mood_match': 1.0,
            'genre_preference': 1.0,
            'artist_familiarity': 0.8,
            'energy_match': 1.0,
            'valence_match': 1.0,
            'tempo_preference': 0.7,
            'novelty': 0.5,
            'diversity': 0.5,
        }
        
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT feature, weight FROM user_weights
                WHERE user_id = ?
            """, (user_id,))
            
            for row in cursor.fetchall():
                default_weights[row['feature']] = row['weight']
        
        return default_weights
    
    def adjust_weights(
        self,
        user_id: int,
        feature: str,
        new_weight: float,
        reason: str = "feedback-based"
    ) -> WeightAdjustment:
        """
        Adjust a feature weight for a user.
        
        Args:
            user_id: User ID
            feature: Feature name (e.g., 'mood_match', 'energy_match')
            new_weight: New weight value (0.0 - 2.0)
            reason: Reason for adjustment
            
        Returns:
            WeightAdjustment record
        """
        self._ensure_weights_table()
        
        new_weight = max(0.0, min(2.0, new_weight))  # Clamp to [0, 2]
        
        with self.connection() as conn:
            # Get old weight
            cursor = conn.execute("""
                SELECT weight FROM user_weights
                WHERE user_id = ? AND feature = ?
            """, (user_id, feature))
            row = cursor.fetchone()
            old_weight = row['weight'] if row else 1.0
            
            # Update or insert
            conn.execute("""
                INSERT INTO user_weights (user_id, feature, weight, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, feature) 
                DO UPDATE SET weight = ?, updated_at = CURRENT_TIMESTAMP
            """, (user_id, feature, new_weight, new_weight))
            
            # Record adjustment
            conn.execute("""
                INSERT INTO weight_adjustments 
                (user_id, feature, old_weight, new_weight, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, feature, old_weight, new_weight, reason))
            
            conn.commit()
        
        return WeightAdjustment(
            user_id=user_id,
            feature=feature,
            old_weight=old_weight,
            new_weight=new_weight,
            reason=reason,
        )
    
    def auto_adjust_weights_from_feedback(self, user_id: int) -> List[WeightAdjustment]:
        """
        Automatically adjust weights based on recent feedback patterns.
        
        Logic:
        - If user consistently likes high-energy songs -> increase energy_match weight
        - If user ignores mood-matched songs -> decrease mood_match weight
        - etc.
        """
        adjustments = []
        
        with self.connection() as conn:
            # Analyze recent feedback
            cursor = conn.execute("""
                SELECT 
                    f.feedback_type,
                    s.energy, s.valence, s.tempo,
                    s.genre, s.mood
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.user_id = ?
                  AND f.created_at > datetime('now', '-30 days')
                ORDER BY f.created_at DESC
                LIMIT 100
            """, (user_id,))
            
            feedback_data = [dict(row) for row in cursor.fetchall()]
        
        if len(feedback_data) < 10:
            return adjustments  # Not enough data
        
        # Compute statistics for liked vs disliked
        liked = [f for f in feedback_data if f['feedback_type'] in ('like', 'love')]
        disliked = [f for f in feedback_data if f['feedback_type'] in ('dislike', 'skip')]
        
        if not liked or not disliked:
            return adjustments
        
        # Energy analysis
        avg_liked_energy = sum(f['energy'] or 0 for f in liked) / len(liked)
        avg_disliked_energy = sum(f['energy'] or 0 for f in disliked) / len(disliked)
        energy_diff = avg_liked_energy - avg_disliked_energy
        
        # If strong preference for energy levels
        current_weights = self.get_user_weights(user_id)
        
        if abs(energy_diff) > 0.2:
            new_energy_weight = min(2.0, current_weights['energy_match'] + 0.1)
            adj = self.adjust_weights(
                user_id, 'energy_match', new_energy_weight,
                f"Energy preference detected (diff={energy_diff:.2f})"
            )
            adjustments.append(adj)
        
        # Valence analysis
        avg_liked_valence = sum(f['valence'] or 0 for f in liked) / len(liked)
        avg_disliked_valence = sum(f['valence'] or 0 for f in disliked) / len(disliked)
        valence_diff = avg_liked_valence - avg_disliked_valence
        
        if abs(valence_diff) > 0.2:
            new_valence_weight = min(2.0, current_weights['valence_match'] + 0.1)
            adj = self.adjust_weights(
                user_id, 'valence_match', new_valence_weight,
                f"Valence preference detected (diff={valence_diff:.2f})"
            )
            adjustments.append(adj)
        
        # Genre consistency analysis
        liked_genres = [f['genre'] for f in liked if f['genre']]
        if liked_genres:
            from collections import Counter
            genre_counts = Counter(liked_genres)
            top_genre_ratio = genre_counts.most_common(1)[0][1] / len(liked_genres)
            
            if top_genre_ratio > 0.5:
                new_genre_weight = min(2.0, current_weights['genre_preference'] + 0.1)
                adj = self.adjust_weights(
                    user_id, 'genre_preference', new_genre_weight,
                    f"Strong genre preference detected (ratio={top_genre_ratio:.2f})"
                )
                adjustments.append(adj)
        
        return adjustments
    
    def get_weight_adjustment_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get history of weight adjustments."""
        self._ensure_weights_table()
        
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM weight_adjustments
                WHERE user_id = ?
                ORDER BY adjusted_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # LEARNING LOOP INTEGRATION (v4.0)
    # =========================================================================
    
    def get_feedback_stats(self, user_id: int, days: int = 30) -> Dict:
        """
        Get comprehensive feedback statistics for learning loop.
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_feedback,
                    COUNT(CASE WHEN feedback_type = 'like' THEN 1 END) as likes,
                    COUNT(CASE WHEN feedback_type = 'love' THEN 1 END) as loves,
                    COUNT(CASE WHEN feedback_type = 'dislike' THEN 1 END) as dislikes,
                    COUNT(CASE WHEN feedback_type = 'skip' THEN 1 END) as skips,
                    COUNT(CASE WHEN feedback_type = 'neutral' THEN 1 END) as neutrals
                FROM feedback
                WHERE user_id = ? AND created_at > ?
            """, (user_id, cutoff.isoformat()))
            counts = dict(cursor.fetchone())
            
            # Calculate rates
            total = counts['total_feedback'] or 1
            counts['like_rate'] = (counts['likes'] + counts['loves']) / total
            counts['dislike_rate'] = counts['dislikes'] / total
            counts['skip_rate'] = counts['skips'] / total
            counts['engagement_score'] = (
                counts['loves'] * 2 + counts['likes'] - 
                counts['dislikes'] * 1.5 - counts['skips'] * 0.5
            ) / total
            
            return counts
    
    def get_feedback_sequences(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Get feedback as sequences for pattern analysis.
        
        Useful for detecting:
        - Skip patterns (e.g., always skips after certain genre)
        - Like streaks
        - Fatigue patterns
        """
        with self.connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    f.feedback_type, f.created_at,
                    s.song_name, s.artist, s.genre, s.mood,
                    s.energy, s.valence, s.tempo,
                    LAG(f.feedback_type) OVER (ORDER BY f.created_at) as prev_feedback,
                    LAG(s.genre) OVER (ORDER BY f.created_at) as prev_genre,
                    LAG(s.mood) OVER (ORDER BY f.created_at) as prev_mood
                FROM feedback f
                JOIN songs s ON f.song_id = s.song_id
                WHERE f.user_id = ?
                ORDER BY f.created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

