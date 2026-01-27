"""
State management for MusicMoodBot
Handles global application state
"""

from src.config.constants import CHAT_STATE_AWAIT_MOOD

# ================== GLOBAL STATE ==================
class AppState:
    """Centralized application state"""
    
    def __init__(self):
        # Chat messages: [{"sender":"user"/"bot","kind":"text"/"card","text":str,"song":dict}]
        self.chat_messages = []
        
        # User information
        self.user_info = {
            "name": "",
            "email": "",
            "user_id": None,
            "password": ""
        }
        
        # Chat flow control
        self.chat_flow = {
            "state": CHAT_STATE_AWAIT_MOOD,  # await_mood | await_intensity | chatting
            "mood": None,
            "intensity": None,
            "busy": False,
        }
        
        # Typing indicator
        self.typing_on = {"value": False}
        
        # Chat bootstrap callback
        self._chat_bootstrap = None
    
    def reset_chat(self):
        """Reset chat state"""
        self.chat_messages.clear()
        self.chat_flow["state"] = CHAT_STATE_AWAIT_MOOD
        self.chat_flow["mood"] = None
        self.chat_flow["intensity"] = None
        self.typing_on["value"] = False
        self.chat_flow["busy"] = False
    
    def reset_user(self):
        """Clear user information"""
        self.user_info = {
            "name": "",
            "email": "",
            "user_id": None,
            "password": ""
        }
    
    def set_chat_bootstrap(self, fn):
        """Set bootstrap callback"""
        self._chat_bootstrap = fn
    
    def get_chat_bootstrap(self):
        """Get bootstrap callback"""
        return self._chat_bootstrap


# Global state instance
app_state = AppState()
