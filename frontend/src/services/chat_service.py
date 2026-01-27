"""
Chat service for MusicMoodBot
Handles chat operations, mood selection, intensity selection, and recommendations
"""

import random

from backend.database import (
    add_chat_history, add_recommendation, get_all_songs
)
from src.config.constants import (
    MOOD_EMOJI, INTENSITY_EMOJI, CHAT_STATE_AWAIT_MOOD, 
    CHAT_STATE_AWAIT_INTENSITY, CHAT_STATE_CHATTING
)
from src.utils.state_manager import app_state


class ChatService:
    """Handles chat and mood-based operations"""
    
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
        """Pick a song based on mood"""
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
            "reason": "Database error"
        }
    
    @staticmethod
    def generate_reason(mood: str, intensity: str, song: dict) -> str:
        """Generate recommendation reason"""
        intensity_text = {
            "Nhẹ": "nhẹ nhàng",
            "Vừa": "vừa phải",
            "Mạnh": "mạnh mẽ"
        }.get(intensity, "phù hợp")
        
        return (
            f"Dựa trên mood '{mood}' và intensity '{intensity_text}', "
            f"bài hát '{song.get('name', 'N/A')}' của {song.get('artist', 'N/A')} "
            f"là lựa chọn hoàn hảo. {song.get('reason', '')}"
        )
    
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
