"""
Song Card Component
===================
Song recommendation card UI component.
"""

import flet as ft

from ...config.settings import settings


def create_song_card(song: dict) -> ft.Container:
    """
    Create song recommendation card (Figma style).
    
    Args:
        song: Song data dictionary with keys:
            - song_name/name: Song title
            - artist: Artist name
            - reason: Recommendation reason
            
    Returns:
        ft.Container with song card UI
    """
    song_name = song.get("song_name", song.get("name", "Bài hát"))
    artist = song.get("artist", "Unknown")
    reason = song.get("reason", "Phù hợp mood của bạn")
    
    return ft.Container(
        margin=ft.margin.only(left=44),
        padding=ft.padding.all(16),
        border_radius=12,
        bgcolor=settings.WHITE,
        border=ft.border.all(1, settings.BORDER_COLOR),
        content=ft.Row([
            # Song icon
            ft.Container(
                width=50,
                height=50,
                border_radius=8,
                bgcolor="#F0F0F0",
                alignment=ft.Alignment(0, 0),
                content=ft.Text("♪", size=24, color=settings.TEAL_PRIMARY),
            ),
            ft.Container(width=12),
            # Song info
            ft.Column([
                ft.Text(song_name, size=15, weight=ft.FontWeight.W_600, color=settings.TEXT_PRIMARY),
                ft.Text(f"Nghệ sĩ {artist}", size=13, color=settings.TEXT_SECONDARY),
                ft.Row([
                    ft.Text("🎵", size=12),
                    ft.Text(f" {reason}", size=12, color=settings.TEXT_MUTED),
                ], spacing=0),
            ], spacing=4, expand=True),
            # Play button
            ft.Container(
                width=44,
                height=44,
                border_radius=22,
                bgcolor=settings.TEAL_PRIMARY,
                alignment=ft.Alignment(0, 0),
                content=ft.Text("▶", size=18, color=settings.WHITE),
            ),
        ]),
    )
