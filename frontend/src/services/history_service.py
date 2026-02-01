"""
History service for MusicMoodBot
Handles loading and displaying user chat history
"""

from backend.src.database.database import get_user_recommendations
from ..utils.state_manager import app_state


class HistoryService:
    """Handles chat history operations"""
    
    @staticmethod
    def load_user_history() -> list:
        """Load recommendations history for current user"""
        if not app_state.user_info["user_id"]:
            return []
        
        try:
            # Use get_user_recommendations instead of get_user_chat_history
            history = get_user_recommendations(app_state.user_info["user_id"])
            
            # Map field names for UI compatibility
            for item in history:
                # song_name is now correctly returned from JOIN
                if "song_name" not in item and "name" in item:
                    item["song_name"] = item["name"]
                # artist field (not artist_name)
                if "song_artist" not in item and "artist" in item:
                    item["song_artist"] = item["artist"]
            
            return history if history else []
        except Exception as e:
            print(f"Error loading history: {e}")
            return []
    
    @staticmethod
    def format_history_item(item: dict) -> str:
        """Format history item for display"""
        if not item:
            return ""
        
        mood = item.get("mood", "N/A")
        intensity = item.get("intensity", "N/A")
        timestamp = item.get("timestamp", "")
        
        # Parse timestamp
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M")
            except:
                time_str = timestamp[:5] if timestamp else ""
        else:
            time_str = ""
        
        return f"[{time_str}] Mood: {mood} | Intensity: {intensity}"
    
    @staticmethod
    def get_history_summary() -> dict:
        """Get summary of user's history"""
        history = HistoryService.load_user_history()
        
        if not history:
            return {
                "total": 0,
                "moods": {},
                "most_common_mood": None
            }
        
        # Count moods
        mood_count = {}
        for item in history:
            mood = item.get("mood")
            if mood:
                mood_count[mood] = mood_count.get(mood, 0) + 1
        
        # Find most common
        most_common = max(mood_count, key=mood_count.get) if mood_count else None
        
        return {
            "total": len(history),
            "moods": mood_count,
            "most_common_mood": most_common
        }


# Singleton instance
history_service = HistoryService()
