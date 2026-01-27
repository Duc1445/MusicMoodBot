"""
MusicMoodBot Professional UI Components - Glassmorphism Edition
Modern, sophisticated components with glass effect and smooth interactions
Version: 2.0 - Premium Components
"""

import flet as ft
from src.config.theme_professional import *


# =============== FUNDAMENTAL COMPONENTS ===============

def create_glassmorphic_container(
    content,
    padding: int = SPACING_MD,
    border_radius: int = RADIUS_LARGE,
    opacity: float = 0.95,
    shadow=SHADOW_MEDIUM,
    expand: bool = False,
):
    """
    Create a glassmorphism container with frosted glass effect
    Modern frosted glass effect with subtle shadow and border
    """
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=GLASS_MEDIUM,
        border_radius=border_radius,
        border=ft.border.all(1, BORDER_COLOR),
        shadow=ft.BoxShadow(
            blur_radius=shadow["blur_radius"],
            color=shadow["color"],
            offset=ft.Offset(shadow["offset"][0], shadow["offset"][1]),
        ),
        expand=expand,
    )


def create_gradient_button(
    text: str,
    on_click=None,
    icon: str = None,
    gradient_colors=None,
    width: int = None,
    height: int = 48,
    icon_size: int = 18,
):
    """Premium gradient button with icon support"""
    if gradient_colors is None:
        gradient_colors = [PRIMARY_ACCENT_DARK, PRIMARY_ACCENT]
    
    button_content = ft.Row(
        spacing=SPACING_SM,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Text(
                icon,
                size=icon_size,
                color=TEXT_PRIMARY,
            ) if icon else None,
            ft.Text(
                text,
                size=FONT_SIZE_LG,
                weight=FONT_WEIGHT_SEMIBOLD,
                color=TEXT_PRIMARY,
            ),
        ],
    )
    button_content.controls = [c for c in button_content.controls if c is not None]
    
    return ft.Container(
        content=button_content,
        width=width,
        height=height,
        padding=SPACING_MD,
        border_radius=RADIUS_MEDIUM,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=gradient_colors,
        ),
        shadow=ft.BoxShadow(
            blur_radius=8,
            color=f"{gradient_colors[0]}30",
            offset=ft.Offset(0, 2),
        ),
        on_click=on_click,
        alignment=ft.Alignment(0, 0),
    )


def create_text_input_professional(
    label: str,
    placeholder: str = "",
    password: bool = False,
    on_change=None,
    icon: str = None,
):
    """Professional text input with icon and label"""
    return ft.Column(
        spacing=SPACING_SM,
        controls=[
            ft.Text(
                label,
                size=FONT_SIZE_SM,
                color=TEXT_SECONDARY,
                weight=FONT_WEIGHT_MEDIUM,
            ),
            ft.Container(
                height=44,
                border_radius=RADIUS_MEDIUM,
                bgcolor=BG_INPUT,
                border=ft.border.all(1, BORDER_COLOR),
                padding=ft.padding.only(left=SPACING_MD, right=SPACING_MD),
                content=ft.Row(
                    spacing=SPACING_SM,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(icon, size=FONT_SIZE_LG) if icon else None,
                        ft.TextField(
                            border=ft.InputBorder.NONE,
                            bgcolor="transparent",
                            hint_text=placeholder,
                            hint_style=ft.TextStyle(
                                color=TEXT_MUTED,
                                size=FONT_SIZE_BASE,
                            ),
                            text_style=ft.TextStyle(
                                color=TEXT_PRIMARY,
                                size=FONT_SIZE_BASE,
                            ),
                            password=password,
                            on_change=on_change,
                            filled=False,
                        ),
                    ],
                ),
            ),
        ],
    )


# =============== INTERACTIVE COMPONENTS ===============

