"""
Message Bubbles Component
=========================
Bot and User message bubble UI components.
"""

import flet as ft
from datetime import datetime

from ...config.settings import settings


def create_bot_message(text: str, time_str: str = None) -> ft.Row:
    """
    Create bot message bubble (left side).
    
    Args:
        text: Message text
        time_str: Optional timestamp string
        
    Returns:
        ft.Row containing the message bubble
    """
    if not time_str:
        time_str = datetime.now().strftime("%H:%M %p")
    
    return ft.Row([
        # Bot avatar
        ft.Container(
            width=36,
            height=36,
            border_radius=18,
            bgcolor=settings.TEAL_PRIMARY,
            alignment=ft.Alignment(0, 0),
            content=ft.Text("🤖", size=18),
        ),
        ft.Container(width=8),
        ft.Column([
            ft.Row([
                ft.Text("MusicMoodBot", size=12, weight=ft.FontWeight.W_600, color=settings.TEXT_PRIMARY),
                ft.Text(f"  {time_str}", size=11, color=settings.TEXT_MUTED),
            ], spacing=0),
            ft.Container(height=4),
            ft.Container(
                padding=ft.padding.all(14),
                border_radius=12,
                bgcolor=settings.WHITE,
                border=ft.border.all(1, settings.BORDER_COLOR),
                content=ft.Text(text, size=14, color=settings.TEXT_PRIMARY),
            ),
        ], spacing=0),
    ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)


def create_user_message(text: str) -> ft.Row:
    """
    Create user message bubble (right side).
    
    Args:
        text: Message text
        
    Returns:
        ft.Row containing the message bubble
    """
    return ft.Row([
        ft.Container(expand=True),
        ft.Column([
            ft.Text("You", size=12, color=settings.TEXT_MUTED, text_align=ft.TextAlign.RIGHT),
            ft.Container(height=4),
            ft.Container(
                padding=ft.padding.all(14),
                border_radius=12,
                bgcolor=settings.TEAL_PRIMARY,
                content=ft.Text(text, size=14, color=settings.WHITE),
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=0),
        ft.Container(width=8),
        # User avatar
        ft.Container(
            width=36,
            height=36,
            border_radius=18,
            bgcolor="#E0E0E0",
            alignment=ft.Alignment(0, 0),
            content=ft.Text("👤", size=18),
        ),
    ], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.START)
