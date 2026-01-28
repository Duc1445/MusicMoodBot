"""
State management for MusicMoodBot
Handles global application state with persistence support
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.config.constants import CHAT_STATE_AWAIT_MOOD

# State file path for persistence
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "user_state.json")


class AppState:
    """Centralized application state with persistence"""
    
    def __init__(self):
        # Chat messages: [{"sender":"user"/"bot","kind":"text"/"card","text":str,"song":dict}]
        self.chat_messages: List[Dict] = []
        
        # User information
        self.user_info: Dict[str, Any] = {
            "name": "",
            "email": "",
            "user_id": None,
            "password": "",
            "preferences": {},
            "last_login": None
        }
        
        # Chat flow control
        self.chat_flow: Dict[str, Any] = {
            "state": CHAT_STATE_AWAIT_MOOD,  # await_mood | await_intensity | chatting
            "mood": None,
            "intensity": None,
            "busy": False,
            "last_recommendation": None
        }
        
        # Typing indicator
        self.typing_on: Dict[str, bool] = {"value": False}
        
        # Chat bootstrap callback
        self._chat_bootstrap = None
        
        # Session tracking
        self.session: Dict[str, Any] = {
            "start_time": datetime.now().isoformat(),
            "recommendations_count": 0,
            "searches_count": 0
        }
        
        # User preferences (learned from interactions)
        self.learned_preferences: Dict[str, Any] = {
            "favorite_moods": [],
            "favorite_genres": [],
            "disliked_songs": [],
            "liked_songs": [],
            "mood_history": []
        }
    
    def reset_chat(self):
        """Reset chat state"""
        self.chat_messages.clear()
        self.chat_flow["state"] = CHAT_STATE_AWAIT_MOOD
        self.chat_flow["mood"] = None
        self.chat_flow["intensity"] = None
        self.chat_flow["last_recommendation"] = None
        self.chat_flow["conversation_history"] = []
        self.chat_flow["conversation_turn"] = 0
        self.typing_on["value"] = False
        self.chat_flow["busy"] = False
    
    def reset_user(self):
        """Clear user information"""
        self.user_info = {
            "name": "",
            "email": "",
            "user_id": None,
            "password": "",
            "preferences": {},
            "last_login": None
        }
        self.learned_preferences = {
            "favorite_moods": [],
            "favorite_genres": [],
            "disliked_songs": [],
            "liked_songs": [],
            "mood_history": []
        }
    
    def set_chat_bootstrap(self, fn):
        """Set bootstrap callback"""
        self._chat_bootstrap = fn
    
    def get_chat_bootstrap(self):
        """Get bootstrap callback"""
        return self._chat_bootstrap
    
    # ==================== NEW FEATURES ====================
    
    def record_mood_selection(self, mood: str):
        """Record mood selection for learning"""
        self.learned_preferences["mood_history"].append({
            "mood": mood,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only last 100 entries
        self.learned_preferences["mood_history"] = \
            self.learned_preferences["mood_history"][-100:]
        
        # Update favorite moods
        mood_counts = {}
        for entry in self.learned_preferences["mood_history"]:
            m = entry["mood"]
            mood_counts[m] = mood_counts.get(m, 0) + 1
        
        self.learned_preferences["favorite_moods"] = sorted(
            mood_counts.keys(),
            key=lambda m: mood_counts[m],
            reverse=True
        )[:3]
    
    def record_song_feedback(self, song_id: int, liked: bool):
        """Record user feedback on song"""
        if liked:
            if song_id not in self.learned_preferences["liked_songs"]:
                self.learned_preferences["liked_songs"].append(song_id)
            if song_id in self.learned_preferences["disliked_songs"]:
                self.learned_preferences["disliked_songs"].remove(song_id)
        else:
            if song_id not in self.learned_preferences["disliked_songs"]:
                self.learned_preferences["disliked_songs"].append(song_id)
            if song_id in self.learned_preferences["liked_songs"]:
                self.learned_preferences["liked_songs"].remove(song_id)
    
    def get_suggested_mood(self) -> Optional[str]:
        """Get suggested mood based on history"""
        if self.learned_preferences["favorite_moods"]:
            return self.learned_preferences["favorite_moods"][0]
        return None
    
    def increment_recommendation_count(self):
        """Increment recommendation counter"""
        self.session["recommendations_count"] += 1
    
    def increment_search_count(self):
        """Increment search counter"""
        self.session["searches_count"] += 1
    
    def save_state(self) -> bool:
        """Save state to file for persistence"""
        try:
            state_data = {
                "user_info": {
                    k: v for k, v in self.user_info.items() 
                    if k != "password"  # Don't save password
                },
                "learned_preferences": self.learned_preferences,
                "session": self.session
            }
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save state: {e}")
            return False
    
    def load_state(self) -> bool:
        """Load state from file"""
        try:
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                # Restore user info (except password)
                if "user_info" in state_data:
                    for k, v in state_data["user_info"].items():
                        if k in self.user_info and k != "password":
                            self.user_info[k] = v
                
                # Restore learned preferences
                if "learned_preferences" in state_data:
                    self.learned_preferences.update(state_data["learned_preferences"])
                
                return True
        except Exception as e:
            print(f"Failed to load state: {e}")
        return False
    
    def get_session_summary(self) -> Dict:
        """Get session summary for analytics"""
        return {
            "session_start": self.session["start_time"],
            "recommendations_made": self.session["recommendations_count"],
            "searches_made": self.session["searches_count"],
            "favorite_moods": self.learned_preferences["favorite_moods"],
            "liked_songs_count": len(self.learned_preferences["liked_songs"]),
            "user_name": self.user_info.get("name", "Guest")
        }


# Global state instance
app_state = AppState()

# Try to load previous state
app_state.load_state()
