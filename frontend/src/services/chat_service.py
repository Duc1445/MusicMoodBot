"""
Chat Service - Refactored
==========================
Clean chat service with proper imports and logging.
"""

import random
from typing import Dict, List, Optional, Tuple

# Centralized config
from ..config.settings import settings, logger, MOOD_VI_TO_EN

# API client
from .api_client import api, APIStatus

# State
from ..utils.state_manager import app_state

# Database (optional fallback)
try:
    from backend.src.database.database import (
        add_chat_history, add_recommendation, get_all_songs
    )
    HAS_LOCAL_DB = True
except ImportError:
    HAS_LOCAL_DB = False
    logger.debug("Local database not available, using API only")


class ChatService:
    """
    Chat and recommendation service.
    Handles communication with backend API.
    """
    
    def __init__(self):
        self.api_available = False
        self._check_api_availability()
    
    def _check_api_availability(self):
        """Check if backend API is available"""
        try:
            response = api.moods.health_check()
            self.api_available = response.is_success
            logger.info(f"API available: {self.api_available}")
        except Exception as e:
            logger.warning(f"API check failed: {e}")
            self.api_available = False
    
    # ==================== MESSAGE METHODS ====================
    
    @staticmethod
    def add_message(sender: str, kind: str, text: str = None, song: dict = None):
        """Add message to chat history via state"""
        app_state.add_message(sender, kind, text, song)
    
    # ==================== SONG METHODS ====================
    
    @staticmethod
    def pick_song(mood: str) -> dict:
        """
        Pick a song based on mood.
        
        Args:
            mood: Vietnamese mood name (e.g., "Vui", "Buồn")
            
        Returns:
            Normalized song dictionary
        """
        mood_en = MOOD_VI_TO_EN.get(mood, "happy")
        logger.debug(f"Picking song for mood: {mood} ({mood_en})")
        
        # Try API first
        try:
            response = api.moods.get_songs_by_mood(mood_en)
            if response.is_success and response.data:
                songs = response.data
                if songs:
                    song = random.choice(songs)
                    logger.debug(f"API returned song: {song.get('song_name', 'N/A')}")
                    return ChatService._normalize_song(song)
        except Exception as e:
            logger.error(f"API error: {e}")
        
        # Fallback to local database
        if HAS_LOCAL_DB:
            try:
                songs = get_all_songs()
                if songs:
                    mood_songs = [s for s in songs if mood in str(s.get("moods", ""))]
                    if mood_songs:
                        return ChatService._normalize_song(random.choice(mood_songs))
                    return ChatService._normalize_song(random.choice(songs))
            except Exception as e:
                logger.error(f"Local DB error: {e}")
        
        # Last resort fallback
        return {
            "name": "Không tìm thấy",
            "artist": "System",
            "genre": "N/A",
            "suy_score": 0,
            "reason": "Không tìm thấy bài hát phù hợp."
        }
    
    @staticmethod
    def _normalize_song(song: dict) -> dict:
        """Normalize song data from API to standard format"""
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
        user_id = app_state.user_info.get("user_id")
        logger.info(f"Smart recommend for: {text[:30]}...")
        
        try:
            response = api.moods.smart_recommend(
                text, 
                user_id=str(user_id) if user_id else None, 
                limit=5
            )
            
            if response.is_success and response.data:
                data = response.data
                mood_info = data.get("detected_mood", {})
                recommendations = data.get("recommendations", [])
                
                logger.debug(f"Detected mood: {mood_info.get('mood', 'N/A')}")
                
                if recommendations:
                    song = ChatService._normalize_song(random.choice(recommendations))
                    song["reason"] = recommendations[0].get("recommendation_reason", "")
                    return mood_info, song
        except Exception as e:
            logger.error(f"Smart recommend error: {e}")
        
        # Fallback
        return {
            "mood": "Chill",
            "confidence": 0.5,
            "intensity": "Vừa"
        }, ChatService.pick_song("Chill")
    
    @staticmethod
    def search_songs(query: str, top_k: int = 10) -> List[dict]:
        """
        Search songs using TF-IDF search.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of matching songs
        """
        logger.debug(f"Searching songs: {query}")
        try:
            response = api.moods.search_songs(query, limit=top_k)
            if response.is_success and response.data:
                songs = response.data
                return [ChatService._normalize_song(s) for s in songs]
        except Exception as e:
            logger.error(f"Search error: {e}")
        return []
    
    # ==================== DATABASE METHODS ====================
    
    @staticmethod
    def save_recommendation(song_id: int = None) -> bool:
        """Save recommendation to database"""
        if not app_state.user_info.get("user_id"):
            return False
        
        if not HAS_LOCAL_DB:
            return False
        
        try:
            add_recommendation(
                app_state.user_info["user_id"],
                song_id=song_id,
                mood=app_state.chat_flow["mood"],
                intensity=app_state.chat_flow["intensity"]
            )
            logger.debug(f"Saved recommendation: song_id={song_id}")
            return True
        except Exception as e:
            logger.error(f"Save recommendation error: {e}")
            return False
    
    # ==================== UTILITY METHODS ====================
    
    @staticmethod
    def generate_reason(mood: str, intensity: str, song: dict) -> str:
        """Generate recommendation reason"""
        intensity_text = {
            "Nhẹ": "nhẹ nhàng",
            "Vừa": "vừa phải",
            "Mạnh": "mạnh mẽ"
        }.get(intensity, "phù hợp")
        
        if song.get("reason"):
            return song["reason"]
        
        return (
            f"Dựa trên mood '{mood}' và intensity '{intensity_text}', "
            f"bài hát '{song.get('name', 'N/A')}' của {song.get('artist', 'N/A')} "
            f"là lựa chọn hoàn hảo cho bạn."
        )
    
    @staticmethod
    def reset():
        """Reset chat state"""
        app_state.reset_chat()
        logger.info("Chat service reset")


# Singleton instance
chat_service = ChatService()
