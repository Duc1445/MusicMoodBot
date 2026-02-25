"""
=============================================================================
WEIGHT ADAPTER - v5.0
=============================================================================

Adaptive weight management for personalized recommendations.

Features:
- Per-user weight learning
- Feedback-based weight adjustment
- Weight regularization (L2)
- Persistence to database

Author: MusicMoodBot Team
Version: 5.0.0
=============================================================================
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from datetime import datetime
import sqlite3
import json
import math


# Module-level default weights constant
DEFAULT_WEIGHTS = {
    "mood_match": 1.0,
    "emotional_resonance": 1.0,
    "valence_alignment": 1.0,
    "energy_alignment": 1.0,
    "artist_preference": 1.0,
    "genre_preference": 1.0,
    "tempo_comfort": 1.0,
    "popularity": 0.5,
    "recency": 0.3,
}


@dataclass
class WeightAdjustment:
    """Record of a weight adjustment."""
    timestamp: datetime
    feature: str
    old_weight: float
    new_weight: float
    delta: float
    reason: str
    feedback_type: Optional[str] = None
    song_id: Optional[int] = None


class WeightAdapter:
    """
    Adaptive weight manager for user preference learning.
    
    Adjusts feature weights based on user feedback using gradient-like updates.
    """
    
    # Default weights (must match ScoringEngine)
    DEFAULT_WEIGHTS = {
        "mood_match": 1.0,
        "emotional_resonance": 1.0,
        "valence_alignment": 1.0,
        "energy_alignment": 1.0,
        "artist_preference": 1.0,
        "genre_preference": 1.0,
        "tempo_comfort": 1.0,
        "popularity": 0.5,
        "recency": 0.3,
    }
    
    # Learning parameters
    LEARNING_RATE = 0.05
    WEIGHT_DECAY = 0.01      # L2 regularization
    WEIGHT_MIN = 0.1
    WEIGHT_MAX = 2.0
    
    # Feedback reward mapping
    FEEDBACK_DELTAS = {
        "love": 0.10,
        "like": 0.05,
        "neutral": 0.0,
        "skip": -0.03,
        "dislike": -0.08,
    }
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self._user_weights: Dict[int, Dict[str, float]] = {}
        self._adjustment_history: Dict[int, List[WeightAdjustment]] = {}
        
        # Initialize weights table if db_path provided
        if self.db_path:
            self._init_database()
    
    def _init_database(self):
        """Create weights table if not exists."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_weights (
                    user_id INTEGER PRIMARY KEY,
                    weights_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weight_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    feature TEXT NOT NULL,
                    old_weight REAL NOT NULL,
                    new_weight REAL NOT NULL,
                    delta REAL NOT NULL,
                    reason TEXT,
                    feedback_type TEXT,
                    song_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not initialize weights database: {e}")
    
    def get_weights(self, user_id: int) -> Dict[str, float]:
        """
        Get weights for a user.
        
        Loads from database if not in memory, or returns defaults.
        """
        # Check memory cache
        if user_id in self._user_weights:
            return self._user_weights[user_id].copy()
        
        # Try loading from database
        if self.db_path:
            weights = self._load_weights_from_db(user_id)
            if weights:
                self._user_weights[user_id] = weights
                return weights.copy()
        
        # Return defaults
        return self.DEFAULT_WEIGHTS.copy()
    
    def set_weights(self, user_id: int, weights: Dict[str, float]) -> None:
        """
        Directly set weights for a user.
        
        Validates and clamps weights to valid range.
        """
        # Validate and clamp weights
        validated_weights = {}
        for feature, weight in weights.items():
            if feature in self.DEFAULT_WEIGHTS or feature in ["valence", "energy", "tempo", "danceability"]:
                validated_weights[feature] = max(self.WEIGHT_MIN, min(self.WEIGHT_MAX, float(weight)))
        
        # Merge with defaults for missing features
        full_weights = self.DEFAULT_WEIGHTS.copy()
        full_weights.update(validated_weights)
        
        # Update memory cache
        self._user_weights[user_id] = full_weights
        
        # Persist to database
        self._save_weights_to_db(user_id, full_weights)
    
    def _load_weights_from_db(self, user_id: int) -> Optional[Dict[str, float]]:
        """Load weights from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT weights_json FROM user_weights WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
        except Exception as e:
            print(f"Error loading weights: {e}")
            return None
    
    def _save_weights_to_db(self, user_id: int, weights: Dict[str, float]):
        """Save weights to database."""
        if not self.db_path:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_weights (user_id, weights_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_id, json.dumps(weights)))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving weights: {e}")
    
    def _save_adjustment_to_db(self, user_id: int, adjustment: WeightAdjustment):
        """Save adjustment record to database."""
        if not self.db_path:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO weight_adjustments 
                (user_id, feature, old_weight, new_weight, delta, reason, feedback_type, song_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                adjustment.feature,
                adjustment.old_weight,
                adjustment.new_weight,
                adjustment.delta,
                adjustment.reason,
                adjustment.feedback_type,
                adjustment.song_id,
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving adjustment: {e}")
    
    def adjust_weights(
        self,
        user_id: int,
        feedback_type: str,
        song_features: Dict[str, float],
        song_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Adjust weights based on user feedback.
        
        Args:
            user_id: User ID
            feedback_type: Type of feedback (love, like, neutral, skip, dislike)
            song_features: Feature values of the song that received feedback
            song_id: Optional song ID for logging
            
        Returns:
            Dictionary with adjusted weights and adjustments made
        """
        # Get current weights
        weights = self.get_weights(user_id)
        
        # Get feedback delta
        base_delta = self.FEEDBACK_DELTAS.get(feedback_type.lower(), 0.0)
        
        if base_delta == 0.0:
            return {
                "user_id": user_id,
                "weights": weights,
                "adjustments": [],
                "message": "No adjustment needed for neutral feedback",
            }
        
        adjustments = []
        
        # Adjust weights based on feature contribution
        for feature, current_weight in list(weights.items()):
            feature_value = song_features.get(feature, 0.5)
            
            # Higher feature value = more influence on this adjustment
            adjustment_magnitude = base_delta * self.LEARNING_RATE * feature_value
            
            # Apply L2 regularization (decay toward 1.0)
            regularization = -self.WEIGHT_DECAY * (current_weight - 1.0)
            
            # Calculate new weight
            new_weight = current_weight + adjustment_magnitude + regularization
            
            # Clamp to valid range
            new_weight = max(self.WEIGHT_MIN, min(self.WEIGHT_MAX, new_weight))
            
            # Only record if changed
            if abs(new_weight - current_weight) > 0.0001:
                adjustment = WeightAdjustment(
                    timestamp=datetime.utcnow(),
                    feature=feature,
                    old_weight=current_weight,
                    new_weight=new_weight,
                    delta=new_weight - current_weight,
                    reason=f"{feedback_type} feedback",
                    feedback_type=feedback_type,
                    song_id=song_id,
                )
                adjustments.append(adjustment)
                weights[feature] = new_weight
                
                # Save to database
                self._save_adjustment_to_db(user_id, adjustment)
        
        # Update memory cache
        self._user_weights[user_id] = weights
        
        # Save to database
        self._save_weights_to_db(user_id, weights)
        
        # Update adjustment history
        if user_id not in self._adjustment_history:
            self._adjustment_history[user_id] = []
        self._adjustment_history[user_id].extend(adjustments)
        
        return {
            "user_id": user_id,
            "weights": weights,
            "adjustments": [
                {
                    "feature": a.feature,
                    "old_weight": round(a.old_weight, 4),
                    "new_weight": round(a.new_weight, 4),
                    "delta": round(a.delta, 4),
                }
                for a in adjustments
            ],
            "message": f"Adjusted {len(adjustments)} weights based on {feedback_type} feedback",
        }
    
    def set_weight(
        self,
        user_id: int,
        feature: str,
        weight: float,
        reason: str = "manual",
    ) -> Dict[str, Any]:
        """
        Manually set a specific weight.
        
        Args:
            user_id: User ID
            feature: Feature name
            weight: New weight value
            reason: Reason for adjustment
            
        Returns:
            Result dictionary
        """
        weights = self.get_weights(user_id)
        
        if feature not in self.DEFAULT_WEIGHTS:
            return {
                "success": False,
                "error": f"Unknown feature: {feature}",
                "valid_features": list(self.DEFAULT_WEIGHTS.keys()),
            }
        
        # Clamp to valid range
        new_weight = max(self.WEIGHT_MIN, min(self.WEIGHT_MAX, weight))
        old_weight = weights[feature]
        
        adjustment = WeightAdjustment(
            timestamp=datetime.utcnow(),
            feature=feature,
            old_weight=old_weight,
            new_weight=new_weight,
            delta=new_weight - old_weight,
            reason=reason,
        )
        
        weights[feature] = new_weight
        self._user_weights[user_id] = weights
        self._save_weights_to_db(user_id, weights)
        self._save_adjustment_to_db(user_id, adjustment)
        
        return {
            "success": True,
            "user_id": user_id,
            "feature": feature,
            "old_weight": round(old_weight, 4),
            "new_weight": round(new_weight, 4),
            "weights": {k: round(v, 4) for k, v in weights.items()},
        }
    
    def reset_weights(self, user_id: int) -> Dict[str, float]:
        """Reset user weights to defaults."""
        weights = self.DEFAULT_WEIGHTS.copy()
        self._user_weights[user_id] = weights
        self._save_weights_to_db(user_id, weights)
        return weights
    
    def get_weight_history(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent weight adjustments for a user."""
        if not self.db_path:
            # Return from memory
            history = self._adjustment_history.get(user_id, [])
            return [
                {
                    "feature": a.feature,
                    "old_weight": round(a.old_weight, 4),
                    "new_weight": round(a.new_weight, 4),
                    "delta": round(a.delta, 4),
                    "reason": a.reason,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in history[-limit:]
            ]
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT feature, old_weight, new_weight, delta, reason, 
                       feedback_type, song_id, created_at
                FROM weight_adjustments
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "feature": row["feature"],
                    "old_weight": round(row["old_weight"], 4),
                    "new_weight": round(row["new_weight"], 4),
                    "delta": round(row["delta"], 4),
                    "reason": row["reason"],
                    "feedback_type": row["feedback_type"],
                    "song_id": row["song_id"],
                    "timestamp": row["created_at"],
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error getting weight history: {e}")
            return []
    
    def get_weight_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get statistics about user's weight adjustments."""
        weights = self.get_weights(user_id)
        history = self.get_weight_history(user_id, limit=100)
        
        # Calculate deviation from defaults
        deviations = {
            feature: abs(weight - self.DEFAULT_WEIGHTS.get(feature, 1.0))
            for feature, weight in weights.items()
        }
        
        # Find most/least important features
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "user_id": user_id,
            "current_weights": {k: round(v, 4) for k, v in weights.items()},
            "most_important": sorted_weights[:3],
            "least_important": sorted_weights[-3:],
            "total_adjustments": len(history),
            "avg_deviation_from_default": round(
                sum(deviations.values()) / len(deviations) if deviations else 0,
                4
            ),
            "personalization_score": round(
                min(1.0, sum(deviations.values()) / len(deviations) * 2) if deviations else 0,
                4
            ),
        }
    
    def get_adjustment_count(self, user_id: int) -> int:
        """Get the total count of weight adjustments for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM user_weight_history
                WHERE user_id = ?
            """, (user_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0


# Global weight adapter instance
_weight_adapter: Optional[WeightAdapter] = None


def get_weight_adapter(db_path: Optional[str] = None) -> WeightAdapter:
    """Get or create the global weight adapter."""
    global _weight_adapter
    if _weight_adapter is None:
        _weight_adapter = WeightAdapter(db_path)
    return _weight_adapter
