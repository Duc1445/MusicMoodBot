"""
History service for MusicMoodBot
Handles loading and displaying user chat history
Integrated with v1 Production API
"""

import requests
from typing import List, Dict
from src.utils.state_manager import app_state


# API Configuration
API_BASE_URL = "http://localhost:8000"
API_V1_URL = f"{API_BASE_URL}/api/v1"
API_TIMEOUT = 10  # seconds


class HistoryService:
    """Handles chat history operations via v1 API"""
    
    @staticmethod
    def load_user_history(limit: int = 50) -> List[Dict]:
        """Load recommendations history for current user via API"""
        if not app_state.user_info.get("user_id"):
            return []
        
        try:
            user_id = app_state.user_info["user_id"]
            response = requests.get(
                f"{API_V1_URL}/user/history",
                params={"user_id": user_id, "limit": limit},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                history = data.get("history", [])
                
                # Normalize field names for UI compatibility
                for item in history:
                    if "song_name" not in item and "name" in item:
                        item["song_name"] = item["name"]
                    if "song_artist" not in item and "artist" in item:
                        item["song_artist"] = item["artist"]
                
                return history
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
        timestamp = item.get("listened_at") or item.get("timestamp", "")
        
        # Parse timestamp
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M")
            except:
                time_str = timestamp[:5] if timestamp else ""
        else:
            time_str = ""
        
        song_name = item.get("song_name") or item.get("name", "Unknown")
        artist = item.get("artist", "")
        
        return f"[{time_str}] {song_name} - {artist} | {mood}"
    
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
            mood = item.get("mood") or item.get("mood_at_time")
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
