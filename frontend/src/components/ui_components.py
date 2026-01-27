"""
Enhanced UI Components for MusicMoodBot
Reusable, stylized components with animations
"""

import flet as ft
from src.config.theme import *


def create_gradient_container(
    gradient: list,
    content,
    padding: int = SPACING_LG,
    border_radius: int = RADIUS_MEDIUM,
    expand: bool = False,
):
    """Create a gradient background container"""
    return ft.Container(
        expand=expand,
        content=content,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=gradient,
        ),
        padding=padding,
        border_radius=border_radius,
    )


def create_glass_container(
    content,
    padding: int = SPACING_LG,
    border_radius: int = RADIUS_MEDIUM,
    opacity: float = 0.95,
    expand: bool = False,
):
    """Create a frosted glass effect container"""
    return ft.Container(
        expand=expand,
        content=content,
        bgcolor=BG_CARD,
        padding=padding,
        border_radius=border_radius,
        border=ft.border.all(1, TEXT_MUTED),
        shadow=ft.BoxShadow(
            blur_radius=12,
            color="#00000030",
            offset=ft.Offset(0, 4),
        ),
    )


def create_mood_chip(mood: str, on_click=None):
    """Create a styled mood selection chip"""
    config = MOOD_CONFIG.get(mood, {})
    emoji = config.get("emoji", "🎵")
    color = config.get("color", PRIMARY_TEAL)
    
    return ft.Container(
        content=ft.Text(
            f"{emoji} {mood}",
            size=FONT_SIZE_BASE,
            weight=FONT_WEIGHT_BOLD,
            color=TEXT_PRIMARY,
        ),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=SPACING_LG, vertical=SPACING_SM),
        border_radius=RADIUS_XL,
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#00000040",
            offset=ft.Offset(0, 2),
        ),
    )


def create_intensity_button(intensity: str, on_click=None):
    """Create a styled intensity selection button"""
    config = INTENSITY_CONFIG.get(intensity, {})
    emoji = config.get("emoji", "✨")
    color = config.get("color", PRIMARY_TEAL)
    
    return ft.Container(
        content=ft.Text(
            f"{emoji} {intensity}",
            size=FONT_SIZE_BASE,
            weight=FONT_WEIGHT_BOLD,
            color=TEXT_PRIMARY,
        ),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=SPACING_MD, vertical=SPACING_SM),
        border_radius=RADIUS_MEDIUM,
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#00000040",
            offset=ft.Offset(0, 2),
        ),
    )


def create_message_bubble(sender: str, text: str):
    """Create a styled message bubble"""
    is_bot = sender == "bot"
    bg_color = BG_CARD if is_bot else PRIMARY_TEAL
    text_color = TEXT_PRIMARY
    
    return ft.Container(
        content=ft.Text(
            text,
            size=FONT_SIZE_SM,
            color=text_color,
        ),
        bgcolor=bg_color,
        padding=SPACING_MD,
        border_radius=RADIUS_MEDIUM,
        shadow=ft.BoxShadow(
            blur_radius=6,
            color="#00000030",
            offset=ft.Offset(0, 2),
        ),
    )


