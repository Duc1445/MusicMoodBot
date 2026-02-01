"""
Profile screen for MusicMoodBot - Figma Design 1:1
"""

import flet as ft
from ..config.theme_professional import *
from ..utils.state_manager import app_state


# Figma color scheme - Profile uses warm coral/terra-cotta
CORAL_PRIMARY = "#E57373"  # Terra-cotta/Coral for profile
CORAL_LIGHT = "#FFCDD2"
CORAL_DARK = "#C62828"
SIDEBAR_BG = "#FFF5F5"  # Warm white for profile sidebar


def create_profile_screen(on_chat_click, on_logout_click, on_history_click):
    """Create profile screen matching Figma design exactly"""
    
    user_info = app_state.user_info or {}
    
    # Input fields
    name_field = ft.TextField(
        value=user_info.get("name", "Nguyễn Văn A"),
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )
    email_field = ft.TextField(
        value=user_info.get("email", "user@example.com"),
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )
    genre_field = ft.TextField(
        value="Pop, Ballad, Indie",
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )

    def create_form_field(label: str, icon: str, field: ft.TextField):
        """Create form field with label and icon"""
        return ft.Column([
            ft.Text(label, size=11, color="#888888", weight=ft.FontWeight.W_600),
            ft.Container(height=6),
            ft.Container(
                height=50,
                border_radius=12,
                bgcolor="#F8F8F8",
                border=ft.border.all(1, "#E8E8E8"),
                padding=ft.padding.only(left=16, right=16),
                content=ft.Row([
                    ft.Text(icon, size=16, color=CORAL_PRIMARY),
                    ft.Container(width=12),
                    field,
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ),
        ], spacing=0)

    # Sidebar menu item
    def create_menu_item(icon: str, label: str, is_active: bool = False, on_click=None):
        return ft.Container(
            height=44,
            border_radius=8,
            bgcolor=CORAL_LIGHT if is_active else "transparent",
            padding=ft.padding.only(left=12),
            on_click=on_click,
            content=ft.Row([
                ft.Text(icon, size=16, color=CORAL_PRIMARY if is_active else "#666666"),
                ft.Container(width=8),
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, 
                       color=CORAL_PRIMARY if is_active else "#1A1A1A"),
            ], alignment=ft.MainAxisAlignment.START),
        )

    # Main layout
    return ft.Container(
        expand=True,
        bgcolor="#FFFFFF",
        content=ft.Stack([
            # Background vinyl decoration (bottom-right)
            ft.Container(
                alignment=ft.Alignment(0.9, 0.8),
                content=ft.Container(
                    width=250,
                    height=250,
                    border_radius=125,
                    bgcolor=CORAL_LIGHT,
                    opacity=0.3,
                    content=ft.Stack([
                        # Outer ring
                        ft.Container(
                            width=250,
                            height=250,
                            border_radius=125,
                            border=ft.border.all(20, CORAL_LIGHT),
                        ),
                        # Inner circle
                        ft.Container(
                            width=80,
                            height=80,
                            border_radius=40,
                            bgcolor=CORAL_PRIMARY,
                            opacity=0.5,
                            alignment=ft.Alignment(0,0),
                        ),
                    ]),
                ),
            ),
            # Main content
            ft.Row([
                # Sidebar
                ft.Container(
                    width=180,
                    bgcolor=SIDEBAR_BG,
                    border=ft.border.only(right=ft.BorderSide(1, "#F0E0E0")),
                    padding=ft.padding.all(16),
                    content=ft.Column([
                        # Logo
                        ft.Row([
                            ft.Container(
                                width=32,
                                height=32,
                                border_radius=16,
                                bgcolor=CORAL_PRIMARY,
                                alignment=ft.Alignment(0,0),
                                content=ft.Text("♪", size=16, color="#FFFFFF"),
                            ),
                            ft.Container(width=8),
                            ft.Column([
                                ft.Text("MusicMood", size=14, weight=ft.FontWeight.W_700, color="#1A1A1A"),
                                ft.Text("BOT", size=10, color="#888888"),
                            ], spacing=0),
                        ]),
                        ft.Container(height=24),
                        # Menu items
                        create_menu_item("💬", "Chat", on_click=lambda e: on_chat_click()),
                        ft.Container(height=4),
                        create_menu_item("🕐", "Lịch sử", on_click=lambda e: on_history_click()),
                        ft.Container(height=4),
                        create_menu_item("👤", "Hồ sơ", is_active=True),
                        ft.Container(expand=True),
                        # Now playing
                        ft.Container(
                            padding=ft.padding.all(12),
                            border_radius=12,
                            bgcolor="#FFFFFF",
                            border=ft.border.all(1, "#F0E0E0"),
                            content=ft.Column([
                                ft.Text("Đang nghe gì?", size=11, color="#888888"),
                                ft.Row([
                                    ft.Container(width=8, height=8, border_radius=4, bgcolor="#22C55E"),
                                    ft.Text(" Jazz for Rainy Days", size=12, color="#1A1A1A", 
                                           weight=ft.FontWeight.W_500),
                                ], spacing=0),
                            ], spacing=4),
                        ),
                    ]),
                ),
                # Main content
                ft.Container(
                    expand=True,
                    bgcolor="#FFFFFF",
                    padding=ft.padding.all(48),
                    content=ft.Column([
                        # Title
                        ft.Text("Hồ sơ cá nhân", size=36, weight=ft.FontWeight.W_800, color="#1A1A1A"),
                        ft.Container(height=8),
                        ft.Text("Quản lý thông tin và sở thích âm nhạc của bạn.", size=14, color="#666666"),
                        ft.Container(height=40),
                        # Content row
                        ft.Row([
                            # Avatar section
                            ft.Column([
                                ft.Container(
                                    width=160,
                                    height=160,
                                    border_radius=80,
                                    bgcolor="#E8F5E9",
                                    border=ft.border.all(4, "#FFFFFF"),
                                    shadow=ft.BoxShadow(blur_radius=20, color="#00000020"),
                                    alignment=ft.Alignment(0,0),
                                    content=ft.Text("👤", size=80),
                                ),
                                ft.Container(height=12),
                                # Edit button
                                ft.Container(
                                    width=36,
                                    height=36,
                                    border_radius=18,
                                    bgcolor=CORAL_PRIMARY,
                                    alignment=ft.Alignment(0,0),
                                    content=ft.Text("✏️", size=16),
                                ),
                                ft.Container(height=8),
                                ft.Text("Thay đổi ảnh đại diện", size=12, color=CORAL_PRIMARY),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Container(width=60),
                            # Form section
                            ft.Container(
                                width=400,
                                padding=ft.padding.all(32),
                                border_radius=20,
                                border=ft.border.all(1, "#F0E0E0"),
                                content=ft.Column([
                                    create_form_field("HỌ VÀ TÊN", "👤", name_field),
                                    ft.Container(height=20),
                                    create_form_field("EMAIL", "✉️", email_field),
                                    ft.Container(height=20),
                                    create_form_field("THỂ LOẠI NHẠC YÊU THÍCH", "♪", genre_field),
                                    ft.Container(height=12),
                                    ft.Text("Chúng tôi sẽ gợi ý bài hát dựa trên sở thích này.", 
                                           size=12, color="#AAAAAA", italic=True),
                                    ft.Container(height=24),
                                    # Action buttons
                                    ft.Row([
                                        # Logout button
                                        ft.Container(
                                            width=140,
                                            height=48,
                                            border_radius=12,
                                            bgcolor="#FFFFFF",
                                            border=ft.border.all(1.5, "#E0E0E0"),
                                            alignment=ft.Alignment(0,0),
                                            on_click=lambda e: on_logout_click(),
                                            content=ft.Row([
                                                ft.Text("↪", size=16, color="#666666"),
                                                ft.Text(" Đăng xuất", size=14, color="#666666"),
                                            ], alignment=ft.MainAxisAlignment.CENTER),
                                        ),
                                        ft.Container(width=16),
                                        # Update button
                                        ft.Container(
                                            width=160,
                                            height=48,
                                            border_radius=12,
                                            bgcolor=CORAL_PRIMARY,
                                            alignment=ft.Alignment(0,0),
                                            content=ft.Row([
                                                ft.Text("💾", size=16, color="#FFFFFF"),
                                                ft.Text(" Cập nhật\nthông tin", size=12, 
                                                       color="#FFFFFF", text_align=ft.TextAlign.CENTER),
                                            ], alignment=ft.MainAxisAlignment.CENTER),
                                        ),
                                    ]),
                                ]),
                            ),
                        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START),
                    ]),
                ),
            ], spacing=0),
        ]),
    )
