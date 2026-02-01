"""
Unified constants for MusicMoodBot (Backend + Frontend)
This is the SINGLE SOURCE OF TRUTH for all constants.
"""

from typing import Dict, List

# ================== DATABASE ==================
TABLE_SONGS = "songs"

# ================== MOODS ==================
# English moods (for backend ML engine)
MOODS = ["energetic", "happy", "sad", "stress", "angry"]

# Vietnamese moods (for frontend display)
MOODS_VI = ["Vui", "Buồn", "Suy tư", "Chill", "Năng lượng"]

# Mapping Vietnamese moods to English moods (for ML engine)
MOOD_VI_TO_EN = {
    "Vui": "happy",
    "Buồn": "sad",
    "Suy tư": "stress",
    "Chill": "happy",
    "Năng lượng": "energetic"
}

# Mapping English moods to Vietnamese (for display)
MOOD_EN_TO_VI = {
    "happy": "Vui",
    "sad": "Buồn",
    "stress": "Suy tư",
    "energetic": "Năng lượng",
    "angry": "Năng lượng"
}

# Mood emoji mapping
MOOD_EMOJI = {
    "Vui": "😊",
    "Buồn": "😢",
    "Suy tư": "🧠",
    "Chill": "😎",
    "Năng lượng": "⚡",
    "happy": "😊",
    "sad": "😢",
    "stress": "🧠",
    "energetic": "⚡",
    "angry": "😠"
}

# Mood descriptions (Vietnamese)
MOOD_DESCRIPTIONS_VI = {
    "Vui": "Tâm trạng vui vẻ, tích cực",
    "Buồn": "Tâm trạng buồn bã, u sầu",
    "Suy tư": "Tâm trạng suy nghĩ, trầm ngâm",
    "Chill": "Tâm trạng thư giãn, bình yên",
    "Năng lượng": "Tâm trạng sôi động, năng động"
}

# Mood descriptions (English)
MOOD_DESCRIPTIONS_EN = {
    "energetic": "High energy, upbeat, exciting",
    "happy": "Joyful, positive, cheerful",
    "sad": "Melancholic, emotional, touching",
    "stress": "Tense, anxious, thoughtful",
    "angry": "Intense, powerful, aggressive"
}

# ================== INTENSITY ==================
INTENSITIES = ["Nhẹ", "Vừa", "Mạnh"]
INTENSITIES_EN = ["low", "medium", "high"]

# Intensity emoji mapping
INTENSITY_EMOJI = {
    "Nhẹ": "🌿",
    "Vừa": "✨",
    "Mạnh": "🔥",
    "low": "🌿",
    "medium": "✨",
    "high": "🔥"
}

# Intensity mapping VI to EN
INTENSITY_VI_TO_EN = {
    "Nhẹ": "low",
    "Vừa": "medium",
    "Mạnh": "high"
}

# Intensity mapping EN to VI
INTENSITY_EN_TO_VI = {
    "low": "Nhẹ",
    "medium": "Vừa",
    "high": "Mạnh"
}

# ================== AUDIO FEATURES ==================
FEATURE_RANGES = {
    "energy": (0, 100),
    "happiness": (0, 100),
    "valence": (0, 100),
    "danceability": (0, 100),
    "acousticness": (0, 100),
    "tempo": (0, 250),
    "loudness": (-60, 0),
    "intensity": (1, 3)
}

DEFAULT_FEATURES = {
    "energy": 50,
    "happiness": 50,
    "valence": 50,
    "danceability": 50,
    "acousticness": 50,
    "tempo": 120,
    "loudness": -10
}

# ================== UI COLORS ==================
COLORS = {
    "cream_bg": "#F6F3EA",
    "white": "#FFFFFF",
    "border_dark": "#111111",
    "button_dark": "#2F2F2F",
    "accent_teal": "#3FB5B3",
    "text_gray": "#6B6B6B",
    "online_green": "#2ECC71",
    "mood_sad": "#BFD7FF",
    "mood_think": "#D7C7FF",
    "mood_happy": "#BFEFC9",
    "date_yellow": "#F6D25C",
    "light_gray": "#EFEFEF",
    "primary_accent": "#00D9FF",
    "secondary_accent": "#FF6B9D",
}

