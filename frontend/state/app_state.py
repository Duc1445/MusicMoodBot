"""
Application State
=================
Centralized application state with persistence.

This is a SINGLETON - only ONE instance exists globally.
All screens/services share the same state.

Usage:
    from frontend.state import app_state
    
    # In screens
    app_state.add_message("user", "text", text="Hello")
    app_state.set_user(1, "John", "john@example.com")
    
    # Check state
    if app_state.is_logged_in():
        print(app_state.user_info["name"])
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger("mmb.state")

# Chat states
CHAT_STATE_AWAIT_MOOD = "await_mood"
CHAT_STATE_AWAIT_INTENSITY = "await_intensity"
CHAT_STATE_CHATTING = "chatting"


class AppState:
    """
    Centralized application state with persistence.
    """
    _instance: Optional['AppState'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        logger.debug("AppState initializing...")
        
        # Dark mode state
        self.dark_mode: bool = False
        
        # Chat messages
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
            "state": CHAT_STATE_AWAIT_MOOD,
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
        
        # Learned preferences
        self.learned_preferences: Dict[str, Any] = {
            "favorite_moods": [],
            "favorite_genres": [],
            "disliked_songs": [],
            "liked_songs": [],
            "mood_history": []
        }
        
        # State file path
        self._state_file = os.path.join(
            os.path.dirname(__file__),
            "..", "user_state.json"
        )
        
        self._initialized = True
        logger.debug("AppState initialized successfully")
    
    # ==================== CHAT METHODS ====================
    
    def reset_chat(self):
        """Reset chat state to initial values"""
        logger.debug("Resetting chat state")
        self.chat_messages.clear()
        self.chat_flow["state"] = CHAT_STATE_AWAIT_MOOD
        self.chat_flow["mood"] = None
        self.chat_flow["intensity"] = None
        self.chat_flow["last_recommendation"] = None
        self.typing_on["value"] = False
        self.chat_flow["busy"] = False
    
    def add_message(self, sender: str, kind: str, text: str = None, song: dict = None):
        """Add a message to chat history"""
        msg = {"sender": sender, "kind": kind, "text": text, "song": song}
        self.chat_messages.append(msg)
        logger.debug(f"Message added: {sender}/{kind} - {len(self.chat_messages)} total")
    
    def set_typing(self, is_typing: bool):
        """Set typing indicator state"""
        self.typing_on["value"] = is_typing
        logger.debug(f"Typing indicator: {is_typing}")
    
    def set_busy(self, is_busy: bool):
        """Set busy state"""
        self.chat_flow["busy"] = is_busy
        logger.debug(f"Busy state: {is_busy}")
    
    # ==================== USER METHODS ====================
    
    def reset_user(self):
        """Clear user information"""
        logger.debug("Resetting user state")
        self.user_info = {
            "name": "", "email": "", "user_id": None,
            "password": "", "preferences": {}, "last_login": None
        }
        self.learned_preferences = {
            "favorite_moods": [], "favorite_genres": [],
            "disliked_songs": [], "liked_songs": [], "mood_history": []
        }
    
    def set_user(self, user_id: int, name: str, email: str):
        """Set user information after login"""
        self.user_info["user_id"] = user_id
        self.user_info["name"] = name
        self.user_info["email"] = email
        self.user_info["last_login"] = datetime.now().isoformat()
        logger.info(f"User logged in: {name} (ID: {user_id})")
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self.user_info.get("user_id") is not None
    
    # ==================== BOOTSTRAP ====================
    
    def set_chat_bootstrap(self, fn):
        """Set bootstrap callback for chat screen"""
        self._chat_bootstrap = fn
    
    def get_chat_bootstrap(self):
        """Get bootstrap callback"""
        return self._chat_bootstrap
    
    # ==================== PREFERENCE LEARNING ====================
    
    def record_mood_selection(self, mood: str):
        """Record mood selection for learning"""
        self.learned_preferences["mood_history"].append({
            "mood": mood, "timestamp": datetime.now().isoformat()
        })
        # Keep only last 100
        self.learned_preferences["mood_history"] = \
            self.learned_preferences["mood_history"][-100:]
        
        # Update favorites
        mood_counts = {}
        for entry in self.learned_preferences["mood_history"]:
            m = entry["mood"]
            mood_counts[m] = mood_counts.get(m, 0) + 1
        
        self.learned_preferences["favorite_moods"] = sorted(
            mood_counts.keys(), key=lambda m: mood_counts[m], reverse=True
        )[:3]
        logger.debug(f"Recorded mood: {mood}")
    
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
    
    # ==================== PERSISTENCE ====================
    
    def save_state(self) -> bool:
        """Save state to file"""
        try:
            state_data = {
                "user_info": {k: v for k, v in self.user_info.items() if k != "password"},
                "learned_preferences": self.learned_preferences,
                "session": self.session
            }
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            logger.debug("State saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    def load_state(self) -> bool:
        """Load state from file"""
        try:
            if os.path.exists(self._state_file):
                with open(self._state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                if "user_info" in state_data:
                    for k, v in state_data["user_info"].items():
                        if k in self.user_info and k != "password":
                            self.user_info[k] = v
                
                if "learned_preferences" in state_data:
                    self.learned_preferences.update(state_data["learned_preferences"])
                
                logger.debug("State loaded")
                return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
        return False
    
    def __repr__(self):
        return f"<AppState user={self.user_info.get('name', 'Guest')} msgs={len(self.chat_messages)}>"


# Singleton instance
app_state = AppState()
app_state.load_state()
logger.info("AppState singleton ready")
