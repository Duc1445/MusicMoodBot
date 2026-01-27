# MusicMoodBot UI Styling Guide

## 📋 Overview

MusicMoodBot có hệ thống styling modular gồm 2 file chính:

- **`src/config/theme.py`** - Color palettes, gradients, spacing, typography
- **`src/components/ui_components.py`** - Reusable styled components

Những file này **không ảnh hưởng** đến core functionality. Chỉ cần thay đổi styling ở đây mà không cần modify screens.

---

## 🎨 Theme Customization

### Colors

```python
from src.config.theme import PRIMARY_TEAL, BG_DARK, MOOD_VUI

# Primary colors
PRIMARY_TEAL = "#1abc9c"
PRIMARY_DARK = "#0d4f3f"
PRIMARY_LIGHT = "#52e1c9"

# Backgrounds
BG_DARK = "#0f1419"
BG_CARD = "#1a1f26"

# Mood colors
MOOD_VUI = "#FFD700"       # Happy - Gold
MOOD_BUON = "#4169E1"      # Sad - Blue
MOOD_SUYTU = "#FF6B6B"     # Thoughtful - Red
```

### Gradients

```python
from src.config.theme import GRADIENT_MAIN, GRADIENT_MOOD_VUI

GRADIENT_MAIN = ["#1abc9c", "#0d7377"]      # Teal gradient
GRADIENT_MOOD_VUI = ["#FFD700", "#FFA500"]  # Gold to orange
```

### Spacing & Border Radius

```python
from src.config.theme import SPACING_MD, RADIUS_LARGE

SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24

RADIUS_SMALL = 8
RADIUS_MEDIUM = 12
RADIUS_LARGE = 16
```

---

## 🧩 Using UI Components

### Mood Chip

```python
from src.components.ui_components import create_mood_chip

mood_chip = create_mood_chip(
    mood="Vui",
    on_click=handle_mood_click
)
```

**Features:**
- Auto emoji + color from theme
- Shadow effect
- Ink ripple on click

### Intensity Button

```python
from src.components.ui_components import create_intensity_button

button = create_intensity_button(
    intensity="Mạnh",
    on_click=handle_intensity_click
)
```

### Message Bubble

```python
from src.components.ui_components import create_message_bubble

bubble = create_message_bubble(
    sender="bot",  # or "user"
    text="Hello!"
)
```

### Song Card

```python
from src.components.ui_components import create_song_card_enhanced

card = create_song_card_enhanced(
    song={
        "name": "Song Title",
        "artist": "Artist Name",
        "genre": "Pop",
        "reason": "Perfect match!"
    },
    on_try_again=handle_try_again
)
```

### Gradient Container

```python
from src.components.ui_components import create_gradient_container
from src.config.theme import GRADIENT_MAIN

container = create_gradient_container(
    gradient=GRADIENT_MAIN,
    content=ft.Text("Content here"),
    padding=16,
    border_radius=12,
)
```

### Buttons

```python
from src.components.ui_components import create_button_primary, create_button_secondary

primary = create_button_primary(
    text="Save",
    icon="💾",
    on_click=handle_save
)

secondary = create_button_secondary(
    text="Cancel",
    icon="✕",
    on_click=handle_cancel
)
```

---

## 🎯 How to Apply to Existing Screens

### Example: Update chat_screen.py

**Before:**
```python
def bubble_for_text(sender: str, text: str):
    """Create message bubble"""
    is_bot = (sender == "bot")
    bg = COLORS["light_gray"] if is_bot else COLORS["accent_teal"]
    fg = COLORS["border_dark"] if is_bot else COLORS["white"]

    return ft.Row(
        alignment=ft.MainAxisAlignment.END if not is_bot else ft.MainAxisAlignment.START,
        controls=[
            ft.Container(
                content=ft.Text(text, color=fg, size=11),
                bgcolor=bg,
                padding=12,
                border_radius=12,
                width=520,
            )
        ]
    )
```

**After:**
```python
from src.components.ui_components import create_message_bubble

def bubble_for_text(sender: str, text: str):
    """Create message bubble"""
    bubble = create_message_bubble(sender, text)
    return ft.Row(
        alignment=ft.MainAxisAlignment.END if sender != "bot" else ft.MainAxisAlignment.START,
        controls=[bubble]
    )
```

---

## 🔧 Customization Examples

### Change Primary Color

Edit `src/config/theme.py`:
```python
PRIMARY_TEAL = "#2E86AB"  # Change to your color
```

All components using `PRIMARY_TEAL` automatically update!

### Add New Mood Color

Edit `src/config/theme.py`:
```python
MOOD_CONFIG = {
    ...
    "Năng động": {
        "emoji": "⚡",
        "color": "#FF1493",
        "gradient": ["#FF1493", "#FF69B4"],
    },
}
```

Then use:
```python
chip = create_mood_chip("Năng động")  # Auto-styled!
```

### Adjust Spacing

```python
from src.config.theme import SPACING_LG

# Use in any container
container = ft.Container(
    padding=SPACING_LG * 2,  # Double padding
)
```

---

## 📚 Current Styling Features

✅ **Colors**
- 5 mood colors
- 3 intensity colors
- Dark theme (BG_DARK, BG_CARD)
- Text color hierarchy

✅ **Shadows & Depth**
- 3 shadow levels (light, medium, heavy)
- Components have box shadows

✅ **Animations**
- Ink ripple on buttons
- Smooth transitions

✅ **Components**
- Mood chips with auto-styling
- Intensity buttons
- Message bubbles
- Song cards (enhanced)
- Gradient containers
- Primary/Secondary buttons

---

## 🚀 Future Enhancements

- [ ] Dark/Light mode toggle
- [ ] Custom animations (slide in, fade)
- [ ] Skeleton loading
- [ ] Toast notifications
- [ ] More button variants
- [ ] Avatar components

---

## 📝 Notes

- All components are in `ui_components.py`
- All colors/spacing are in `theme.py`
- No changes needed to core screen files!
- Components are composable - combine them freely
