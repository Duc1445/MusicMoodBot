"""
Chat service for MusicMoodBot
Handles chat operations, mood selection, intensity selection, and recommendations
Integrated with v1 & v5 Production API
"""

import requests
from typing import Dict, List, Optional, Tuple

from src.config.constants import (
    MOOD_EMOJI, INTENSITY_EMOJI, CHAT_STATE_AWAIT_MOOD, 
    CHAT_STATE_AWAIT_INTENSITY, CHAT_STATE_CHATTING
)
from src.utils.state_manager import app_state


# API Configuration - Using production API
API_BASE_URL = "http://localhost:8000"
API_V1_URL = f"{API_BASE_URL}/api/v1"
API_V5_URL = f"{API_BASE_URL}/api/v1/v5"  # v5.0 Adaptive API
API_TIMEOUT = 15  # seconds


class ChatService:
    """Handles chat and mood-based operations with v1/v5 API integration"""
    
    def __init__(self):
        self.api_available = False
        self.session_id = None
        self._check_api_availability()
    
    def _check_api_availability(self):
        """Check if backend API is available"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            self.api_available = response.status_code == 200
        except:
            self.api_available = False
    
    @staticmethod
    def add_message(sender: str, kind: str, text: str = None, song: dict = None):
        """Add message to chat history"""
        msg = {
            "sender": sender,
            "kind": kind,
            "text": text,
            "song": song
        }
        app_state.chat_messages.append(msg)
    
    @staticmethod
    def select_mood(mood: str) -> str:
        """
        Handle mood selection
        Returns: Bot response message
        """
        if not mood or mood not in MOOD_EMOJI:
            return "Vui lòng chọn mood hợp lệ."
        
        emoji = MOOD_EMOJI.get(mood, "🎵")
        ChatService.add_message("user", "text", f"{emoji} Mood: {mood}")
        
        # Update state
        app_state.chat_flow["mood"] = mood
        app_state.chat_flow["state"] = CHAT_STATE_AWAIT_INTENSITY
        
        return "Ok. Bạn muốn intensity mức nào? (Nhẹ / Vừa / Mạnh)"
    
    @staticmethod
    def select_intensity(intensity: str) -> dict:
        """
        Handle intensity selection - Uses v1 API for recommendations
        Returns: recommendation data with message
        """
        if not intensity or intensity not in INTENSITY_EMOJI:
            return {"success": False, "message": "Vui lòng chọn intensity hợp lệ."}
        
        emoji = INTENSITY_EMOJI.get(intensity, "✨")
        ChatService.add_message("user", "text", f"{emoji} Intensity: {intensity}")
        
        # Update state
        app_state.chat_flow["intensity"] = intensity
        app_state.chat_flow["state"] = CHAT_STATE_CHATTING
        
        # Call v1 API for mood-based recommendations
        mood = app_state.chat_flow["mood"]
        result = ChatService.get_mood_recommendations(mood, intensity)
        
        if result["success"]:
            return result
        
        # Fallback to a simple response
        return {
            "success": True,
            "songs": [],
            "bot_message": "Xin lỗi, không tìm thấy bài hát phù hợp. Vui lòng thử lại."
        }
    
    @staticmethod
    def get_mood_recommendations(mood: str, intensity: str = "Vừa", limit: int = 5) -> dict:
        """
        Get song recommendations by mood using v1 API.
        
        Args:
            mood: Vietnamese mood name (Vui, Buồn, etc.)
            intensity: "Nhẹ", "Vừa", or "Mạnh"
            limit: Number of songs to return
            
        Returns:
            Dict with success, songs, bot_message, playlist_id
        """
        try:
            user_id = app_state.user_info.get("user_id") or 1
            response = requests.post(
                f"{API_V1_URL}/chat/mood",
                json={
                    "mood": mood,
                    "intensity": intensity,
                    "limit": limit,
                    "user_id": user_id
                },
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                songs = [ChatService._normalize_song(s) for s in data.get("songs", [])]
                return {
                    "success": True,
                    "songs": songs,
                    "bot_message": data.get("bot_message", ""),
                    "playlist_id": data.get("playlist_id"),
                    "detected_mood": data.get("detected_mood", {}),
                    "session_id": data.get("session_id")
                }
        except Exception as e:
            print(f"Mood recommendation error: {e}")
        
        return {"success": False, "message": "Không thể kết nối đến server."}
    
    @staticmethod
    def smart_recommend(text: str, limit: int = 5) -> dict:
        """
        Smart recommendation using v5.0 adaptive API first, fallback to v1.
        
        Args:
            text: User's text describing their mood
            limit: Number of songs to return
            
        Returns:
            Dict with success, songs, detected_mood, bot_message
        """
        # Try v5.0 adaptive API first for better personalization
        try:
            user_id = app_state.user_info.get("user_id") or 1
            
            # Use v5.0 conversation continue for context-aware responses
            response = requests.post(
                f"{API_V5_URL}/conversation/continue",
                json={
                    "message": text,
                    "input_type": "text",
                    "include_recommendations": True,
                    "max_recommendations": limit,
                    "emotional_support_mode": True
                },
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                
                detected = {
                    "mood": data.get("detected_mood"),
                    "mood_vi": data.get("detected_mood"),
                    "confidence": data.get("mood_confidence", 0),
                    "intensity": "Vừa"
                }
                
                if detected.get("mood"):
                    app_state.chat_flow["mood"] = detected.get("mood_vi", "Chill")
                    app_state.chat_flow["state"] = CHAT_STATE_CHATTING
                
                # v5.0 returned recommendations - use them
                if data.get("should_recommend") and data.get("recommendations"):
                    songs = [ChatService._normalize_song(s) for s in data.get("recommendations", [])]
                    
                    return {
                        "success": True,
                        "songs": songs,
                        "detected_mood": detected,
                        "bot_message": data.get("bot_response", ""),
                        "session_id": data.get("session_id"),
                        "emotional_trend": data.get("emotional_trend"),
                        "require_mood_selection": False
                    }
                else:
                    # v5.0 needs more context - return clarifying question WITHOUT songs
                    return {
                        "success": True,
                        "songs": [],  # No songs yet - need more conversation
                        "detected_mood": detected,
                        "bot_message": data.get("bot_response", "Bạn có thể chia sẻ thêm về tâm trạng không?"),
                        "session_id": data.get("session_id"),
                        "emotional_trend": data.get("emotional_trend"),
                        "require_mood_selection": True,  # Signal that we need more input
                        "clarity_score": data.get("clarity_score", 0),
                        "turn_number": data.get("turn_number", 1)
                    }
        except Exception as e:
            print(f"v5.0 API error, falling back to v1: {e}")
        
        # Fallback to v1 API
        try:
            user_id = app_state.user_info.get("user_id") or 1
            response = requests.post(
                f"{API_V1_URL}/chat/message",
                json={
                    "message": text,
                    "limit": limit,
                    "user_id": user_id
                },
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                songs = [ChatService._normalize_song(s) for s in data.get("songs", [])]
                detected = data.get("detected_mood", {})
                
                # Update chat flow with detected mood
                if detected:
                    app_state.chat_flow["mood"] = detected.get("mood_vi", "Chill")
                    app_state.chat_flow["intensity"] = detected.get("intensity", "Vừa")
                    app_state.chat_flow["state"] = CHAT_STATE_CHATTING
                
                return {
                    "success": True,
                    "songs": songs,
                    "detected_mood": detected,
                    "bot_message": data.get("bot_message", ""),
                    "playlist_id": data.get("playlist_id"),
                    "session_id": data.get("session_id"),
                    "require_mood_selection": data.get("require_mood_selection", False)
                }
        except Exception as e:
            print(f"v1 API error: {e}")
        
        return {"success": False, "message": "Không thể kết nối đến server."}
    
    @staticmethod
    def submit_feedback(song_id: int, feedback_type: str) -> bool:
        """
        Submit feedback (like/dislike/skip) for a song.
        
        Args:
            song_id: ID of the song
            feedback_type: "like", "dislike", or "skip"
            
        Returns:
            True if successful
        """
        try:
            user_id = app_state.user_info.get("user_id") or 1
            response = requests.post(
                f"{API_V1_URL}/chat/feedback",
                json={
                    "song_id": song_id,
                    "feedback_type": feedback_type,
                    "user_id": user_id
                },
                timeout=API_TIMEOUT
            )
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def get_available_moods() -> List[dict]:
        """
        Get list of available moods from API.
        
        Returns:
            List of mood dicts with name, emoji, description
        """
        try:
            response = requests.get(
                f"{API_V1_URL}/chat/moods",
                timeout=API_TIMEOUT
            )
            if response.status_code == 200:
                return response.json().get("moods", [])
        except:
            pass
        
        # Fallback to local constants
        return [
            {"name": mood, "emoji": MOOD_EMOJI.get(mood, "🎵")}
            for mood in MOOD_EMOJI.keys()
        ]
    
    @staticmethod
    def _normalize_song(song: dict) -> dict:
        """Normalize song data from API to match expected format"""
        return {
            "song_id": song.get("song_id"),
            "name": song.get("name") or song.get("song_name", "Unknown"),
            "artist": song.get("artist", "Unknown"),
            "genre": song.get("genre", "Pop"),
            "mood": song.get("mood", ""),
            "reason": song.get("reason", ""),
            "match_score": song.get("match_score", 0),
            "audio_features": song.get("audio_features", {})
        }
    
    @staticmethod
    def generate_reason(mood: str, intensity: str, song: dict) -> str:
        """Generate recommendation reason"""
        # Use API-generated reason if available
        if song.get("reason"):
            return song["reason"]
        
        intensity_text = {
            "Nhẹ": "nhẹ nhàng",
            "Vừa": "vừa phải",
            "Mạnh": "mạnh mẽ"
        }.get(intensity, "phù hợp")
        
        return (
            f"Dựa trên mood '{mood}' và intensity '{intensity_text}', "
            f"bài hát '{song.get('name', 'N/A')}' của {song.get('artist', 'N/A')} "
            f"là lựa chọn hoàn hảo cho bạn."
        )
    
    @staticmethod
    def reset():
        """Reset chat"""
        app_state.reset_chat()


# Singleton instance
chat_service = ChatService()

