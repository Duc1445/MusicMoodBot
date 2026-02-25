"""
=============================================================================
V5.0 PRODUCTION READINESS - INTEGRATION TEST
=============================================================================

FastAPI TestClient tests for v5.0 Adaptive Recommendation System.

Tests:
- POST /api/v1/v5/conversation/continue
- POST /api/v1/v5/recommendation/adaptive
- POST /api/v1/v5/learning/weights/{user_id}
- POST /api/v1/v5/feedback/reward
- GET /api/v1/v5/session/{user_id}/status
- Edge cases and error handling

Target: 1,000 concurrent users (demo scale)
Run with: pytest tests/test_v5_integration.py -v

Author: MusicMoodBot Team
=============================================================================
"""

import pytest
import sys
import os
import time
import tracemalloc
from typing import Dict, Any, List

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


class TestV5Integration:
    """Integration tests for v5.0 API."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client for each test."""
        # Import here to avoid circular imports
        from backend.main import app
        self.client = TestClient(app)
        yield
        # Cleanup (could reset stores here)
    
    # =========================================================================
    # PHASE 1.1: POST /api/v1/v5/conversation/continue
    # =========================================================================
    
    def test_conversation_continue_basic(self):
        """Test basic conversation continue."""
        payload = {
            "message": "I feel happy today!",
            "input_type": "text",
            "include_recommendations": False
        }
        
        response = self.client.post(
            "/api/v1/v5/conversation/continue",
            json=payload
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response schema
        assert "session_id" in data
        assert "turn_number" in data
        assert "bot_response" in data
        assert "detected_mood" in data
        assert "emotional_trend" in data
        assert "clarity_score" in data
        assert "should_recommend" in data
        
        # Verify types
        assert isinstance(data["session_id"], str)
        assert isinstance(data["turn_number"], int)
        assert isinstance(data["bot_response"], str)
        assert data["turn_number"] >= 1
    
    def test_conversation_continue_with_recommendations(self):
        """Test conversation with recommendations enabled."""
        payload = {
            "message": "Play something calm and relaxing",
            "input_type": "text",
            "include_recommendations": True,
            "max_recommendations": 5,
            "emotional_support_mode": False
        }
        
        response = self.client.post(
            "/api/v1/v5/conversation/continue",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Recommendations may or may not be present depending on clarity
        if data["should_recommend"] and data.get("recommendations"):
            assert isinstance(data["recommendations"], list)
    
    def test_conversation_multi_turn_state_persistence(self):
        """Test state persists across multiple turns."""
        # Use a unique session to isolate this test
        session_id = f"test_session_{int(time.time())}"
        
        messages = [
            "Hi, I'm feeling a bit down today",
            "Maybe some relaxing music would help",
            "I like indie and acoustic music",
        ]
        
        turn_numbers = []
        for i, msg in enumerate(messages):
            payload = {
                "message": msg,
                "session_id": session_id,
                "input_type": "text",
                "include_recommendations": False
            }
            
            response = self.client.post(
                "/api/v1/v5/conversation/continue",
                json=payload
            )
            
            assert response.status_code == 200, f"Turn {i+1} failed: {response.text}"
            data = response.json()
            turn_numbers.append(data["turn_number"])
        
        # Turn numbers should be monotonically increasing
        assert turn_numbers == sorted(turn_numbers), f"Turn numbers not increasing: {turn_numbers}"
        assert len(set(turn_numbers)) == len(turn_numbers), f"Duplicate turn numbers: {turn_numbers}"
        
        # Final response should accumulate entities from conversation
        assert "context_entities" in data
    
    def test_conversation_emotional_support_mode(self):
        """Test emotional support mode activation."""
        payload = {
            "message": "I'm feeling really sad and stressed",
            "input_type": "text",
            "include_recommendations": True,
            "emotional_support_mode": True
        }
        
        response = self.client.post(
            "/api/v1/v5/conversation/continue",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Emotional trend should be tracked (any valid value)
        assert data["emotional_trend"] in ["stable", "improving", "declining", "volatile"]
    
    # =========================================================================
    # PHASE 1.2: POST /api/v1/v5/recommendation/adaptive
    # =========================================================================
    
    def test_adaptive_recommendation_basic(self):
        """Test basic adaptive recommendation."""
        payload = {
            "mood": "happy",
            "energy_level": 0.7,
            "limit": 5,
            "use_context_memory": False,
            "use_emotional_trajectory": False,
            "apply_cold_start": True,
            "include_explanations": True
        }
        
        response = self.client.post(
            "/api/v1/v5/recommendation/adaptive",
            json=payload
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response schema
        assert "recommendations" in data
        assert "strategy_used" in data
        assert "personalization_weight" in data
        assert "cold_start_active" in data
        assert "processing_time_ms" in data
        
        # Verify types
        assert isinstance(data["recommendations"], list)
        assert isinstance(data["personalization_weight"], (int, float))
        assert 0 <= data["personalization_weight"] <= 1
    
    def test_adaptive_recommendation_with_context(self):
        """Test recommendations using context memory."""
        # First, build context
        self.client.post(
            "/api/v1/v5/conversation/continue",
            json={"message": "I love Taylor Swift", "input_type": "text"}
        )
        
        # Then request recommendations 
        payload = {
            "mood": "calm",
            "limit": 10,
            "use_context_memory": True,
            "use_emotional_trajectory": True,
            "diversity_factor": 0.5
        }
        
        response = self.client.post(
            "/api/v1/v5/recommendation/adaptive",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["diversity_applied"] == True
    
    def test_adaptive_recommendation_valence_arousal(self):
        """Test recommendations with VA space parameters."""
        payload = {
            "valence": 0.8,
            "arousal": 0.5,
            "limit": 5,
            "include_explanations": True,
            "explanation_verbosity": "detailed"
        }
        
        response = self.client.post(
            "/api/v1/v5/recommendation/adaptive",
            json=payload
        )
        
        assert response.status_code == 200
    
    # =========================================================================
    # PHASE 1.3: POST /api/v1/v5/learning/weights/{user_id}
    # =========================================================================
    
    def test_weight_update_feedback(self):
        """Test weight update via feedback."""
        payload = {
            "adjustment_type": "feedback",
            "feedback_type": "like",
            "song_features": {
                "valence": 0.7,
                "energy": 0.6,
                "danceability": 0.5
            }
        }
        
        response = self.client.post(
            "/api/v1/v5/learning/weights/1",
            json=payload
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response schema
        assert "success" in data
        assert "updated_weights" in data
        assert "adjustment_magnitude" in data
        
        assert data["success"] == True
        assert isinstance(data["updated_weights"], dict)
    
    def test_weight_update_explicit(self):
        """Test explicit weight setting."""
        payload = {
            "adjustment_type": "explicit",
            "explicit_weights": {
                "valence": 0.8,
                "energy": 0.6,
                "tempo": 0.5,
                "danceability": 0.4
            }
        }
        
        response = self.client.post(
            "/api/v1/v5/learning/weights/1",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_weight_update_reset(self):
        """Test weight reset to defaults."""
        payload = {
            "adjustment_type": "reset"
        }
        
        response = self.client.post(
            "/api/v1/v5/learning/weights/1",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    # =========================================================================
    # PHASE 1.4: Additional Endpoints
    # =========================================================================
    
    def test_feedback_reward(self):
        """Test feedback with reward calculation."""
        payload = {
            "song_id": 123,
            "feedback_type": "like",
            "play_duration_seconds": 180,
            "song_duration_seconds": 210
        }
        
        response = self.client.post(
            "/api/v1/v5/feedback/reward",
            json=payload
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert "engagement_score" in data
        assert "satisfaction_score" in data
        assert "total_reward" in data
        
        # Scores should be in valid range
        assert 0 <= data["engagement_score"] <= 1
        assert 0 <= data["satisfaction_score"] <= 1
        assert 0 <= data["total_reward"] <= 1
    
    def test_session_status(self):
        """Test session status retrieval."""
        # First create some activity
        self.client.post(
            "/api/v1/v5/conversation/continue",
            json={"message": "Hello!", "input_type": "text"}
        )
        
        response = self.client.get("/api/v1/v5/session/1/status")
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "user_id" in data
        assert "context_memory" in data
        assert "emotional_trajectory" in data
        assert "session_rewards" in data
        assert "personalization_weights" in data
        assert "cold_start_status" in data
    
    # =========================================================================
    # PHASE 2: EDGE CASES
    # =========================================================================
    
    def test_edge_empty_message(self):
        """Test handling of empty message - should fail validation."""
        payload = {
            "message": "",
            "input_type": "text"
        }
        
        response = self.client.post(
            "/api/v1/v5/conversation/continue",
            json=payload
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422
    
    def test_edge_max_length_message(self):
        """Test max length message (1000 chars)."""
        long_message = "A" * 1000
        payload = {
            "message": long_message,
            "input_type": "text"
        }
        
        response = self.client.post(
            "/api/v1/v5/conversation/continue",
            json=payload
        )
        
        # Should succeed at boundary
        assert response.status_code == 200
    
    def test_edge_over_max_length_message(self):
        """Test over max length message (1001 chars)."""
        long_message = "A" * 1001
        payload = {
            "message": long_message,
            "input_type": "text"
        }
        
        response = self.client.post(
            "/api/v1/v5/conversation/continue",
            json=payload
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422
    
    def test_edge_50_turn_conversation(self):
        """Test 50-turn conversation (stress test)."""
        # Use unique session for isolation
        session_id = f"stress_test_{int(time.time())}"
        first_turn = None
        
        for i in range(50):
            payload = {
                "message": f"This is message number {i+1}",
                "session_id": session_id,
                "input_type": "text",
                "include_recommendations": False
            }
            
            response = self.client.post(
                "/api/v1/v5/conversation/continue",
                json=payload
            )
            
            assert response.status_code == 200, f"Failed at turn {i+1}"
            data = response.json()
            
            if first_turn is None:
                first_turn = data["turn_number"]
        
        # Should have processed all 50 turns (relative to start)
        assert data["turn_number"] == first_turn + 49
    
    def test_edge_invalid_feedback_type(self):
        """Test invalid feedback type."""
        payload = {
            "song_id": 123,
            "feedback_type": "invalid_type",
            "play_duration_seconds": 100,
            "song_duration_seconds": 200
        }
        
        response = self.client.post(
            "/api/v1/v5/feedback/reward",
            json=payload
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422
    
    def test_edge_extreme_weight_values(self):
        """Test extreme weight values (boundary)."""
        payload = {
            "adjustment_type": "explicit",
            "explicit_weights": {
                "valence": 1.0,
                "energy": 0.0,
                "tempo": 0.5
            }
        }
        
        response = self.client.post(
            "/api/v1/v5/learning/weights/1",
            json=payload
        )
        
        assert response.status_code == 200
    
    def test_edge_unauthorized_cross_user_access(self):
        """Test that users cannot access other users' sessions."""
        # User ID 1 tries to access user 2's session
        response = self.client.get("/api/v1/v5/session/2/status")
        
        # Should return 403 Forbidden
        assert response.status_code == 403
    
    def test_edge_no_mood_recommendation(self):
        """Test recommendation with no mood specified."""
        payload = {
            "limit": 5,
            "use_context_memory": False,
            "apply_cold_start": True
        }
        
        response = self.client.post(
            "/api/v1/v5/recommendation/adaptive",
            json=payload
        )
        
        # Should still succeed with default handling
        assert response.status_code == 200
    
    def test_edge_energy_boundaries(self):
        """Test energy level boundary values."""
        # Test at 0.0
        response = self.client.post(
            "/api/v1/v5/recommendation/adaptive",
            json={"energy_level": 0.0, "limit": 3}
        )
        assert response.status_code == 200
        
        # Test at 1.0
        response = self.client.post(
            "/api/v1/v5/recommendation/adaptive",
            json={"energy_level": 1.0, "limit": 3}
        )
        assert response.status_code == 200
    
    # =========================================================================
    # PHASE 3: PERFORMANCE BASELINE
    # =========================================================================
    
    def test_performance_conversation_latency(self):
        """Test conversation endpoint latency."""
        payload = {
            "message": "Test message for latency check",
            "input_type": "text",
            "include_recommendations": False
        }
        
        times = []
        for _ in range(10):
            start = time.time()
            response = self.client.post(
                "/api/v1/v5/conversation/continue",
                json=payload
            )
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            assert response.status_code == 200
        
        avg_latency = sum(times) / len(times)
        max_latency = max(times)
        
        print(f"\nConversation Latency: avg={avg_latency:.1f}ms, max={max_latency:.1f}ms")
        
        # Should be under 500ms for demo
        assert max_latency < 500, f"Max latency {max_latency}ms exceeds threshold"
    
    def test_performance_recommendation_latency(self):
        """Test recommendation endpoint latency."""
        payload = {
            "mood": "calm",
            "limit": 10,
            "use_context_memory": True,
            "include_explanations": True
        }
        
        times = []
        for _ in range(10):
            start = time.time()
            response = self.client.post(
                "/api/v1/v5/recommendation/adaptive",
                json=payload
            )
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            assert response.status_code == 200
        
        avg_latency = sum(times) / len(times)
        max_latency = max(times)
        
        print(f"\nRecommendation Latency: avg={avg_latency:.1f}ms, max={max_latency:.1f}ms")
        
        # Should be under 1000ms for demo
        assert max_latency < 1000, f"Max latency {max_latency}ms exceeds threshold"


# =============================================================================
# MEMORY ESTIMATION TEST
# =============================================================================

class TestMemoryEstimation:
    """Tests for memory usage estimation."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client for each test."""
        from backend.main import app
        self.client = TestClient(app)
        yield
    
    def test_memory_per_session(self):
        """Estimate memory per session."""
        tracemalloc.start()
        
        # Simulate one user session with 10 turns
        session_id = None
        for i in range(10):
            payload = {
                "message": f"Test message for memory estimation {i}",
                "session_id": session_id,
                "input_type": "text",
                "include_recommendations": False
            }
            response = self.client.post(
                "/api/v1/v5/conversation/continue",
                json=payload
            )
            if session_id is None:
                session_id = response.json()["session_id"]
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\nMemory: current={current/1024:.1f}KB, peak={peak/1024:.1f}KB")
        
        # Rough estimate: ~50KB per session is reasonable for sliding window
        # This gives ~50MB for 1000 users which is acceptable


# =============================================================================
# RUN INTEGRATION TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
