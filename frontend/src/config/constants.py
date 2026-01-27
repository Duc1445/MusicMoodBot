"""
Configuration and constants for MusicMoodBot frontend
"""

# ================== COLORS ==================
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
}

# ================== MOOD & INTENSITY ==================
MOOD_CHIPS = ["Vui", "Buồn", "Suy tư", "Chill", "Năng lượng"]
INTENSITY_CHIPS = ["Nhẹ", "Vừa", "Mạnh"]

# ================== MOOD EMOJI MAPPING ==================
MOOD_EMOJI = {
    "Vui": "😊",
    "Buồn": "😢",
    "Suy tư": "🧠",
    "Chill": "😎",
    "Năng lượng": "⚡"
}

INTENSITY_EMOJI = {
    "Nhẹ": "🌿",
    "Vừa": "✨",
    "Mạnh": "🔥"
}

# ================== SAMPLE SONGS ==================
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

# ================== APP INFO ==================
APP_VERSION = "1.0.0"
APP_NAME = "MusicMoodBot"

# ================== CHAT STATES ==================
CHAT_STATE_AWAIT_MOOD = "await_mood"
CHAT_STATE_AWAIT_INTENSITY = "await_intensity"
CHAT_STATE_CHATTING = "chatting"
