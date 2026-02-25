"""
=============================================================================
SESSION REWARD CALCULATOR - v5.0
=============================================================================

Calculates composite session reward for reinforcement learning.

Formula:
    R = 0.40 × Engagement + 0.30 × Satisfaction + 0.30 × EmotionalImprovement

Features:
- Multi-component reward calculation
- Real-time reward tracking per session
- Feedback integration for bandit learning
- Historical reward analysis

Author: MusicMoodBot Team
Version: 5.0.0
=============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    """User feedback types with reward values."""
    LOVE = "love"         # +1.0
    LIKE = "like"         # +0.8
    NEUTRAL = "neutral"   # +0.4
    SKIP = "skip"         # +0.1
    DISLIKE = "dislike"   # 0.0


@dataclass
class RewardEvent:
    """Single reward event in a session."""
    timestamp: datetime
    event_type: str                    # feedback, engagement, emotional
    song_id: Optional[int]
    raw_value: float                   # Raw component value
    weighted_value: float              # After weight applied
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "song_id": self.song_id,
            "raw_value": round(self.raw_value, 4),
            "weighted_value": round(self.weighted_value, 4),
            "metadata": self.metadata,
        }


class SessionRewardCalculator:
    """
    Calculates composite session reward for learning.
    
    Reward Components:
    - Engagement (40%): Based on user actions (likes, listens, etc.)
    - Satisfaction (30%): Based on recommendation acceptance rate
    - Emotional Improvement (30%): Based on trajectory direction
    """
    
    # Component weights (must sum to 1.0)
    ENGAGEMENT_WEIGHT = 0.40
    SATISFACTION_WEIGHT = 0.30
    EMOTIONAL_WEIGHT = 0.30
    
    # Feedback reward mapping
    FEEDBACK_REWARDS = {
        FeedbackType.LOVE.value: 1.0,
        FeedbackType.LIKE.value: 0.8,
        FeedbackType.NEUTRAL.value: 0.4,
        FeedbackType.SKIP.value: 0.1,
        FeedbackType.DISLIKE.value: 0.0,
    }
    
    # Listen duration thresholds
    LISTEN_THRESHOLD_FULL = 0.8     # >80% = full listen
    LISTEN_THRESHOLD_PARTIAL = 0.3  # >30% = partial listen
    
    def __init__(self, session_id: str, user_id: int):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.utcnow()
        
        # Reward tracking
        self._events: List[RewardEvent] = []
        self._engagement_sum = 0.0
        self._engagement_count = 0
        self._satisfaction_sum = 0.0
        self._satisfaction_count = 0
        self._emotional_improvement = 0.0
        
        # Rolling metrics
        self._total_recommendations = 0
        self._accepted_recommendations = 0  # liked or loved
        self._songs_fully_listened = 0
        self._songs_partially_listened = 0
        
        # Emotional baseline (set from first turn)
        self._initial_valence: Optional[float] = None
        self._current_valence: float = 0.0
    
    def record_feedback(
        self,
        song_id: int,
        feedback: str,
        listen_duration_pct: float = 0.0,
        recommendation_score: float = 0.5,
    ) -> float:
        """
        Record user feedback and calculate reward contribution.
        
        Args:
            song_id: ID of the song
            feedback: Feedback type (love, like, neutral, skip, dislike)
            listen_duration_pct: Percentage of song listened (0-100)
            recommendation_score: Original recommendation score (0-1)
            
        Returns:
            The calculated reward contribution
        """
        # Calculate engagement component
        feedback_reward = self.FEEDBACK_REWARDS.get(feedback.lower(), 0.4)
        
        # Bonus for listen duration
        listen_pct = listen_duration_pct / 100.0 if listen_duration_pct > 1.0 else listen_duration_pct
        if listen_pct >= self.LISTEN_THRESHOLD_FULL:
            listen_bonus = 0.2
            self._songs_fully_listened += 1
        elif listen_pct >= self.LISTEN_THRESHOLD_PARTIAL:
            listen_bonus = 0.1
            self._songs_partially_listened += 1
        else:
            listen_bonus = 0.0
        
        engagement_value = min(1.0, feedback_reward + listen_bonus)
        engagement_weighted = engagement_value * self.ENGAGEMENT_WEIGHT
        
        self._engagement_sum += engagement_value
        self._engagement_count += 1
        
        # Calculate satisfaction component
        self._total_recommendations += 1
        if feedback.lower() in (FeedbackType.LOVE.value, FeedbackType.LIKE.value):
            self._accepted_recommendations += 1
            satisfaction_value = recommendation_score  # Higher score = better match
        elif feedback.lower() == FeedbackType.NEUTRAL.value:
            satisfaction_value = 0.5
        else:
            satisfaction_value = 1.0 - recommendation_score  # Penalty for bad predictions
        
        self._satisfaction_sum += satisfaction_value
        self._satisfaction_count += 1
        satisfaction_weighted = satisfaction_value * self.SATISFACTION_WEIGHT
        
        # Record event
        event = RewardEvent(
            timestamp=datetime.utcnow(),
            event_type="feedback",
            song_id=song_id,
            raw_value=feedback_reward,
            weighted_value=engagement_weighted + satisfaction_weighted,
            metadata={
                "feedback": feedback,
                "listen_duration_pct": listen_duration_pct,
                "engagement_value": engagement_value,
                "satisfaction_value": satisfaction_value,
            }
        )
        self._events.append(event)
        
        return engagement_weighted + satisfaction_weighted
    
    def update_emotional_state(
        self,
        valence: float,
        arousal: float,
        trajectory_trend: str,
    ) -> float:
        """
        Update emotional component based on trajectory.
        
        Args:
            valence: Current valence (-1 to 1)
            arousal: Current arousal (-1 to 1)
            trajectory_trend: Trend from EmotionalTrajectoryTracker
            
        Returns:
            Emotional improvement contribution
        """
        # Set baseline on first update
        if self._initial_valence is None:
            self._initial_valence = valence
        
        self._current_valence = valence
        
        # Calculate improvement from baseline
        if self._initial_valence is not None:
            raw_improvement = valence - self._initial_valence
            # Normalize to 0-1 range (improvement from -2 to +2 range)
            normalized_improvement = (raw_improvement + 2.0) / 4.0
        else:
            normalized_improvement = 0.5
        
        # Trend bonus
        trend_bonus = 0.0
        if trajectory_trend == "improving":
            trend_bonus = 0.15
        elif trajectory_trend == "stable":
            trend_bonus = 0.05
        elif trajectory_trend == "declining":
            trend_bonus = -0.1
        
        emotional_value = min(1.0, max(0.0, normalized_improvement + trend_bonus))
        emotional_weighted = emotional_value * self.EMOTIONAL_WEIGHT
        
        self._emotional_improvement = emotional_value
        
        # Record event
        event = RewardEvent(
            timestamp=datetime.utcnow(),
            event_type="emotional",
            song_id=None,
            raw_value=emotional_value,
            weighted_value=emotional_weighted,
            metadata={
                "valence": valence,
                "arousal": arousal,
                "trajectory_trend": trajectory_trend,
                "initial_valence": self._initial_valence,
                "improvement": raw_improvement if self._initial_valence else 0.0,
            }
        )
        self._events.append(event)
        
        return emotional_weighted
    
    def calculate_session_reward(self) -> float:
        """
        Calculate total session reward.
        
        Returns:
            Composite reward value [0, 1]
        """
        # Average engagement
        if self._engagement_count > 0:
            avg_engagement = self._engagement_sum / self._engagement_count
        else:
            avg_engagement = 0.5  # Default neutral
        
        # Average satisfaction (acceptance rate)
        if self._satisfaction_count > 0:
            avg_satisfaction = self._satisfaction_sum / self._satisfaction_count
        else:
            avg_satisfaction = 0.5
        
        # Emotional improvement (already 0-1)
        emotional = self._emotional_improvement
        
        # Weighted sum
        total_reward = (
            avg_engagement * self.ENGAGEMENT_WEIGHT +
            avg_satisfaction * self.SATISFACTION_WEIGHT +
            emotional * self.EMOTIONAL_WEIGHT
        )
        
        return round(total_reward, 4)
    
    def get_acceptance_rate(self) -> float:
        """Get recommendation acceptance rate."""
        if self._total_recommendations == 0:
            return 0.0
        return self._accepted_recommendations / self._total_recommendations
    
    def get_engagement_metrics(self) -> Dict[str, float]:
        """Get detailed engagement metrics."""
        return {
            "average_engagement": (
                self._engagement_sum / self._engagement_count
                if self._engagement_count > 0 else 0.0
            ),
            "total_feedbacks": self._engagement_count,
            "songs_fully_listened": self._songs_fully_listened,
            "songs_partially_listened": self._songs_partially_listened,
        }
    
    def get_reward_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed reward breakdown.
        
        Returns:
            Dictionary with all reward components
        """
        avg_engagement = (
            self._engagement_sum / self._engagement_count
            if self._engagement_count > 0 else 0.5
        )
        avg_satisfaction = (
            self._satisfaction_sum / self._satisfaction_count
            if self._satisfaction_count > 0 else 0.5
        )
        
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "session_duration_seconds": (datetime.utcnow() - self.created_at).total_seconds(),
            "total_reward": self.calculate_session_reward(),
            "components": {
                "engagement": {
                    "weight": self.ENGAGEMENT_WEIGHT,
                    "average": round(avg_engagement, 4),
                    "weighted": round(avg_engagement * self.ENGAGEMENT_WEIGHT, 4),
                    "count": self._engagement_count,
                },
                "satisfaction": {
                    "weight": self.SATISFACTION_WEIGHT,
                    "average": round(avg_satisfaction, 4),
                    "weighted": round(avg_satisfaction * self.SATISFACTION_WEIGHT, 4),
                    "acceptance_rate": round(self.get_acceptance_rate(), 4),
                    "total_recommendations": self._total_recommendations,
                    "accepted": self._accepted_recommendations,
                },
                "emotional_improvement": {
                    "weight": self.EMOTIONAL_WEIGHT,
                    "value": round(self._emotional_improvement, 4),
                    "weighted": round(self._emotional_improvement * self.EMOTIONAL_WEIGHT, 4),
                    "initial_valence": self._initial_valence,
                    "current_valence": self._current_valence,
                },
            },
            "event_count": len(self._events),
            "listen_metrics": {
                "fully_listened": self._songs_fully_listened,
                "partially_listened": self._songs_partially_listened,
            },
        }
    
    def get_bandit_reward(self, strategy: str) -> float:
        """
        Get reward value for Thompson Sampling bandit update.
        
        This converts the session reward into a binary-ish signal
        for updating the beta distribution priors.
        
        Args:
            strategy: The strategy that was used
            
        Returns:
            Reward value suitable for bandit update (0 or 1 for binary)
        """
        session_reward = self.calculate_session_reward()
        
        # Convert to binary for Thompson Sampling
        # Threshold at 0.5 for success/failure
        if session_reward >= 0.6:
            return 1.0  # Success
        elif session_reward >= 0.4:
            return 0.5  # Partial success
        else:
            return 0.0  # Failure
    
    def get_recent_events(self, n: int = 10) -> List[Dict]:
        """Get n most recent reward events."""
        return [e.to_dict() for e in self._events[-n:]]
    
    def calculate_engagement_score(self) -> float:
        """Calculate engagement score component."""
        if self._engagement_count > 0:
            return self._engagement_sum / self._engagement_count
        return 0.0
    
    def calculate_satisfaction_score(self) -> float:
        """Calculate satisfaction score component."""
        if self._satisfaction_count > 0:
            return self._satisfaction_sum / self._satisfaction_count
        return 0.0
    
    def calculate_emotional_alignment(self) -> float:
        """Calculate emotional alignment/improvement component."""
        return self._emotional_improvement
    
    @property
    def events(self) -> List[RewardEvent]:
        """Get all events."""
        return self._events.copy()
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "engagement_sum": self._engagement_sum,
            "engagement_count": self._engagement_count,
            "satisfaction_sum": self._satisfaction_sum,
            "satisfaction_count": self._satisfaction_count,
            "emotional_improvement": self._emotional_improvement,
            "total_recommendations": self._total_recommendations,
            "accepted_recommendations": self._accepted_recommendations,
            "songs_fully_listened": self._songs_fully_listened,
            "songs_partially_listened": self._songs_partially_listened,
            "initial_valence": self._initial_valence,
            "current_valence": self._current_valence,
            "events": [e.to_dict() for e in self._events],
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SessionRewardCalculator":
        """Deserialize from dictionary."""
        instance = cls(
            session_id=data["session_id"],
            user_id=data["user_id"]
        )
        instance.created_at = datetime.fromisoformat(data["created_at"])
        instance._engagement_sum = data["engagement_sum"]
        instance._engagement_count = data["engagement_count"]
        instance._satisfaction_sum = data["satisfaction_sum"]
        instance._satisfaction_count = data["satisfaction_count"]
        instance._emotional_improvement = data["emotional_improvement"]
        instance._total_recommendations = data["total_recommendations"]
        instance._accepted_recommendations = data["accepted_recommendations"]
        instance._songs_fully_listened = data["songs_fully_listened"]
        instance._songs_partially_listened = data["songs_partially_listened"]
        instance._initial_valence = data.get("initial_valence")
        instance._current_valence = data.get("current_valence", 0.0)
        
        # Events can be reconstructed if needed
        return instance


