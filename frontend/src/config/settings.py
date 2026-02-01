"""
MusicMoodBot Frontend Settings
=============================
Centralized configuration file - ALL settings in ONE place.
Easy to modify, easy to debug.

Usage:
    from ..config.settings import settings, logger
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional


# ==================== LOGGING SETUP ====================

def setup_logger(name: str = "mmb", level: str = "INFO") -> logging.Logger:
    """Create a configured logger"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    logger = logging.getLogger(name)
    
    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    logger.propagate = False  # Prevent duplicate logs from parent
    
    # Console handler with formatting
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Global logger
logger = setup_logger("mmb", "INFO")


# ==================== SETTINGS CLASS ====================

@dataclass
class Settings:
    """
    All application settings in one place.
    
    Modify values here to change app behavior.
    """
    
    # === API Configuration ===
    API_BASE_URL: str = "http://localhost:8000"
    API_TIMEOUT: float = 30.0
    API_MAX_RETRIES: int = 3
    API_DEBUG: bool = True
    
    # === Authentication ===
    AUTH_TOKEN_KEY: str = "mmb_auth_token"
    AUTH_TOKEN_EXPIRY_BUFFER: int = 60  # seconds before expiry to refresh
    
    # === Chat Configuration ===
    CHAT_BOT_TYPING_DELAY: float = 0.5  # seconds
    CHAT_MAX_MESSAGES: int = 100  # max messages to keep in memory
    CHAT_WELCOME_MESSAGE: str = "Chào bạn! Hôm nay bạn cảm thấy thế nào? Mình sẽ giúp bạn chọn nhạc phù hợp nhé!"
    
    # === Recommendation Settings ===
    DEFAULT_RECOMMENDATION_LIMIT: int = 3
    DEFAULT_SEARCH_LIMIT: int = 10
    MIN_CONFIDENCE_THRESHOLD: float = 0.5
    
    # === UI Theme Colors ===
    TEAL_PRIMARY: str = "#4DB6AC"
    TEAL_DARK: str = "#00897B"
    SIDEBAR_BG: str = "#FAFAFA"
    CHAT_BG: str = "#F5F5F5"
    WHITE: str = "#FFFFFF"
    TEXT_PRIMARY: str = "#1A1A1A"
    TEXT_SECONDARY: str = "#666666"
    TEXT_MUTED: str = "#888888"
    BORDER_COLOR: str = "#E0E0E0"
    
    # === Paths ===
    @property
    def BASE_DIR(self) -> str:
        """Frontend base directory"""
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    @property
    def STATE_FILE(self) -> str:
        """User state persistence file"""
        return os.path.join(self.BASE_DIR, "user_state.json")
    
    @property
    def AUTH_TOKEN_FILE(self) -> str:
        """Auth token file (fallback storage)"""
        return os.path.join(self.BASE_DIR, ".auth_token")
    
    @property
    def ENV_FILE(self) -> str:
        """Environment file path"""
        return os.path.join(self.BASE_DIR, ".env")
    
    def load_from_env(self):
        """Load settings from .env file if exists"""
        if os.path.exists(self.ENV_FILE):
            logger.info(f"Loading settings from {self.ENV_FILE}")
            with open(self.ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        # Map env vars to settings
                        if key == "API_BASE_URL":
                            self.API_BASE_URL = value
                        elif key == "API_TIMEOUT":
                            self.API_TIMEOUT = float(value)
                        elif key == "API_DEBUG":
                            self.API_DEBUG = value.lower() == "true"
        
        logger.info(f"API URL: {self.API_BASE_URL}")
        return self


# ==================== GLOBAL SETTINGS INSTANCE ====================

settings = Settings()
settings.load_from_env()


# ==================== MOOD & INTENSITY DATA ====================

# Available moods (Vietnamese)
MOODS = ["Vui", "Buồn", "Suy tư", "Chill", "Năng lượng"]

# Available intensities (Vietnamese)
INTENSITIES = ["Nhẹ", "Vừa", "Mạnh"]

# Mood emojis
MOOD_EMOJI = {
    "Vui": "😊",
    "Buồn": "😢",
    "Suy tư": "🧠",
    "Chill": "😎",
    "Năng lượng": "⚡",
    # English variants (for API responses)
    "happy": "😊",
    "sad": "😢",
    "stress": "🧠",
    "energetic": "⚡",
    "angry": "😠"
}

# Intensity emojis
INTENSITY_EMOJI = {
    "Nhẹ": "🌿",
    "Vừa": "✨",
    "Mạnh": "🔥",
    "low": "🌿",
    "medium": "✨",
    "high": "🔥"
}

# Vietnamese → English mood mapping (for API calls)
MOOD_VI_TO_EN = {
    "Vui": "happy",
    "Buồn": "sad",
    "Suy tư": "stress",
    "Chill": "happy",
    "Năng lượng": "energetic"
}

# English → Vietnamese mood mapping (for display)
MOOD_EN_TO_VI = {
    "happy": "Vui",
    "sad": "Buồn",
    "stress": "Suy tư",
    "energetic": "Năng lượng",
    "angry": "Năng lượng"
}

# Intensity mappings
INTENSITY_VI_TO_EN = {
    "Nhẹ": "low",
    "Vừa": "medium",
    "Mạnh": "high"
}

INTENSITY_EN_TO_VI = {
    "low": "Nhẹ",
    "medium": "Vừa",
    "high": "Mạnh"
}

# Mood colors (for UI)
MOOD_COLORS = {
    "Vui": "#FFD93D",
    "Buồn": "#6C9BCF",
    "Suy tư": "#9B59B6",
    "Chill": "#26D07C",
    "Năng lượng": "#FF6B6B"
}

# Chat states
CHAT_STATE_AWAIT_MOOD = "await_mood"
CHAT_STATE_AWAIT_INTENSITY = "await_intensity"
CHAT_STATE_CHATTING = "chatting"