def create_mood_button_premium(
    mood: str,
    on_click=None,
    selected: bool = False,
):
    """Premium mood selection button with glassmorphism"""
    mood_data = MOOD_CONFIG.get(mood, {})
    emoji = mood_data.get("emoji", "🎵")
    color = mood_data.get("color", PRIMARY_ACCENT)
    
    button_content = ft.Column(
        spacing=SPACING_XS,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Text(emoji, size=24),
            ft.Text(
                mood,
                size=FONT_SIZE_SMALL,
                weight=FONT_WEIGHT_SEMIBOLD,
                color=TEXT_PRIMARY,
            ),
        ],
    )
    
    return ft.Container(
        width=75,
        height=85,
        padding=SPACING_SM,
        border_radius=RADIUS_LARGE,
        bgcolor=GLASS_MEDIUM if not selected else f"{color}20",
        border=ft.border.all(
            2,
            color if selected else BORDER_COLOR,
        ),
        shadow=ft.BoxShadow(
            blur_radius=8 if selected else 4,
            color=f"{color}40" if selected else "#00000020",
            offset=ft.Offset(0, 2 if selected else 1),
        ),
        content=button_content,
        on_click=on_click,
        alignment=ft.Alignment(0, 0),
    )


def create_intensity_button_premium(
    intensity: str,
    on_click=None,
    selected: bool = False,
):
    """Premium intensity selection button"""
    intensity_data = INTENSITY_CONFIG.get(intensity, {})
    emoji = intensity_data.get("emoji", "🎵")
    color = intensity_data.get("color", PRIMARY_ACCENT)
    
    return ft.Container(
        width=75,
        height=75,
        padding=SPACING_SM,
        border_radius=RADIUS_LARGE,
        bgcolor=GLASS_MEDIUM if not selected else f"{color}20",
        border=ft.border.all(
            2,
            color if selected else BORDER_COLOR,
        ),
        shadow=ft.BoxShadow(
            blur_radius=8 if selected else 4,
            color=f"{color}40" if selected else "#00000020",
            offset=ft.Offset(0, 2 if selected else 1),
        ),
        content=ft.Column(
            spacing=SPACING_XS,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(emoji, size=20),
                ft.Text(
                    intensity,
                    size=FONT_SIZE_SMALL,
                    weight=FONT_WEIGHT_SEMIBOLD,
                    color=TEXT_PRIMARY,
                ),
            ],
        ),
        on_click=on_click,
        alignment=ft.Alignment(0, 0),
    )


# =============== CONTENT DISPLAY COMPONENTS ===============

def create_message_bubble_professional(
    sender: str,
    text: str,
    avatar_emoji: str = None,
):
    """Professional chat message bubble with glassmorphism"""
    is_user = sender == "user"
    
    # Determine styling based on sender
    bubble_bgcolor = GLASS_LIGHT if is_user else f"{PRIMARY_ACCENT}20"
    bubble_border = ft.border.all(1, PRIMARY_ACCENT if is_user else BORDER_COLOR)
    text_color = TEXT_PRIMARY
    alignment = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
    cross_alignment = ft.CrossAxisAlignment.END if is_user else ft.CrossAxisAlignment.START
    
    bubble = ft.Container(
        padding=ft.padding.symmetric(horizontal=SPACING_MD, vertical=SPACING_SM),
        border_radius=RADIUS_LARGE,
        bgcolor=bubble_bgcolor,
        border=bubble_border,
        shadow=ft.BoxShadow(
            blur_radius=4,
            color="#00000020",
            offset=ft.Offset(0, 1),
        ),
        content=ft.Column(
            spacing=SPACING_XS,
            controls=[
                ft.Text(
                    text,
                    color=text_color,
                    size=FONT_SIZE_BASE,
                    selectable=True,
                ),
            ],
        ),
        width=350,
    )
    
    return ft.Row(
        alignment=alignment,
        controls=[bubble],
    )


