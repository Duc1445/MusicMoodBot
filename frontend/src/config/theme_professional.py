"""
MusicMoodBot Professional Theme - Modern Glassmorphism Design
Sophisticated dark theme inspired by contemporary applications
Version: 2.0 - Premium Edition
"""

# =============== DESIGN TOKENS ===============
# Professional color palette with modern aesthetic

# ========== BASE COLORS ==========
# Primary Brand Colors - Updated for Figma design
PRIMARY_ACCENT = "#00D9FF"          # Cyan - Modern tech color
PRIMARY_ACCENT_LIGHT = "#33E5FF"    # Light Cyan
PRIMARY_ACCENT_DARK = "#00A8CC"     # Dark Cyan

# Background - Light theme for Figma design
BG_LIGHT = "#FFFFFF"        # White background
BG_LIGHT_GRAY = "#F8F9FA"   # Light gray for cards
BG_LIGHT_SECONDARY = "#F1F3F4" # Secondary light areas
BG_LIGHT_CARD = "#FFFFFF"   # Card backgrounds (white)
BG_LIGHT_CARD_HOVER = "#F8F9FA" # Hover state
BG_LIGHT_INPUT = "#FFFFFF"  # Input fields (white)
BG_LIGHT_OVERLAY = "#0000000D" # Semi-transparent overlay

# Glassmorphism - Light theme glass effect
GLASS_LIGHT_FIGMA = "#FFFFFFCC"   # Light glass (semi-transparent white)
GLASS_MEDIUM_FIGMA = "#FFFFFFE6"  # Medium glass
GLASS_DARK_FIGMA = "#FFFFFF99"    # Dark glass

# Text & Typography - Dark text for light theme
TEXT_PRIMARY_FIGMA = "#1A1A1A"    # Dark gray/black primary text
TEXT_SECONDARY_FIGMA = "#5F6368"  # Secondary text
TEXT_TERTIARY_FIGMA = "#80868B"   # Tertiary text
TEXT_MUTED_FIGMA = "#9AA0A6"      # Muted text
TEXT_DISABLED_FIGMA = "#BDC1C6"   # Disabled text

# Divider & Borders - Light theme
BORDER_COLOR_FIGMA = "#E0E0E0"    # Light gray borders
DIVIDER_COLOR_FIGMA = "#E8EAED"   # Light dividers

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
# Professional shadow system for depth - Updated for Figma light theme

# Subtle shadows for glass effect - Figma spec
SHADOW_SUBTLE_FIGMA = {
    "blur_radius": 20,
    "color": "#0000000D",  # rgba(0,0,0,0.05)
    "offset": (0, 4),
}

# Small shadows for cards and buttons - Figma spec
SHADOW_SMALL_FIGMA = {
    "blur_radius": 20,
    "color": "#0000000D",  # rgba(0,0,0,0.05)
    "offset": (0, 4),
}

# Medium shadows for elevated content
SHADOW_MEDIUM_FIGMA = {
    "blur_radius": 20,
    "color": "#0000000D",  # rgba(0,0,0,0.05)
    "offset": (0, 4),
}

# Large shadows for modals and overlays
SHADOW_LARGE_FIGMA = {
    "blur_radius": 20,
    "color": "#0000000D",  # rgba(0,0,0,0.05)
    "offset": (0, 4),
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
# Modern rounded corners - Updated for Figma

RADIUS_NONE = 0
RADIUS_SMALL = 4     # Subtle rounding
RADIUS_MEDIUM = 8    # Standard button/input
RADIUS_LARGE = 12    # Cards and containers (Figma spec)
RADIUS_XL = 25       # Large components (buttons - pill shape)
RADIUS_FULL = 50     # Fully rounded

# =============== TYPOGRAPHY ===============
# Professional type scale

# Font Sizes - Updated for Figma specs
FONT_SIZE_TINY = 10
FONT_SIZE_SMALL = 12    # Small text/version (Figma: 12px)
FONT_SIZE_SM = 13
FONT_SIZE_BASE = 14     # Body/Labels (Figma: 14px-16px)
FONT_SIZE_MD = 15
FONT_SIZE_LG = 16       # Body/Labels (Figma: 14px-16px)
FONT_SIZE_XL = 18
FONT_SIZE_2XL = 24      # Headline (Figma: 24px-28px)
FONT_SIZE_3XL = 28      # Headline (Figma: 24px-28px)
FONT_SIZE_TITLE = 28    # Headline (Figma: 24px-28px)

# Font Families - Figma specs
FONT_FAMILY_FIGMA_HEADLINE = "Quicksand, sans-serif"  # Headlines
FONT_FAMILY_FIGMA_BODY = "Nunito, sans-serif"        # Body text

# Font Weights - Updated for Figma
FONT_WEIGHT_LIGHT = 300
FONT_WEIGHT_NORMAL = 400
FONT_WEIGHT_MEDIUM = 500    # Body text (Figma: Medium)
FONT_WEIGHT_SEMIBOLD = 600
FONT_WEIGHT_BOLD = 700      # Headlines (Figma: Bold)

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
