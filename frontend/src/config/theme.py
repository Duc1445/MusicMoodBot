"""
MusicMoodBot Theme & Styling Configuration
Colors, gradients, and UI styling constants
"""

# =============== COLOR PALETTES ===============

# Main brand colors
PRIMARY_TEAL = "#1abc9c"
PRIMARY_DARK = "#0d4f3f"
PRIMARY_LIGHT = "#52e1c9"

# Background colors
BG_DARK = "#0f1419"
BG_DARKER = "#0a0e12"
BG_CARD = "#1a1f26"
BG_INPUT = "#252d35"

# Accent colors - by mood
MOOD_VUI = "#FFD700"      # Vui (Happy) - Gold
MOOD_BUON = "#4169E1"     # Buồn (Sad) - Royal Blue
MOOD_SUYTU = "#FF6B6B"    # Suy tư (Thoughtful) - Red
MOOD_CHILL = "#20B2AA"    # Chill - Light Sea Green
MOOD_NANGLUO = "#FF8C00"  # Nâng lương (Energetic) - Dark Orange

# Intensity colors
INTENSITY_Nvancouver = "#7FFFD4"  # Nhẹ (Light) - Aquamarine
INTENSITY_TRUNG = "#20B2AA"       # Vừa (Medium) - Light Sea Green
INTENSITY_MANH = "#FF6347"        # Mạnh (Strong) - Tomato

# Text colors
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#B0B8C1"
TEXT_MUTED = "#7A8590"

# Utility colors
SUCCESS = "#27AE60"
WARNING = "#F39C12"
ERROR = "#E74C3C"
INFO = "#3498DB"

# =============== GRADIENTS ===============

GRADIENT_MAIN = ["#1abc9c", "#0d7377"]      # Teal to dark teal
GRADIENT_MOOD_VUI = ["#FFD700", "#FFA500"]  # Gold to orange
GRADIENT_MOOD_BUON = ["#4169E1", "#1E3A8A"] # Royal blue to deep blue
GRADIENT_SIDEBAR = ["#0f1419", "#1a1f26"]   # Dark gradient

# =============== SHADOWS ===============

SHADOW_LIGHT = "0px 2px 8px rgba(0, 0, 0, 0.15)"
SHADOW_MEDIUM = "0px 4px 16px rgba(0, 0, 0, 0.25)"
SHADOW_HEAVY = "0px 8px 24px rgba(0, 0, 0, 0.35)"

# =============== BORDER RADIUS ===============

RADIUS_SMALL = 8
RADIUS_MEDIUM = 12
RADIUS_LARGE = 16
RADIUS_XL = 24

# =============== SPACING ===============

SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_XXL = 32

# =============== TYPOGRAPHY ===============

FONT_SIZE_TINY = 10
FONT_SIZE_SM = 11
FONT_SIZE_BASE = 12
FONT_SIZE_MD = 14
FONT_SIZE_LG = 16
FONT_SIZE_XL = 20
FONT_SIZE_XXL = 24
FONT_SIZE_TITLE = 28

FONT_WEIGHT_NORMAL = "normal"
FONT_WEIGHT_BOLD = "bold"

# =============== ANIMATION DURATIONS (ms) ===============

DURATION_FAST = 100
DURATION_NORMAL = 300
DURATION_SLOW = 500

# =============== MOOD EMOJI & COLORS ===============

MOOD_CONFIG = {
    "Vui": {
        "emoji": "😊",
        "color": MOOD_VUI,
        "gradient": GRADIENT_MOOD_VUI,
    },
    "Buồn": {
        "emoji": "😢",
        "color": MOOD_BUON,
        "gradient": GRADIENT_MOOD_BUON,
    },
    "Suy tư": {
        "emoji": "🤔",
        "color": MOOD_SUYTU,
        "gradient": ["#FF6B6B", "#FF4757"],
    },
    "Chill": {
        "emoji": "😎",
        "color": MOOD_CHILL,
        "gradient": ["#20B2AA", "#008B8B"],
    },
    "Nâng lương": {
        "emoji": "🔥",
        "color": MOOD_NANGLUO,
        "gradient": ["#FF8C00", "#FF6347"],
    },
}

# =============== INTENSITY CONFIG ===============

INTENSITY_CONFIG = {
    "Nhẹ": {
        "emoji": "🌿",
        "color": INTENSITY_Nvancouver,
    },
    "Vừa": {
        "emoji": "✨",
        "color": INTENSITY_TRUNG,
    },
    "Mạnh": {
        "emoji": "🔥",
        "color": INTENSITY_MANH,
    },
}