def create_song_card_enhanced(song: dict, on_try_again=None):
    """Create a beautifully styled song recommendation card"""
    song_name = song.get("name", "Unknown Song")
    artist = song.get("artist", "Unknown Artist")
    genre = song.get("genre", "Unknown")
    reason = song.get("reason", "Perfect match for your mood!")
    
    return ft.Container(
        width=520,
        bgcolor=BG_CARD,
        padding=SPACING_LG,
        border_radius=RADIUS_LARGE,
        border=ft.border.all(1, PRIMARY_TEAL),
        shadow=ft.BoxShadow(
            blur_radius=16,
            color="#1abc9c40",
            offset=ft.Offset(0, 4),
        ),
        content=ft.Column(
            spacing=SPACING_MD,
            controls=[
                # Song title
                ft.Text(
                    song_name,
                    size=FONT_SIZE_MD,
                    weight=FONT_WEIGHT_BOLD,
                    color=PRIMARY_LIGHT,
                ),
                # Artist
                ft.Text(
                    f"By {artist}",
                    size=FONT_SIZE_SM,
                    color=TEXT_SECONDARY,
                ),
                # Genre badge
                ft.Container(
                    content=ft.Text(
                        f"🎵 {genre}",
                        size=FONT_SIZE_SM,
                        color=TEXT_PRIMARY,
                    ),
                    bgcolor=PRIMARY_DARK,
                    padding=ft.padding.symmetric(horizontal=SPACING_SM, vertical=SPACING_XS),
                    border_radius=RADIUS_SMALL,
                ),
                # Reason
                ft.Text(
                    reason,
                    size=FONT_SIZE_SM,
                    color=TEXT_SECONDARY,
                    italic=True,
                ),
                # Try again button
                ft.Container(
                    content=ft.Text(
                        "🔄 Try Again",
                        size=FONT_SIZE_BASE,
                        weight=FONT_WEIGHT_BOLD,
                        color=TEXT_PRIMARY,
                    ),
                    bgcolor=PRIMARY_TEAL,
                    padding=ft.padding.symmetric(horizontal=SPACING_LG, vertical=SPACING_SM),
                    border_radius=RADIUS_MEDIUM,
                    on_click=on_try_again,
                    ink=True,
                    shadow=ft.BoxShadow(
                        blur_radius=8,
                        color="#1abc9c40",
                        offset=ft.Offset(0, 2),
                    ),
                ),
            ],
        ),
    )


def create_section_title(title: str, icon: str = ""):
    """Create a styled section title"""
    return ft.Text(
        f"{icon} {title}" if icon else title,
        size=FONT_SIZE_LG,
        weight=FONT_WEIGHT_BOLD,
        color=PRIMARY_LIGHT,
    )


def create_divider():
    """Create a themed divider"""
    return ft.Container(
        height=1,
        bgcolor=TEXT_MUTED,
        opacity=0.3,
    )


def create_button_primary(text: str, on_click=None, icon: str = ""):
    """Create a primary action button"""
    return ft.Container(
        content=ft.Text(
            f"{icon} {text}" if icon else text,
            size=FONT_SIZE_BASE,
            weight=FONT_WEIGHT_BOLD,
            color=TEXT_PRIMARY,
        ),
        bgcolor=PRIMARY_TEAL,
        padding=ft.padding.symmetric(horizontal=SPACING_LG, vertical=SPACING_SM),
        border_radius=RADIUS_MEDIUM,
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(
            blur_radius=8,
            color="#1abc9c40",
            offset=ft.Offset(0, 2),
        ),
    )


def create_button_secondary(text: str, on_click=None, icon: str = ""):
    """Create a secondary action button"""
    return ft.Container(
        content=ft.Text(
            f"{icon} {text}" if icon else text,
            size=FONT_SIZE_BASE,
            weight=FONT_WEIGHT_BOLD,
            color=PRIMARY_TEAL,
        ),
        bgcolor=BG_CARD,
        padding=ft.padding.symmetric(horizontal=SPACING_LG, vertical=SPACING_SM),
        border_radius=RADIUS_MEDIUM,
        border=ft.border.all(2, PRIMARY_TEAL),
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(
            blur_radius=6,
            color="#00000020",
            offset=ft.Offset(0, 2),
        ),
    )


def create_info_box(title: str, content: str, icon: str = "ℹ️"):
    """Create an info/notification box"""
    return ft.Container(
        bgcolor=BG_CARD,
        padding=SPACING_LG,
        border_radius=RADIUS_MEDIUM,
        border=ft.border.all(1, INFO),
        content=ft.Column(
            spacing=SPACING_SM,
            controls=[
                ft.Text(f"{icon} {title}", size=FONT_SIZE_BASE, weight=FONT_WEIGHT_BOLD, color=INFO),
                ft.Text(content, size=FONT_SIZE_SM, color=TEXT_SECONDARY),
            ],
        ),
    )
