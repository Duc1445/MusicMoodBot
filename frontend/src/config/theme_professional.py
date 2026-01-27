"""
MusicMoodBot Professional Theme - Modern Glassmorphism Design
Sophisticated dark theme inspired by contemporary applications
Version: 2.0 - Premium Edition
"""

# =============== DESIGN TOKENS ===============
# Professional color palette with modern aesthetic

# ========== BASE COLORS ==========
# Primary Brand Colors
PRIMARY_ACCENT = "#00D9FF"          # Cyan - Modern tech color
PRIMARY_ACCENT_LIGHT = "#33E5FF"    # Light Cyan
PRIMARY_ACCENT_DARK = "#00A8CC"     # Dark Cyan

# Background - Premium Dark Mode
BG_DARKEST = "#0A0E17"   # Ultra dark - behind modals
BG_DARK = "#0F1419"      # Primary background
BG_SECONDARY = "#131A24" # Secondary areas
BG_CARD = "#1A232F"      # Card/Container backgrounds
BG_CARD_HOVER = "#232D3D" # Hover state
BG_INPUT = "#141D2A"     # Input fields
BG_OVERLAY = "#0F141988" # Semi-transparent overlay

# Glassmorphism - Frosted glass effect
GLASS_LIGHT = "#1A232F80"   # Light glass (semi-transparent)
GLASS_MEDIUM = "#1A232F99"  # Medium glass
GLASS_DARK = "#0F1419CC"    # Dark glass

# Text & Typography
TEXT_PRIMARY = "#FFFFFF"
TEXT_SECONDARY = "#8FA3C0"
TEXT_TERTIARY = "#617A94"
TEXT_MUTED = "#475569"
TEXT_DISABLED = "#364558"

# Divider & Borders
BORDER_COLOR = "#1F2937"
DIVIDER_COLOR = "#1F293799"

# ========== MOOD COLORS - PREMIUM PALETTE ==========
# Carefully selected colors for mood representation
MOOD_VUI = "#FFD93D"       # Golden Yellow - Joy, Energy, Happiness
MOOD_BUON = "#6C8ADB"      # Soft Blue - Sadness, Melancholy
MOOD_SUYTU = "#E76B6B"     # Rose Red - Thoughtfulness, Contemplation
MOOD_CHILL = "#4ECDC4"     # Turquoise - Relaxation, Calmness
MOOD_NANGLUO = "#FF9F66"   # Warm Orange - Excitement, Energy

# Mood color variations
MOOD_VUI_LIGHT = "#FFE66D"
MOOD_BUON_LIGHT = "#8FA3DB"
MOOD_SUYTU_LIGHT = "#FF9999"
MOOD_CHILL_LIGHT = "#7FE0DB"
MOOD_NANGLUO_LIGHT = "#FFBA99"

# ========== INTENSITY COLORS ==========
INTENSITY_NHE = "#81D4FA"     # Light - Soft Blue
INTENSITY_TRUNG = "#64B5F6"   # Medium - Standard Blue
INTENSITY_MANH = "#FF7043"    # Strong - Deep Orange

# ========== STATUS COLORS ==========
SUCCESS = "#52D273"    # Green
ERROR = "#FF5252"      # Red
WARNING = "#FFB74D"    # Orange
INFO = "#29B6F6"       # Light Blue

# ========== INTERACTIVE STATES ==========
HOVER_OVERLAY = "#FFFFFF08"   # Slight white overlay on hover
ACTIVE_OVERLAY = "#00D9FF20"  # Accent overlay on active
FOCUS_RING = "#00D9FF"        # Focus ring color
DISABLED_OPACITY = 0.5        # Opacity for disabled elements

# =============== GRADIENTS ===============
# Modern gradients for backgrounds and accents

GRADIENT_MAIN = [PRIMARY_ACCENT, "#00A8CC"]           # Cyan gradient
GRADIENT_SECONDARY = ["#1A232F", "#0F1419"]           # Dark card gradient
GRADIENT_MOOD_VUI = [MOOD_VUI, "#FFC107"]             # Happy gradient
GRADIENT_MOOD_BUON = [MOOD_BUON, "#1E3A8A"]          # Sad gradient
GRADIENT_MOOD_SUYTU = [MOOD_SUYTU, "#C53030"]        # Pensive gradient
GRADIENT_MOOD_CHILL = [MOOD_CHILL, "#2C9E9E"]        # Chill gradient
GRADIENT_MOOD_NANGLUO = [MOOD_NANGLUO, "#FF6B35"]    # Excited gradient

# Premium background gradients
GRADIENT_BG_DARK = ["#0F1419", "#1A232F"]
GRADIENT_BG_CARD = ["#1A232F", "#131A24"]

