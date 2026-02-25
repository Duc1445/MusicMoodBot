"""
=============================================================================
CONVERSATION CONTEXT MEMORY - v5.0
=============================================================================

Multi-turn conversation context management with sliding window memory.

Features:
- 10-turn sliding window with FIFO eviction
- Accumulated entity extraction (artists, genres, moods)
- Context-aware feature enrichment
- Mood trajectory tracking integration

Author: MusicMoodBot Team
Version: 5.0.0
=============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from collections import deque
import json
import re


@dataclass
class ConversationTurn:
    """Single turn in conversation."""
    turn_number: int
    user_message: str
    bot_response: str
    timestamp: datetime
    detected_mood: Optional[str] = None
    valence: float = 0.0
    arousal: float = 0.0
    intensity: float = 0.5
    confidence: float = 0.0
    entities: Dict[str, List[str]] = field(default_factory=dict)
    recommended_songs: List[int] = field(default_factory=list)
    feedback: Optional[str] = None  # like, dislike, skip, neutral
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "turn_number": self.turn_number,
            "user_message": self.user_message,
            "bot_response": self.bot_response,
            "timestamp": self.timestamp.isoformat(),
            "detected_mood": self.detected_mood,
            "valence": self.valence,
            "arousal": self.arousal,
            "intensity": self.intensity,
            "confidence": self.confidence,
            "entities": self.entities,
            "recommended_songs": self.recommended_songs,
            "feedback": self.feedback,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationTurn":
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class ConversationContextMemory:
    """
    Multi-turn conversation context with sliding window memory.
    
    Maintains a FIFO queue of conversation turns with configurable window size.
    Accumulates entities and moods across turns for context-aware recommendations.
    """
    
    DEFAULT_WINDOW_SIZE = 10
    
    def __init__(
        self,
        session_id: str,
        user_id: int,
        window_size: int = DEFAULT_WINDOW_SIZE
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.window_size = window_size
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Sliding window of turns (FIFO)
        self._turns: deque[ConversationTurn] = deque(maxlen=window_size)
        
        # Accumulated entities across all turns (not windowed)
        self._accumulated_artists: Set[str] = set()
        self._accumulated_genres: Set[str] = set()
        self._accumulated_moods: List[str] = []
        
        # Conversation state
        self._total_turns = 0
        self._positive_feedback_count = 0
        self._negative_feedback_count = 0
        self._skip_count = 0
    
    @property
    def turn_count(self) -> int:
        """Total number of turns in this session."""
        return self._total_turns
    
    @property
    def windowed_turns(self) -> List[ConversationTurn]:
        """Get turns in the current window."""
        return list(self._turns)
    
    @property
    def accumulated_moods(self) -> List[str]:
        """Get all moods detected across session."""
        return self._accumulated_moods.copy()
    
    @property
    def accumulated_artists(self) -> Set[str]:
        """Get all artists mentioned or recommended."""
        return self._accumulated_artists.copy()
    
    @property
    def accumulated_genres(self) -> Set[str]:
        """Get all genres mentioned or recommended."""
        return self._accumulated_genres.copy()
    
    def add_turn(
        self,
        user_message: str,
        bot_response: str,
        detected_mood: Optional[str] = None,
        valence: float = 0.0,
        arousal: float = 0.0,
        intensity: float = 0.5,
        confidence: float = 0.0,
        entities: Optional[Dict[str, List[str]]] = None,
        recommended_songs: Optional[List[int]] = None,
    ) -> ConversationTurn:
        """
        Add a new turn to the conversation.
        
        Args:
            user_message: User's input text
            bot_response: Bot's response text
            detected_mood: Primary detected mood
            valence: Valence score (-1 to 1)
            arousal: Arousal score (-1 to 1)
            intensity: Mood intensity (0 to 1)
            confidence: Detection confidence (0 to 1)
            entities: Extracted entities (artists, genres, etc.)
            recommended_songs: IDs of recommended songs
            
        Returns:
            The created ConversationTurn
        """
        self._total_turns += 1
        
        turn = ConversationTurn(
            turn_number=self._total_turns,
            user_message=user_message,
            bot_response=bot_response,
            timestamp=datetime.utcnow(),
            detected_mood=detected_mood,
            valence=valence,
            arousal=arousal,
            intensity=intensity,
            confidence=confidence,
            entities=entities or {},
            recommended_songs=recommended_songs or [],
        )
        
        # Add to sliding window (oldest evicted if full)
        self._turns.append(turn)
        
        # Accumulate entities
        if entities:
            if "artists" in entities:
                self._accumulated_artists.update(entities["artists"])
            if "genres" in entities:
                self._accumulated_genres.update(entities["genres"])
        
        # Accumulate moods
        if detected_mood:
            self._accumulated_moods.append(detected_mood)
        
        self.updated_at = datetime.utcnow()
        
        return turn
    
    def record_feedback(self, turn_number: int, feedback: str) -> bool:
        """
        Record feedback for a specific turn.
        
        Args:
            turn_number: Turn to update
            feedback: Feedback type (like, dislike, skip, neutral)
            
        Returns:
            True if feedback recorded successfully
        """
        for turn in self._turns:
            if turn.turn_number == turn_number:
                turn.feedback = feedback
                
                # Update counters
                if feedback in ("like", "love"):
                    self._positive_feedback_count += 1
                elif feedback == "dislike":
                    self._negative_feedback_count += 1
                elif feedback == "skip":
                    self._skip_count += 1
                
                return True
        
        return False
    
    def get_recent_moods(self, n: int = 5) -> List[str]:
        """Get n most recent detected moods."""
        moods = [t.detected_mood for t in self._turns if t.detected_mood]
        return moods[-n:] if moods else []
    
    def get_mood_trajectory(self) -> List[Dict[str, float]]:
        """
        Get valence-arousal trajectory for emotional tracking.
        
        Returns:
            List of VA points for each turn
        """
        return [
            {
                "turn": t.turn_number,
                "valence": t.valence,
                "arousal": t.arousal,
                "mood": t.detected_mood
            }
            for t in self._turns
        ]
    
    def get_context_features(self) -> Dict[str, Any]:
        """
        Extract context features for recommendation enrichment.
        
        Returns:
            Dictionary of context features
        """
        recent_turns = list(self._turns)[-5:]  # Last 5 turns
        
        # Calculate mood stability
        recent_moods = [t.detected_mood for t in recent_turns if t.detected_mood]
        unique_moods = len(set(recent_moods))
        mood_stability = 1.0 - (unique_moods - 1) / max(len(recent_moods), 1) if recent_moods else 0.5
        
        # Calculate average confidence
        avg_confidence = sum(t.confidence for t in recent_turns) / len(recent_turns) if recent_turns else 0.0
        
        # Calculate engagement rate
        total_feedback = self._positive_feedback_count + self._negative_feedback_count + self._skip_count
        engagement_rate = (self._positive_feedback_count / total_feedback) if total_feedback > 0 else 0.5
        
        # Get dominant mood
        if self._accumulated_moods:
            mood_counts = {}
            for mood in self._accumulated_moods:
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
            dominant_mood = max(mood_counts.keys(), key=lambda k: mood_counts[k])
        else:
            dominant_mood = None
        
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "turn_count": self._total_turns,
            "window_size": len(self._turns),
            "mood_stability": round(mood_stability, 3),
            "avg_confidence": round(avg_confidence, 3),
            "engagement_rate": round(engagement_rate, 3),
            "dominant_mood": dominant_mood,
            "recent_moods": recent_moods,
            "accumulated_artists": list(self._accumulated_artists),
            "accumulated_genres": list(self._accumulated_genres),
            "positive_feedback": self._positive_feedback_count,
            "negative_feedback": self._negative_feedback_count,
            "skip_count": self._skip_count,
            "session_duration_seconds": (datetime.utcnow() - self.created_at).total_seconds(),
        }
    
    def get_context_modifiers(self) -> Dict[str, float]:
        """
        Calculate context-based modifiers for recommendation scoring.
        
        Returns:
            Dictionary of modifier weights
        """
        features = self.get_context_features()
        
        modifiers = {
            # Boost mood matching if mood is stable
            "mood_stability_weight": 1.0 + (features["mood_stability"] * 0.3),
            
            # Boost diversity if engagement is dropping
            "diversity_boost": max(0.0, 0.3 - (features["engagement_rate"] * 0.3)),
            
            # Boost familiar artists if positive feedback on specific artists
            "artist_familiarity_boost": min(0.2, len(features["accumulated_artists"]) * 0.02),
            
            # Comfort music boost if emotional trajectory is declining
            "comfort_music_boost": 0.0,  # Set by EmotionalTrajectoryTracker
            
            # Exploration penalty if user shows strong preferences
            "exploration_penalty": -0.1 if features["positive_feedback"] > 5 else 0.0,
        }
        
        return modifiers
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "window_size": self.window_size,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "total_turns": self._total_turns,
            "turns": [t.to_dict() for t in self._turns],
            "accumulated_artists": list(self._accumulated_artists),
            "accumulated_genres": list(self._accumulated_genres),
            "accumulated_moods": self._accumulated_moods,
            "positive_feedback_count": self._positive_feedback_count,
            "negative_feedback_count": self._negative_feedback_count,
            "skip_count": self._skip_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContextMemory":
        """Deserialize from dictionary."""
        instance = cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            window_size=data.get("window_size", cls.DEFAULT_WINDOW_SIZE)
        )
        instance.created_at = datetime.fromisoformat(data["created_at"])
        instance.updated_at = datetime.fromisoformat(data["updated_at"])
        instance._total_turns = data["total_turns"]
        instance._accumulated_artists = set(data.get("accumulated_artists", []))
        instance._accumulated_genres = set(data.get("accumulated_genres", []))
        instance._accumulated_moods = data.get("accumulated_moods", [])
        instance._positive_feedback_count = data.get("positive_feedback_count", 0)
        instance._negative_feedback_count = data.get("negative_feedback_count", 0)
        instance._skip_count = data.get("skip_count", 0)
        
        for turn_data in data.get("turns", []):
            instance._turns.append(ConversationTurn.from_dict(turn_data))
        
        return instance


class ConversationContextStore:
    """
    In-memory store for active conversation contexts.
    
    For production, replace with Redis or database-backed store.
    """
    
    def __init__(self):
        self._contexts: Dict[str, ConversationContextMemory] = {}
    
    def get(self, session_id: str) -> Optional[ConversationContextMemory]:
        """Get context by session ID."""
        return self._contexts.get(session_id)
    
    def create(
        self,
        session_id: str,
        user_id: int,
        window_size: int = ConversationContextMemory.DEFAULT_WINDOW_SIZE
    ) -> ConversationContextMemory:
        """Create new context."""
        context = ConversationContextMemory(
            session_id=session_id,
            user_id=user_id,
            window_size=window_size
        )
        self._contexts[session_id] = context
        return context
    
    def get_or_create(
        self,
        session_id: str,
        user_id: int
    ) -> ConversationContextMemory:
        """Get existing context or create new one."""
        if session_id in self._contexts:
            return self._contexts[session_id]
        return self.create(session_id, user_id)
    
    def delete(self, session_id: str) -> bool:
        """Delete context by session ID."""
        if session_id in self._contexts:
            del self._contexts[session_id]
            return True
        return False
    
    def list_active(self, user_id: Optional[int] = None) -> List[str]:
        """List active session IDs, optionally filtered by user."""
        if user_id is None:
            return list(self._contexts.keys())
        return [
            sid for sid, ctx in self._contexts.items()
            if ctx.user_id == user_id
        ]
    
    def cleanup_stale(self, max_age_seconds: int = 3600) -> int:
        """Remove contexts older than max_age_seconds."""
        now = datetime.utcnow()
        stale = [
            sid for sid, ctx in self._contexts.items()
            if (now - ctx.updated_at).total_seconds() > max_age_seconds
        ]
        for sid in stale:
            del self._contexts[sid]
        return len(stale)
    
    def get_user_context(self, user_id: int) -> Optional[ConversationContextMemory]:
        """Get context by user ID (most recent session)."""
        user_sessions = [
            ctx for ctx in self._contexts.values()
            if ctx.user_id == user_id
        ]
        if not user_sessions:
            return None
        # Return most recently updated
        return max(user_sessions, key=lambda c: c.updated_at)
    
    def set_user_context(self, user_id: int, context: ConversationContextMemory) -> None:
        """Store context for a user."""
        self._contexts[context.session_id] = context


# Global store instance
_context_store: Optional[ConversationContextStore] = None


def get_context_store() -> ConversationContextStore:
    """Get or create the global context store."""
    global _context_store
    if _context_store is None:
        _context_store = ConversationContextStore()
    return _context_store