MOOD_COLORS = {
    "Vui": "#FFD93D",
    "Buồn": "#6C9BCF",
    "Suy tư": "#9B59B6",
    "Chill": "#26D07C",
    "Năng lượng": "#FF6B6B"
}

# ================== APP INFO ==================
APP_VERSION = "2.0.0"
APP_NAME = "MusicMoodBot"
APP_DESCRIPTION = "Gợi ý nhạc theo tâm trạng với AI thông minh"

# ================== CHAT STATES ==================
CHAT_STATE_AWAIT_MOOD = "await_mood"
CHAT_STATE_AWAIT_INTENSITY = "await_intensity"
CHAT_STATE_CHATTING = "chatting"

# ================== API CONFIGURATION ==================
API_BASE_URL = "http://localhost:8000/api/moods"
API_TIMEOUT = 10  # seconds

# ================== FEATURE FLAGS ==================
FEATURES = {
    "smart_recommendation": True,
    "text_mood_detection": True,
    "vietnamese_search": True,
    "user_preferences": True,
    "password_hashing": True,
    "state_persistence": True
}

# ================== BOT MESSAGES ==================
BOT_MESSAGES = {
    "welcome": "Xin chào! Mình là MusicMoodBot 🎵\nHôm nay bạn đang cảm thấy thế nào?",
    "ask_mood": "Bạn đang có tâm trạng như thế nào?",
    "ask_intensity": "Ok. Bạn muốn intensity mức nào? (Nhẹ / Vừa / Mạnh)",
    "thinking": "Bot đang suy nghĩ...",
    "not_understood": "Mình chưa hiểu ý bạn. Hãy chọn 1 mood bằng nút bên dưới.",
    "try_again": "Được rồi, mình thử gợi ý bài khác nhé!",
    "error": "Oops! Có lỗi xảy ra. Vui lòng thử lại."
}

# ================== SAMPLE SONGS (for demo/testing) ==================
SAMPLE_SONGS = [
    {
        "name": "Mưa Tháng Sáu",
        "artist": "Văn Mai Hương",
        "genre": "Ballad",
        "suy_score": 8.8,
        "reason": "Giai điệu chậm, vocal mềm, hợp mood trầm.",
        "moods": ["Buồn", "Suy tư"]
    },
    {
        "name": "Có Chàng Trai Viết Lên Cây",
        "artist": "Phan Mạnh Quỳnh",
        "genre": "Ballad",
        "suy_score": 7.2,
        "reason": "Nostalgia nhẹ, hợp khi cần thả cảm xúc.",
        "moods": ["Buồn", "Chill"]
    },
    {
        "name": "Ngày Chưa Giông Bão",
        "artist": "Bùi Lan Hương",
        "genre": "Indie/Pop",
        "suy_score": 7.9,
        "reason": "Không khí suy tư, cinematic, hợp tập trung.",
        "moods": ["Suy tư", "Chill"]
    },
    {
        "name": "Cô Gái M52",
        "artist": "HuyR x Tùng Viu",
        "genre": "Pop",
        "suy_score": 2.5,
        "reason": "Nhịp vui, bắt tai, hợp mood tích cực.",
        "moods": ["Vui", "Năng lượng"]
    },
    {
        "name": "Bước Qua Nhau",
        "artist": "Vũ.",
        "genre": "Indie",
        "suy_score": 6.9,
        "reason": "Chill nhẹ, hợp nghe đêm, không quá nặng.",
        "moods": ["Chill", "Suy tư"]
    },
    {
        "name": "Nơi Này Có Anh",
        "artist": "Sơn Tùng M-TP",
        "genre": "Pop",
        "suy_score": 3.8,
        "reason": "Tươi sáng, lời tích cực, hợp tâm trạng vui.",
        "moods": ["Vui"]
    },
]
