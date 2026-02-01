"""
Mood & Intensity Chips Components
==================================
Chip selection UI components for mood and intensity.
"""

import flet as ft
from typing import Callable, Optional

from ...config.settings import settings, MOOD_EMOJI, INTENSITY_EMOJI


def create_mood_chip(
    mood_name: str, 
    emoji: str, 
    on_click: Optional[Callable] = None
) -> ft.Container:
    """
    Create mood selection chip (outlined, compact).
    
    Args:
        mood_name: Mood name (e.g., "Vui", "Buồn")
        emoji: Emoji for the mood
        on_click: Callback function when chip is clicked
        
    Returns:
        ft.Container with chip UI
    """
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=16,
        bgcolor=settings.WHITE,
        border=ft.border.all(1, settings.TEXT_PRIMARY),
        on_click=on_click,
        content=ft.Row([
            ft.Text(emoji, size=12),
            ft.Text(f" {mood_name}", size=11, weight=ft.FontWeight.W_500, color=settings.TEXT_PRIMARY),
        ], spacing=0),
    )


def create_intensity_chip(
    intensity_name: str, 
    emoji: str,
    on_click: Optional[Callable] = None
) -> ft.Container:
    """
    Create intensity selection chip (compact).
    
    Args:
        intensity_name: Intensity name (e.g., "Nhẹ", "Vừa")
        emoji: Emoji for the intensity
        on_click: Callback function when chip is clicked
        
    Returns:
        ft.Container with chip UI
    """
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=16,
        bgcolor=settings.WHITE,
        border=ft.border.all(1, settings.TEAL_PRIMARY),
        on_click=on_click,
        content=ft.Row([
            ft.Text(emoji, size=12),
            ft.Text(f" {intensity_name}", size=11, weight=ft.FontWeight.W_500, color=settings.TEAL_DARK),
        ], spacing=0),
    )


def create_mood_chips_row(
    moods: list = None,
    on_mood_click: Optional[Callable[[str], None]] = None
) -> ft.Row:
    """
    Create row of mood chips.
    
    Args:
        moods: List of mood names (defaults to standard moods)
        on_mood_click: Callback receiving mood name when clicked
        
    Returns:
        ft.Row containing all mood chips
    """
    if moods is None:
        moods = ["Vui", "Buồn", "Năng động", "Thư giãn", "Tập trung"]
    
    chips = []
    for mood in moods:
        emoji = MOOD_EMOJI.get(mood, "🎵")
        
        def make_click_handler(m):
            def handler(e):
                if on_mood_click:
                    on_mood_click(m)
            return handler
        
        chips.append(create_mood_chip(mood, emoji, on_click=make_click_handler(mood)))
    
    return ft.Row(chips, spacing=6)


def create_intensity_chips_row(
    intensities: list = None,
    on_intensity_click: Optional[Callable[[str], None]] = None
) -> ft.Row:
    """
    Create row of intensity chips.
    
    Args:
        intensities: List of intensity names (defaults to standard intensities)
        on_intensity_click: Callback receiving intensity name when clicked
        
    Returns:
        ft.Row containing all intensity chips
    """
    if intensities is None:
        intensities = ["Nhẹ", "Vừa", "Mạnh"]
    
    chips = []
    for intensity in intensities:
        emoji = INTENSITY_EMOJI.get(intensity, "✨")
        
        def make_click_handler(i):
            def handler(e):
                if on_intensity_click:
                    on_intensity_click(i)
            return handler
        
        chips.append(create_intensity_chip(intensity, emoji, on_click=make_click_handler(intensity)))
    
    return ft.Row(chips, spacing=6)
