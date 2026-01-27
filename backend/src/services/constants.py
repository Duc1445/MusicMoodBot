"""Shared constants for the mood engine module."""

from typing import Dict, List

# Database configuration
TABLE_SONGS = "songs"

# Mood labels (English - for backend ML engine)
MOODS = ["energetic", "happy", "sad", "stress", "angry"]

# Vietnamese mood labels (for frontend)
MOODS_VI = ["Vui", "Buồn", "Suy tư", "Chill", "Năng lượng"]

# Intensity levels
INTENSITIES = ["Nhẹ", "Vừa", "Mạnh"]
INTENSITIES_EN = ["low", "medium", "high"]

# Mapping Vietnamese moods to English moods (for ML engine)
MOOD_VI_TO_EN = {
    "Vui": "happy",
    "Buồn": "sad",
    "Suy tư": "stress",  # thinking/contemplating maps to stress
    "Chill": "happy",    # chill maps to happy (low arousal happy)
    "Năng lượng": "energetic"
}

# Mapping English moods to Vietnamese (for display)
MOOD_EN_TO_VI = {
    "happy": "Vui",
    "sad": "Buồn",
    "stress": "Suy tư",
    "energetic": "Năng lượng",
    "angry": "Năng lượng"  # angry maps to high energy
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

# Type aliases
Song = Dict[str, object]

# Audio feature ranges for validation
FEATURE_RANGES = {
    "energy": (0, 100),
    "happiness": (0, 100),
    "valence": (0, 100),
    "danceability": (0, 100),
    "acousticness": (0, 100),
    "tempo": (0, 250),  # BPM
    "loudness": (-60, 0),  # dBFS
    "intensity": (1, 3)
}

# Default feature values when missing
DEFAULT_FEATURES = {
    "energy": 50,
    "happiness": 50,
    "valence": 50,
    "danceability": 50,
    "acousticness": 50,
    "tempo": 120,
    "loudness": -10
}