def create_song_card_premium(
    song: dict,
    on_try_again=None,
):
    """Premium song recommendation card with glassmorphism"""
    mood_color = PRIMARY_ACCENT
    
    song_title = ft.Text(
        song.get("name", "Unknown"),
        size=FONT_SIZE_XL,
        weight=FONT_WEIGHT_BOLD,
        color=TEXT_PRIMARY,
        max_lines=2,
    )
    
    song_artist = ft.Text(
        song.get("artist", "Unknown Artist"),
        size=FONT_SIZE_MD,
        color=TEXT_SECONDARY,
    )
    
    song_genre = ft.Container(
        padding=ft.padding.symmetric(horizontal=SPACING_SM, vertical=SPACING_XS),
        bgcolor=f"{mood_color}20",
        border_radius=RADIUS_MEDIUM,
        border=ft.border.all(1, mood_color),
        content=ft.Text(
            song.get("genre", "Unknown"),
            size=FONT_SIZE_SM,
            color=mood_color,
            weight=FONT_WEIGHT_MEDIUM,
        ),
    )
    
    reason = ft.Text(
        song.get("reason", "Perfect match for your mood"),
        size=FONT_SIZE_SM,
        color=TEXT_SECONDARY,
        italic=True,
    )
    
    buttons = ft.Row(
        spacing=SPACING_MD,
        controls=[
            create_gradient_button(
                "▶️  Play Now",
                width=150,
                height=42,
            ),
            ft.Container(
                width=150,
                height=42,
                border_radius=RADIUS_MEDIUM,
                bgcolor=GLASS_LIGHT,
                border=ft.border.all(1, PRIMARY_ACCENT),
                content=ft.TextButton(
                    content=ft.Text(
                        "🔄  Try Again",
                        color=PRIMARY_ACCENT,
                        weight=FONT_WEIGHT_SEMIBOLD,
                        size=FONT_SIZE_SM,
                    ),
                    on_click=on_try_again,
                ),
                alignment=ft.Alignment(0, 0),
            ),
        ],
    )
    
    return create_glassmorphic_container(
        ft.Column(
            spacing=SPACING_LG,
            controls=[
                ft.Column(
                    spacing=SPACING_MD,
                    controls=[
                        song_title,
                        song_artist,
                        song_genre,
                    ],
                ),
                ft.Divider(color=BORDER_COLOR, height=1),
                ft.Column(
                    spacing=SPACING_MD,
                    controls=[
                        reason,
                        buttons,
                    ],
                ),
            ],
        ),
        padding=SPACING_LG,
    )


def create_info_card_premium(
    title: str,
    content: str,
    icon: str = "ℹ️",
):
    """Premium information card"""
    return create_glassmorphic_container(
        ft.Column(
            spacing=SPACING_MD,
            controls=[
                ft.Row(
                    spacing=SPACING_MD,
                    controls=[
                        ft.Text(icon, size=FONT_SIZE_XL),
                        ft.Text(
                            title,
                            size=FONT_SIZE_LG,
                            weight=FONT_WEIGHT_SEMIBOLD,
                            color=TEXT_PRIMARY,
                        ),
                    ],
                ),
                ft.Text(
                    content,
                    size=FONT_SIZE_SM,
                    color=TEXT_SECONDARY,
                ),
            ],
        ),
        padding=SPACING_LG,
    )


# =============== DECORATIVE COMPONENTS ===============

def create_section_header_premium(
    title: str,
    icon: str = "",
):
    """Professional section header"""
    return ft.Column(
        spacing=SPACING_SM,
        controls=[
            ft.Row(
                spacing=SPACING_MD,
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    ft.Text(icon, size=FONT_SIZE_XL) if icon else None,
                    ft.Text(
                        title,
                        size=FONT_SIZE_XL,
                        weight=FONT_WEIGHT_BOLD,
                        color=TEXT_PRIMARY,
                    ),
                ],
            ),
            ft.Container(
                height=2,
                bgcolor=PRIMARY_ACCENT,
                border_radius=RADIUS_SMALL,
                width=40,
            ),
        ],
    )


def create_divider_premium(opacity: float = 0.3):
    """Professional divider"""
    return ft.Divider(
        color=f"{BORDER_COLOR}80",
        height=16,
    )


# =============== UTILITY FUNCTIONS ===============

def create_section_spacer(size: int = SPACING_LG):
    """Create vertical spacing"""
    return ft.Container(height=size)


def create_loading_indicator():
    """Professional loading indicator"""
    return ft.Container(
        content=ft.ProgressRing(
            width=50,
            height=50,
            stroke_width=3,
            color=PRIMARY_ACCENT,
        ),
        alignment=ft.Alignment(0, 0),
    )


def create_status_badge(text: str, status: str = "info"):
    """Status badge with color coding"""
    status_colors = {
        "success": SUCCESS,
        "error": ERROR,
        "warning": WARNING,
        "info": INFO,
    }
    color = status_colors.get(status, INFO)
    
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=SPACING_SM, vertical=SPACING_XS),
        bgcolor=f"{color}20",
        border_radius=RADIUS_MEDIUM,
        border=ft.border.all(1, color),
        content=ft.Text(
            text,
            size=FONT_SIZE_SM,
            color=color,
            weight=FONT_WEIGHT_MEDIUM,
        ),
    )
