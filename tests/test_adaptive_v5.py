"""
=============================================================================
ADAPTIVE RECOMMENDATION v5.0 - TEST SUITE
=============================================================================

Unit tests for the v5.0 Adaptive Recommendation System.

Test Coverage:
- ConversationContextMemory
- EmotionalTrajectoryTracker
- SessionRewardCalculator
- ScoringEngine (Thompson Sampling)
- WeightAdapter
- ColdStartHandler
- API Endpoints

Author: MusicMoodBot Team
Version: 5.0.0

Run with: pytest tests/test_adaptive_v5.py -v
=============================================================================
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.conversation.conversation_context import (
    ConversationTurn,
    ConversationContextMemory,
    ConversationContextStore,
)
from backend.services.conversation.emotional_trajectory import (
    VAPoint,
    EmotionalTrend,
    EmotionalTrajectoryTracker,
    mood_to_va,
    va_to_mood,
)
from backend.services.conversation.session_reward import (
    FeedbackType,
    RewardEvent,
    SessionRewardCalculator,
)
from backend.services.recommendation.scoring_engine import (
    ScoredSong,
    ThompsonSamplingBandit,
    ScoringEngine,
)
from backend.services.recommendation.weight_adapter import (
    WeightAdapter,
    DEFAULT_WEIGHTS,
)
from backend.services.recommendation.cold_start import (
    ColdStartSong,
    ColdStartHandler,
    ColdStartTransitionManager,
)


# =============================================================================
# CONVERSATION CONTEXT TESTS
# =============================================================================

class TestConversationContext:
    """Tests for ConversationContextMemory."""
    
    def test_create_context(self):
        """Test creating a new context."""
        context = ConversationContextMemory(session_id="test_session", user_id=1, window_size=10)
        assert context.user_id == 1
        assert context.window_size == 10
        assert context.turn_count == 0
    
    def test_add_turn(self):
        """Test adding turns to context."""
        context = ConversationContextMemory(session_id="test_session", user_id=1, window_size=10)
        
        turn = ConversationTurn(
            turn_id=1,
            user_input="I feel happy today",
            input_type="text",
            timestamp=datetime.now(),
            detected_mood="happy",
            mood_confidence=0.85,
        )
        
        context.add_turn(turn)
        assert context.turn_count == 1
        assert context.windowed_turns[0].detected_mood == "happy"
    
    def test_sliding_window_eviction(self):
        """Test FIFO eviction when max turns exceeded."""
        context = ConversationContextMemory(session_id="test_session", user_id=1, window_size=3)
        
        for i in range(5):
            turn = ConversationTurn(
                turn_id=i + 1,
                user_input=f"Message {i}",
                input_type="text",
                timestamp=datetime.now(),
            )
            context.add_turn(turn)
        
        # Should only have 3 turns in window (oldest evicted)
        assert len(context.windowed_turns) == 3
        assert context.windowed_turns[0].turn_id == 3  # First turn is now turn 3
    
    def test_entity_accumulation(self):
        """Test that entities accumulate across turns."""
        context = ConversationContextMemory(session_id="test_session", user_id=1, window_size=10)
        
        # First turn with artist
        turn1 = ConversationTurn(
            turn_id=1,
            user_input="Play some Taylor Swift",
            input_type="text",
            timestamp=datetime.now(),
            extracted_entities={"artists": ["Taylor Swift"]},
        )
        context.add_turn(turn1)
        
        # Second turn with genre
        turn2 = ConversationTurn(
            turn_id=2,
            user_input="I like pop music",
            input_type="text",
            timestamp=datetime.now(),
            extracted_entities={"genres": ["pop"]},
        )
        context.add_turn(turn2)
        
        assert "Taylor Swift" in context.accumulated_artists
        assert "pop" in context.accumulated_genres
    
    def test_context_modifiers(self):
        """Test context modifier calculation."""
        context = ConversationContextMemory(session_id="test_session", user_id=1, window_size=10)
        
        # Add turn with mood
        turn = ConversationTurn(
            turn_id=1,
            user_input="I feel calm",
            input_type="text",
            timestamp=datetime.now(),
            detected_mood="calm",
            mood_confidence=0.9,
        )
        context.add_turn(turn)
        
        modifiers = context.get_context_modifiers()
        assert "recent_mood" in modifiers
        assert modifiers.get("mood_confidence", 0) > 0
    
    def test_to_dict_from_dict(self):
        """Test serialization/deserialization."""
        context = ConversationContextMemory(session_id="test_session", user_id=1, window_size=10)
        turn = ConversationTurn(
            turn_id=1,
            user_input="Test",
            input_type="text",
            timestamp=datetime.now(),
        )
        context.add_turn(turn)
        
        data = context.to_dict()
        restored = ConversationContextMemory.from_dict(data)
        
        assert restored.user_id == context.user_id
        assert restored.turn_count == context.turn_count


class TestConversationContextStore:
    """Tests for ConversationContextStore."""
    
    def test_store_get_context(self):
        """Test storing and retrieving context."""
        store = ConversationContextStore()
        context = ConversationContextMemory(session_id="test_session", user_id=42, window_size=10)
        
        store.set_user_context(42, context)
        retrieved = store.get_user_context(42)
        
        assert retrieved is not None
        assert retrieved.user_id == 42
    
    def test_store_nonexistent_user(self):
        """Test getting context for nonexistent user."""
        store = ConversationContextStore()
        result = store.get_user_context(9999)
        assert result is None


# =============================================================================
# EMOTIONAL TRAJECTORY TESTS
# =============================================================================

class TestEmotionalTrajectory:
    """Tests for EmotionalTrajectoryTracker."""
    
    def test_mood_to_va_mapping(self):
        """Test mood to VA-space mapping."""
        va = mood_to_va("happy")
        assert va.valence > 0
        assert va.arousal > 0
        
        va = mood_to_va("sad")
        assert va.valence < 0
    
    def test_va_to_mood_mapping(self):
        """Test VA-space to mood mapping."""
        mood = va_to_mood(0.8, 0.6)
        assert mood == "happy"
        
        mood = va_to_mood(-0.7, -0.3)
        assert mood == "sad"
    
    def test_trajectory_tracking(self):
        """Test tracking multiple mood points."""
        tracker = EmotionalTrajectoryTracker()
        
        tracker.add_mood(1, "sad")
        tracker.add_mood(1, "sad")
        tracker.add_mood(1, "neutral")
        tracker.add_mood(1, "happy")
        
        trend = tracker.get_trend(1)
        assert trend == EmotionalTrend.IMPROVING
    
    def test_declining_trend(self):
        """Test detecting declining emotional trend."""
        tracker = EmotionalTrajectoryTracker()
        
        tracker.add_mood(1, "happy")
        tracker.add_mood(1, "happy")
        tracker.add_mood(1, "neutral")
        tracker.add_mood(1, "sad")
        
        trend = tracker.get_trend(1)
        assert trend == EmotionalTrend.DECLINING
    
    def test_comfort_boost(self):
        """Test comfort boost calculation."""
        tracker = EmotionalTrajectoryTracker()
        
        # Create declining trend
        tracker.add_mood(1, "happy")
        tracker.add_mood(1, "neutral")
        tracker.add_mood(1, "sad")
        tracker.add_mood(1, "sad")
        
        boost = tracker.get_comfort_boost(1)
        assert boost > 0  # Should have some boost for declining trend


# =============================================================================
# SESSION REWARD TESTS
# =============================================================================

class TestSessionReward:
    """Tests for SessionRewardCalculator."""
    
    def test_create_calculator(self):
        """Test creating a reward calculator."""
        calc = SessionRewardCalculator(session_id="test_session", user_id=1)
        assert calc.user_id == 1
        assert len(calc.events) == 0
    
    def test_record_feedback(self):
        """Test recording feedback events."""
        calc = SessionRewardCalculator(session_id="test_session", user_id=1)
        
        calc.record_feedback(
            song_id=123,
            feedback="like",
            listen_duration_pct=90.0,
        )
        
        assert len(calc.events) == 1
        assert calc.events[0].feedback == "like"
    
    def test_engagement_score(self):
        """Test engagement score calculation."""
        calc = SessionRewardCalculator(session_id="test_session", user_id=1)
        
        # Full play + like = high engagement
        calc.record_feedback(
            song_id=1,
            feedback="like",
            listen_duration_pct=100.0,
        )
        calc.record_feedback(
            song_id=2,
            feedback="like",
            listen_duration_pct=80.0,
        )
        
        score = calc.calculate_engagement_score()
        assert score > 0.5
    
    def test_satisfaction_score(self):
        """Test satisfaction score calculation."""
        calc = SessionRewardCalculator(session_id="test_session", user_id=1)
        
        # Mostly likes
        calc.record_feedback(song_id=1, feedback="like", listen_duration_pct=80.0)
        calc.record_feedback(song_id=2, feedback="like", listen_duration_pct=80.0)
        calc.record_feedback(song_id=3, feedback="love", listen_duration_pct=100.0)
        
        score = calc.calculate_satisfaction_score()
        assert score > 0.7
    
    def test_session_reward_formula(self):
        """Test composite reward formula."""
        calc = SessionRewardCalculator(session_id="test_session", user_id=1)
        
        # Positive feedback
        calc.record_feedback(song_id=1, feedback="like", listen_duration_pct=90.0)
        
        reward = calc.calculate_session_reward()
        
        # Verify reward is in valid range
        assert 0 <= reward <= 1
    
    def test_bandit_reward_conversion(self):
        """Test converting session reward for bandit update."""
        calc = SessionRewardCalculator(session_id="test_session", user_id=1)
        calc.record_feedback(song_id=1, feedback="like", listen_duration_pct=80.0)
        
        bandit_reward = calc.get_bandit_reward()
        # Bandit reward should be 0 or 1 (binary)
        assert bandit_reward in [0, 1]


# =============================================================================
# SCORING ENGINE TESTS
# =============================================================================

class TestThompsonSamplingBandit:
    """Tests for ThompsonSamplingBandit."""
    
    def test_create_bandit(self):
        """Test creating a bandit."""
        bandit = ThompsonSamplingBandit(n_strategies=5)
        assert bandit.n_strategies == 5
        assert len(bandit.alphas) == 5
        assert len(bandit.betas) == 5
    
    def test_select_strategy(self):
        """Test strategy selection."""
        bandit = ThompsonSamplingBandit(n_strategies=5)
        
        strategy = bandit.select_strategy()
        assert 0 <= strategy < 5
    
    def test_update_bandit(self):
        """Test updating bandit after reward."""
        bandit = ThompsonSamplingBandit(n_strategies=5)
        initial_alpha = bandit.alphas[0]
        
        bandit.update(strategy=0, reward=1)
        
        # Alpha should increase with reward=1
        assert bandit.alphas[0] > initial_alpha


class TestScoringEngine:
    """Tests for ScoringEngine."""
    
    def test_create_engine(self):
        """Test creating scoring engine."""
        engine = ScoringEngine()
        assert engine.bandit is not None
    
    def test_scored_song_dataclass(self):
        """Test ScoredSong dataclass."""
        song = ScoredSong(
            song_id=1,
            name="Test Song",
            artist="Test Artist",
            genre="pop",
            score=0.85,
            strategy="emotion",
            explanation="Great match",
        )
        
        data = song.to_dict()
        assert data["song_id"] == 1
        assert data["score"] == 0.85


# =============================================================================
# WEIGHT ADAPTER TESTS
# =============================================================================

class TestWeightAdapter:
    """Tests for WeightAdapter."""
    
    def test_default_weights(self):
        """Test getting default weights."""
        adapter = WeightAdapter()
        weights = adapter.get_weights(user_id=1)
        
        assert "valence" in weights
        assert "energy" in weights
        assert weights["valence"] == 1.0
    
    def test_adjust_weights_like(self):
        """Test weight adjustment for like feedback."""
        adapter = WeightAdapter()
        
        initial_weights = adapter.get_weights(user_id=1).copy()
        
        # Like a song with high energy
        adapter.adjust_weights(
            user_id=1,
            feedback_type="like",
            song_features={"energy": 0.8, "valence": 0.6},
        )
        
        new_weights = adapter.get_weights(user_id=1)
        
        # Energy weight should increase slightly
        assert new_weights["energy"] >= initial_weights["energy"]
    
    def test_adjust_weights_dislike(self):
        """Test weight adjustment for dislike feedback."""
        adapter = WeightAdapter()
        
        adapter.adjust_weights(
            user_id=1,
            feedback_type="dislike",
            song_features={"energy": 0.9},
        )
        
        weights = adapter.get_weights(user_id=1)
        # Weight should decrease but stay non-negative
        assert weights["energy"] >= 0
    
    def test_weight_decay(self):
        """Test L2 weight decay regularization."""
        adapter = WeightAdapter()
        
        # Set high weight
        adapter.set_weights(user_id=1, weights={"valence": 2.0})
        
        # Apply feedback to trigger decay
        adapter.adjust_weights(
            user_id=1,
            feedback_type="neutral",
            song_features={"energy": 0.5},
        )
        
        weights = adapter.get_weights(user_id=1)
        # Valence should have decayed slightly toward 1.0
        assert weights["valence"] < 2.0


# =============================================================================
# COLD START TESTS
# =============================================================================

class TestColdStartHandler:
    """Tests for ColdStartHandler."""
    
    def test_cold_start_threshold(self):
        """Test cold start detection threshold."""
        handler = ColdStartHandler()
        assert handler.COLD_START_THRESHOLD == 10
    
    def test_personalization_weight(self):
        """Test personalization weight calculation."""
        handler = ColdStartHandler()
        
        # Mock feedback count
        with patch.object(handler, '_get_user_feedback_count', return_value=0):
            pw = handler.get_personalization_weight(user_id=1)
            assert pw == 0.0
        
        with patch.object(handler, '_get_user_feedback_count', return_value=15):
            pw = handler.get_personalization_weight(user_id=1)
            assert 0 < pw < 1.0
        
        with patch.object(handler, '_get_user_feedback_count', return_value=50):
            pw = handler.get_personalization_weight(user_id=1)
            assert pw == 1.0
    
    def test_cold_start_song_dataclass(self):
        """Test ColdStartSong dataclass."""
        song = ColdStartSong(
            song_id=1,
            name="Popular Song",
            artist="Popular Artist",
            genre="pop",
            mood="happy",
            score=0.9,
            strategy="popularity_baseline",
            explanation="Trending song",
        )
        
        data = song.to_dict()
        assert data["strategy"] == "popularity_baseline"


class TestColdStartTransitionManager:
    """Tests for ColdStartTransitionManager."""
    
    def test_blend_recommendations(self):
        """Test blending cold start and personalized recommendations."""
        handler = ColdStartHandler()
        manager = ColdStartTransitionManager(handler)
        
        cold_songs = [
            ColdStartSong(
                song_id=1, name="Cold 1", artist="A", genre="pop",
                mood="happy", score=0.9, strategy="cold", explanation=""
            )
        ]
        
        personalized = [{"song_id": 2, "name": "Personal 1"}]
        
        with patch.object(handler, 'get_personalization_weight', return_value=0.5):
            blended, weights = manager.blend_recommendations(
                user_id=1,
                cold_start_songs=cold_songs,
                personalized_songs=personalized,
                limit=2,
            )
            
            assert weights["personalization_weight"] == 0.5
            assert weights["cold_start_weight"] == 0.5


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_session_flow(self):
        """Test full session flow from context to recommendations."""
        # Create context
        context = ConversationContextMemory(user_id=1)
        
        # Add turns
        for i, mood in enumerate(["neutral", "sad", "sad"]):
            turn = ConversationTurn(
                turn_id=i + 1,
                user_input=f"Message {i}",
                input_type="text",
                timestamp=datetime.now(),
                detected_mood=mood,
                mood_confidence=0.8,
            )
            context.add_turn(turn)
        
        # Track emotional trajectory
        tracker = EmotionalTrajectoryTracker()
        for turn in context.turns:
            if turn.detected_mood:
                tracker.add_mood(1, turn.detected_mood)
        
        # Check trend
        trend = tracker.get_trend(1)
        assert trend == EmotionalTrend.DECLINING
        
        # Get comfort boost
        boost = tracker.get_comfort_boost(1)
        assert boost > 0
        
        # Calculate rewards
        calc = SessionRewardCalculator(user_id=1)
        calc.record_feedback(song_id=1, feedback_type=FeedbackType.LIKE)
        reward = calc.calculate_session_reward()
        assert 0 <= reward <= 1


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
