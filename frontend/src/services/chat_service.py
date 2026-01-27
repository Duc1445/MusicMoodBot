"""
Chat service for MusicMoodBot
Handles chat operations, mood selection, intensity selection, and recommendations
Now with API integration for smart recommendations
"""

import random
import requests
from typing import Dict, List, Optional, Tuple

from backend.database import (
    add_chat_history, add_recommendation, get_all_songs
)
from src.config.constants import (
    MOOD_EMOJI, INTENSITY_EMOJI, CHAT_STATE_AWAIT_MOOD, 
    CHAT_STATE_AWAIT_INTENSITY, CHAT_STATE_CHATTING
)
from src.utils.state_manager import app_state


# API Configuration
API_BASE_URL = "http://localhost:8000/api/moods"
API_TIMEOUT = 10  # seconds


class ChatService:
    """Handles chat and mood-based operations with API integration"""
    
    def __init__(self):
        self.api_available = False
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
        
        # Save to database
        if app_state.user_info["user_id"]:
            add_chat_history(
                app_state.user_info["user_id"],
                mood=mood,
                intensity=None
            )
        
        # Update state
        app_state.chat_flow["mood"] = mood
        app_state.chat_flow["state"] = CHAT_STATE_AWAIT_INTENSITY
        
        return "Ok. Bạn muốn intensity mức nào? (Nhẹ / Vừa / Mạnh)"
    
    @staticmethod
    def select_intensity(intensity: str) -> dict:
        """
        Handle intensity selection
        Returns: recommendation data with message
        """
        if not intensity or intensity not in INTENSITY_EMOJI:
            return {"success": False, "message": "Vui lòng chọn intensity hợp lệ."}
        
        emoji = INTENSITY_EMOJI.get(intensity, "✨")
        ChatService.add_message("user", "text", f"{emoji} Intensity: {intensity}")
        
        # Save to database
        if app_state.user_info["user_id"]:
            add_chat_history(
                app_state.user_info["user_id"],
                mood=app_state.chat_flow["mood"],
                intensity=intensity
            )
        
        # Update state
        app_state.chat_flow["intensity"] = intensity
        app_state.chat_flow["state"] = CHAT_STATE_CHATTING
        
        # Generate recommendation
        song = ChatService.pick_song(app_state.chat_flow["mood"])
        reason = ChatService.generate_reason(
            app_state.chat_flow["mood"],
            intensity,
            song
        )
        
        return {
            "success": True,
            "song": song,
            "reason": reason
        }
    
    @staticmethod
    def pick_song(mood: str) -> dict:
        """Pick a song based on mood - with API fallback"""
        # Try API first
        try:
            response = requests.get(
                f"{API_BASE_URL}/songs/by-mood/{ChatService._mood_to_en(mood)}",
                timeout=API_TIMEOUT
            )
            if response.status_code == 200:
                songs = response.json()
                if songs:
                    song = random.choice(songs)
                    return ChatService._normalize_song(song)
        except:
            pass
        
        # Fallback to local database
        try:
            songs = get_all_songs()
            if songs:
                # Filter by mood if available
                mood_songs = [s for s in songs if mood in s.get("moods", [])]
                if mood_songs:
                    return random.choice(mood_songs)
                return random.choice(songs)
        except:
            pass
        
        return {
            "name": "No songs found",
            "artist": "System",
            "genre": "N/A",
            "suy_score": 0,
            "reason": "Không tìm thấy bài hát phù hợp."
        }
    
    @staticmethod
    def _mood_to_en(mood_vi: str) -> str:
        """Convert Vietnamese mood to English for API"""
        mapping = {
            "Vui": "happy",
            "Buồn": "sad",
            "Suy tư": "stress",
            "Chill": "happy",
            "Năng lượng": "energetic"
        }
        return mapping.get(mood_vi, "happy")
    
    @staticmethod
    def _normalize_song(song: dict) -> dict:
        """Normalize song data from API to match expected format"""
        return {
            "song_id": song.get("song_id"),
            "name": song.get("song_name", song.get("name", "Unknown")),
            "artist": song.get("artist", song.get("artist_name", "Unknown")),
            "genre": song.get("genre", "Pop"),
            "suy_score": round(float(song.get("mood_score", 5) or 5), 1),
            "reason": song.get("recommendation_reason", ""),
            "moods": [song.get("mood", "")]
        }
    
    @staticmethod
    def smart_recommend(text: str) -> Tuple[dict, dict]:
        """
        Smart recommendation using text mood detection.
        
        Args:
            text: User's text describing their mood
            
        Returns:
            Tuple of (mood_info, song)
        """
        try:
            response = requests.post(
                f"{API_BASE_URL}/smart-recommend",
                params={"text": text, "top_k": 5},
                timeout=API_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                mood_info = data.get("detected_mood", {})
                recommendations = data.get("recommendations", [])
                
                if recommendations:
                    song = ChatService._normalize_song(random.choice(recommendations))
                    song["reason"] = recommendations[0].get("recommendation_reason", "")
                    return mood_info, song
        except Exception as e:
            print(f"Smart recommend error: {e}")
        
        # Fallback
        return {
            "mood": "Chill",
            "confidence": 0.5,
            "intensity": "Vừa"
        }, ChatService.pick_song("Chill")
    
    @staticmethod
    def detect_mood_from_text(text: str) -> dict:
        """
        Detect mood from user text using API.
        
        Args:
            text: User's text
            
        Returns:
            Dict with mood, confidence, intensity
        """
        try:
            response = requests.post(
                f"{API_BASE_URL}/detect-mood-from-text",
                params={"text": text},
                timeout=API_TIMEOUT
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return {
            "detected_mood": "Chill",
            "confidence": 0.5,
            "intensity": "Vừa",
            "keywords_matched": []
        }
    
    @staticmethod
    def generate_reason(mood: str, intensity: str, song: dict) -> str:
        """Generate recommendation reason"""
        intensity_text = {
            "Nhẹ": "nhẹ nhàng",
            "Vừa": "vừa phải",
            "Mạnh": "mạnh mẽ"
        }.get(intensity, "phù hợp")
        
        # Use API-generated reason if available
        if song.get("reason"):
            return song["reason"]
        
        return (
            f"Dựa trên mood '{mood}' và intensity '{intensity_text}', "
            f"bài hát '{song.get('name', 'N/A')}' của {song.get('artist', 'N/A')} "
            f"là lựa chọn hoàn hảo cho bạn."
        )
    
    @staticmethod
    def search_songs(query: str, top_k: int = 10) -> List[dict]:
        """
        Search songs using TF-IDF search (supports Vietnamese).
        
        Args:
            query: Search query (Vietnamese or English)
            top_k: Number of results
            
        Returns:
            List of matching songs
        """
        try:
            response = requests.get(
                f"{API_BASE_URL}/search",
                params={"query": query, "top_k": top_k},
                timeout=API_TIMEOUT
            )
            if response.status_code == 200:
                songs = response.json()
                return [ChatService._normalize_song(s) for s in songs]
        except:
            pass
        
        return []
    
    @staticmethod
    def get_user_recommendations(user_id: str, mood: str = None, top_k: int = 5) -> List[dict]:
        """
        Get personalized recommendations for user.
        
        Args:
            user_id: User identifier
            mood: Optional mood filter
            top_k: Number of recommendations
            
        Returns:
            List of recommended songs
        """
        try:
            params = {"top_k": top_k, "diversity": True}
            if mood:
                params["mood"] = ChatService._mood_to_en(mood)
            
            response = requests.get(
                f"{API_BASE_URL}/user/{user_id}/personalized-recommend",
                params=params,
                timeout=API_TIMEOUT
            )
            if response.status_code == 200:
                songs = response.json()
                return [ChatService._normalize_song(s) for s in songs]
        except:
            pass
        
        return []
    
    @staticmethod
    def save_recommendation(song_id: int = None):
        """Save recommendation to database"""
        if not app_state.user_info["user_id"]:
            return False
        
        try:
            add_recommendation(
                app_state.user_info["user_id"],
                song_id=song_id,
                mood=app_state.chat_flow["mood"],
                intensity=app_state.chat_flow["intensity"]
            )
            return True
        except:
            return False
    
    @staticmethod
    def reset():
        """Reset chat"""
        app_state.reset_chat()


# Singleton instance
chat_service = ChatService()
