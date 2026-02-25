# MusicMoodBot v5.0 API - curl Examples

This document provides example curl requests for the v5.0 Adaptive Recommendation System.

## Prerequisites

Start the backend server:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

## Authentication

All endpoints require authentication. Include the JWT token in the Authorization header:
```bash
AUTH_TOKEN="your_jwt_token_here"
```

---

## 1. Continue Conversation

Continue a multi-turn conversation with context awareness.

### Basic Request
```bash
curl -X POST "http://localhost:8000/api/v1/v5/conversation/continue" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "message": "Hôm nay mình cảm thấy hơi buồn...",
    "input_type": "text",
    "include_recommendations": false
  }'
```

### With Recommendations and Emotional Support
```bash
curl -X POST "http://localhost:8000/api/v1/v5/conversation/continue" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "message": "Tôi muốn nghe nhạc để thư giãn sau ngày làm việc mệt mỏi",
    "input_type": "text",
    "include_recommendations": true,
    "max_recommendations": 5,
    "emotional_support_mode": true,
    "session_id": "session_1_1234567890"
  }'
```

### Expected Response
```json
{
  "session_id": "session_1_1234567890",
  "turn_number": 1,
  "bot_response": "Mình hiểu. Bạn đang buồn vì chuyện gì vậy?",
  "detected_mood": "sad",
  "mood_confidence": 0.85,
  "emotional_trend": "stable",
  "comfort_boost_applied": false,
  "clarity_score": 0.45,
  "context_entities": {
    "artists": [],
    "genres": [],
    "moods": ["sad"]
  },
  "should_recommend": false,
  "recommendations": null,
  "processing_time_ms": 120
}
```

---

## 2. Adaptive Recommendations

Get context-aware recommendations with emotional trajectory consideration.

### Basic Request
```bash
curl -X POST "http://localhost:8000/api/v1/v5/recommendation/adaptive" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "mood": "calm",
    "energy_level": 0.3,
    "limit": 10,
    "include_explanations": true
  }'
```

### Full Request with All Options
```bash
curl -X POST "http://localhost:8000/api/v1/v5/recommendation/adaptive" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "mood": "happy",
    "energy_level": 0.7,
    "valence": 0.6,
    "arousal": 0.5,
    "limit": 10,
    "use_context_memory": true,
    "use_emotional_trajectory": true,
    "apply_cold_start": true,
    "diversity_factor": 0.3,
    "include_explanations": true,
    "explanation_verbosity": "detailed",
    "session_context": {
      "time_of_day": "evening",
      "activity": "relaxing"
    }
  }'
```

### Expected Response
```json
{
  "recommendations": [
    {
      "song_id": 123,
      "name": "Peaceful Morning",
      "artist": "Chill Vibes",
      "mood": "calm",
      "energy": 0.3,
      "score": 0.95,
      "strategy": "adaptive_v5",
      "explanation": "Selected based on your calm mood, emotional trend (stable), and listening history"
    }
  ],
  "strategy_used": "adaptive_v5",
  "personalization_weight": 0.75,
  "cold_start_active": false,
  "emotional_trend": "stable",
  "context_modifiers": {
    "recent_mood": 0.8,
    "mood_confidence": 0.85
  },
  "total_candidates": 20,
  "diversity_applied": true,
  "processing_time_ms": 85
}
```

---

## 3. Submit Feedback with Reward

Submit feedback for reinforcement learning reward calculation.

### Like with Play Duration
```bash
curl -X POST "http://localhost:8000/api/v1/v5/feedback/reward" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "song_id": 123,
    "feedback_type": "like",
    "play_duration_seconds": 180,
    "song_duration_seconds": 210,
    "context": {
      "song_features": {
        "valence": 0.7,
        "energy": 0.6,
        "danceability": 0.5
      }
    }
  }'
```

### Skip Feedback
```bash
curl -X POST "http://localhost:8000/api/v1/v5/feedback/reward" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "song_id": 456,
    "feedback_type": "skip",
    "play_duration_seconds": 15,
    "song_duration_seconds": 180
  }'
```

### Love Feedback (Strong Positive)
```bash
curl -X POST "http://localhost:8000/api/v1/v5/feedback/reward" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "song_id": 789,
    "feedback_type": "love"
  }'
```

### Expected Response
```json
{
  "success": true,
  "session_reward_updated": true,
  "engagement_score": 0.85,
  "satisfaction_score": 0.8,
  "emotional_alignment": 0.7,
  "total_reward": 0.78,
  "weights_updated": true
}
```

---

## 4. Get Session Status