# =============== SHADOWS ===============
# Professional shadow system for depth

# Subtle shadows for glass effect
SHADOW_SUBTLE = {
    "blur_radius": 4,
    "color": "#00000030",
    "offset": (0, 1),
}

# Small shadows for cards and buttons
SHADOW_SMALL = {
    "blur_radius": 8,
    "color": "#00000040",
    "offset": (0, 2),
}

# Medium shadows for elevated content
SHADOW_MEDIUM = {
    "blur_radius": 16,
    "color": "#00000050",
    "offset": (0, 4),
}

# Large shadows for modals and overlays
SHADOW_LARGE = {
    "blur_radius": 32,
    "color": "#00000060",
    "offset": (0, 8),
}

# Glow effect (for active/focus states)
SHADOW_GLOW = {
    "blur_radius": 12,
    "color": "#00D9FF40",
    "offset": (0, 0),
}

# =============== SPACING SYSTEM ===============
# Consistent spacing scale (4px base unit)

SPACING_XS = 4      # Minimal
SPACING_SM = 8      # Small
SPACING_MD = 12     # Medium
SPACING_LG = 16     # Large
SPACING_XL = 24     # Extra Large
SPACING_XXL = 32    # Double Extra Large
SPACING_3XL = 40    # 3X Extra Large
SPACING_4XL = 48    # 4X Extra Large

# =============== BORDER RADIUS ===============
# Modern rounded corners

RADIUS_NONE = 0
RADIUS_SMALL = 4     # Subtle rounding
RADIUS_MEDIUM = 8    # Standard button/input
RADIUS_LARGE = 12    # Cards and containers
RADIUS_XL = 16       # Large components
RADIUS_FULL = 24     # Fully rounded

# =============== TYPOGRAPHY ===============
# Professional type scale

# Font Sizes
FONT_SIZE_TINY = 10
FONT_SIZE_SMALL = 12
FONT_SIZE_SM = 13
FONT_SIZE_BASE = 14
FONT_SIZE_MD = 15
FONT_SIZE_LG = 16
FONT_SIZE_XL = 18
FONT_SIZE_2XL = 20
FONT_SIZE_3XL = 24
FONT_SIZE_TITLE = 28

# Font Weights
FONT_WEIGHT_LIGHT = 300
FONT_WEIGHT_NORMAL = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_SEMIBOLD = 600
FONT_WEIGHT_BOLD = 700

# Line Heights
LINE_HEIGHT_TIGHT = 1.2
LINE_HEIGHT_NORMAL = 1.5
LINE_HEIGHT_RELAXED = 1.75

# =============== ANIMATIONS ===============
# Duration values for transitions and animations

DURATION_FAST = 100      # Quick feedback
DURATION_NORMAL = 300    # Standard transition
DURATION_SLOW = 500      # Smooth animation

# =============== CONFIGURATION DICTIONARIES ===============

# Mood Configuration - Auto-styling based on mood selection
MOOD_CONFIG = {
    "Vui": {
        "emoji": "😊",
        "color": MOOD_VUI,
        "color_light": MOOD_VUI_LIGHT,
        "gradient": GRADIENT_MOOD_VUI,
    },
    "Buồn": {
        "emoji": "😢",
        "color": MOOD_BUON,
        "color_light": MOOD_BUON_LIGHT,
        "gradient": GRADIENT_MOOD_BUON,
    },
    "Suy tư": {
        "emoji": "🤔",
        "color": MOOD_SUYTU,
        "color_light": MOOD_SUYTU_LIGHT,
        "gradient": GRADIENT_MOOD_SUYTU,
    },
    "Chill": {
        "emoji": "😎",
        "color": MOOD_CHILL,
        "color_light": MOOD_CHILL_LIGHT,
        "gradient": GRADIENT_MOOD_CHILL,
    },
    "Nâng lương": {
        "emoji": "🚀",
        "color": MOOD_NANGLUO,
        "color_light": MOOD_NANGLUO_LIGHT,
        "gradient": GRADIENT_MOOD_NANGLUO,
    },
}

# Intensity Configuration - Auto-styling based on intensity
INTENSITY_CONFIG = {
    "Nhẹ": {
        "emoji": "🌤️",
        "color": INTENSITY_NHE,
        "description": "Light & Soft",
    },
    "Vừa": {
        "emoji": "🌦️",
        "color": INTENSITY_TRUNG,
        "description": "Balanced",
    },
    "Mạnh": {
        "emoji": "⛈️",
        "color": INTENSITY_MANH,
        "description": "Heavy & Intense",
    },
}