class SessionRewardStore:
    """
    In-memory store for session reward calculators.
    
    For production, replace with Redis or database-backed store.
    """
    
    def __init__(self):
        self._calculators: Dict[str, SessionRewardCalculator] = {}
    
    def get(self, session_id: str) -> Optional[SessionRewardCalculator]:
        """Get calculator by session ID."""
        return self._calculators.get(session_id)
    
    def create(self, session_id: str, user_id: int) -> SessionRewardCalculator:
        """Create new calculator."""
        calc = SessionRewardCalculator(session_id, user_id)
        self._calculators[session_id] = calc
        return calc
    
    def get_or_create(self, session_id: str, user_id: int) -> SessionRewardCalculator:
        """Get existing or create new calculator."""
        if session_id in self._calculators:
            return self._calculators[session_id]
        return self.create(session_id, user_id)
    
    def delete(self, session_id: str) -> bool:
        """Delete calculator by session ID."""
        if session_id in self._calculators:
            del self._calculators[session_id]
            return True
        return False
    
    def finalize_session(self, session_id: str) -> Optional[Dict]:
        """
        Finalize session and return final reward breakdown.
        
        This should be called when a session ends to persist the reward.
        """
        calc = self._calculators.get(session_id)
        if calc:
            breakdown = calc.get_reward_breakdown()
            # In production, persist to database here
            return breakdown
        return None
    
    def get_user_calculator(self, user_id: int) -> Optional[SessionRewardCalculator]:
        """Get calculator by user ID (most recent session)."""
        user_calcs = [
            calc for calc in self._calculators.values()
            if calc.user_id == user_id
        ]
        if not user_calcs:
            return None
        # Return most recently created
        return max(user_calcs, key=lambda c: c.created_at)
    
    def set_user_calculator(self, user_id: int, calculator: SessionRewardCalculator) -> None:
        """Store calculator for a user."""
        self._calculators[calculator.session_id] = calculator


# Global store instance
_reward_store: Optional[SessionRewardStore] = None


def get_reward_store() -> SessionRewardStore:
    """Get or create the global reward store."""
    global _reward_store
    if _reward_store is None:
        _reward_store = SessionRewardStore()
    return _reward_store