Get comprehensive status of user's session including all v5.0 components.

```bash
curl -X GET "http://localhost:8000/api/v1/v5/session/1/status" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

### Expected Response
```json
{
  "user_id": 1,
  "active_session_id": "session_1",
  "context_memory": {
    "turn_count": 3,
    "accumulated_entities": {
      "artists": ["Taylor Swift"],
      "genres": ["pop"],
      "moods": ["happy", "excited"]
    },
    "window_size": 10
  },
  "emotional_trajectory": {
    "current_trend": "improving",
    "data_points": 5
  },
  "session_rewards": {
    "engagement_score": 0.75,
    "satisfaction_score": 0.82,
    "total_reward": 0.72
  },
  "personalization_weights": {
    "valence": 1.05,
    "energy": 1.12,
    "danceability": 0.98,
    "acousticness": 1.0,
    "instrumentalness": 1.0,
    "tempo_match": 1.0,
    "mood_match": 1.15,
    "artist_familiarity": 1.08,
    "genre_match": 1.03
  },
  "cold_start_status": {
    "is_cold_start": false,
    "personalization_weight": 1.0,
    "transition_threshold": 30
  }
}
```

---

## 5. Update Personalization Weights

Update user's personalization weights.

### Feedback-Based Adjustment
```bash
curl -X POST "http://localhost:8000/api/v1/v5/learning/weights/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "adjustment_type": "feedback",
    "feedback_type": "like",
    "song_features": {
      "valence": 0.8,
      "energy": 0.7,
      "danceability": 0.6
    }
  }'
```

### Explicit Weight Setting
```bash
curl -X POST "http://localhost:8000/api/v1/v5/learning/weights/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "adjustment_type": "explicit",
    "explicit_weights": {
      "valence": 1.2,
      "energy": 1.5,
      "mood_match": 1.3
    }
  }'
```

### Reset Weights to Default
```bash
curl -X POST "http://localhost:8000/api/v1/v5/learning/weights/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "adjustment_type": "reset"
  }'
```

### Expected Response
```json
{
  "success": true,
  "updated_weights": {
    "valence": 1.05,
    "energy": 1.08,
    "danceability": 1.02,
    "acousticness": 1.0,
    "instrumentalness": 1.0,
    "tempo_match": 1.0,
    "mood_match": 1.0,
    "artist_familiarity": 1.0,
    "genre_match": 1.0
  },
  "adjustment_magnitude": 0.15,
  "total_adjustments": 5
}
```

---

## 6. Complete Conversation Flow Example

Here's a complete example of a multi-turn conversation with recommendations:

### Turn 1: Initial Greeting
```bash
curl -X POST "http://localhost:8000/api/v1/v5/conversation/continue" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "message": "Chào bạn, hôm nay mình hơi mệt",
    "input_type": "text"
  }'
```

### Turn 2: Provide More Context
```bash
curl -X POST "http://localhost:8000/api/v1/v5/conversation/continue" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "message": "Mình muốn nghe nhạc nhẹ nhàng để thư giãn",
    "session_id": "session_from_turn_1",
    "input_type": "text"
  }'
```

### Turn 3: Get Recommendations
```bash
curl -X POST "http://localhost:8000/api/v1/v5/conversation/continue" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "message": "Thể loại ballad thì tốt",
    "session_id": "session_from_turn_1",
    "input_type": "text",
    "include_recommendations": true,
    "max_recommendations": 5,
    "emotional_support_mode": true
  }'
```

### Provide Feedback on Recommendation
```bash
curl -X POST "http://localhost:8000/api/v1/v5/feedback/reward" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "song_id": 123,
    "feedback_type": "like",
    "session_id": "session_from_turn_1",
    "play_duration_seconds": 200,
    "song_duration_seconds": 240
  }'
```

---

## Error Handling

### Session Not Found
```json
{
  "detail": "Session not found"
}
```

### Invalid Request
```json
{
  "detail": [
    {
      "loc": ["body", "mood"],
      "msg": "Invalid mood value",
      "type": "value_error"
    }
  ]
}
```

### Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

---

## Testing Tips

1. **Get Auth Token First**: Use the `/api/v1/auth/login` endpoint to get a JWT token

2. **Use jq for Pretty Output**:
   ```bash
   curl ... | jq .
   ```

3. **Save Session ID**: Store the session_id from the first response for subsequent calls

4. **Monitor Emotional Trend**: Watch how the emotional_trend changes across turns

5. **Check Cold Start Status**: New users will have `cold_start_active: true` until ~10 feedback events
