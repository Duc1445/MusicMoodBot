"""
Typing Indicator Component
==========================
Bot typing indicator UI component.
"""

import flet as ft

from ...config.settings import settings
from ...utils.helpers import _make_progress


def create_typing_indicator() -> ft.Row:
    """
    Create bot typing indicator.
    
    Returns:
        ft.Row containing typing indicator UI
    """
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
        ft.Container(
            padding=ft.padding.all(12),
            border_radius=12,
            bgcolor=settings.WHITE,
            border=ft.border.all(1, settings.BORDER_COLOR),
            content=ft.Row([
                _make_progress(),
                ft.Text(" Đang nhập...", size=13, color=settings.TEXT_MUTED),
            ]),
        ),
    ])
