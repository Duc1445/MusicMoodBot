"""
Login screen for MusicMoodBot - Figma Design 1:1
"""

import flet as ft
from ..config.theme_professional import *
from ..services.auth_service import auth_service
from ..utils.state_manager import app_state


def create_login_screen(on_signup_click, on_login_submit):
    """Create login screen matching Figma design exactly"""
    error_text = ft.Text("", size=12, color="#FF4444")

    # Input fields
    email_field = ft.TextField(
        hint_text="user123",
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color="#999999", size=14),
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )
    password_field = ft.TextField(
        hint_text="••••••••",
        password=True,
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color="#999999", size=14),
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )

    def handle_login(e):
        success, message = auth_service.login(
            email_field.value,
            password_field.value
        )
        if success:
            error_text.value = ""
            on_login_submit()
        else:
            error_text.value = message
            error_text.update()

    # Password visibility toggle
    password_visible = {"value": False}
    password_icon = ft.Text("🔒", size=16, color="#666666")
    
    def toggle_password(e):
        password_visible["value"] = not password_visible["value"]
        password_field.password = not password_visible["value"]
        password_icon.value = "👁" if password_visible["value"] else "🔒"
        password_field.update()
        password_icon.update()

    # Input field with icon (Figma style - rectangular with border)
    def create_figma_input(field: ft.TextField, icon: str, is_password: bool = False) -> ft.Container:
        if is_password:
            return ft.Container(
                height=44,
                border_radius=8,
                bgcolor="#FFFFFF",
                border=ft.border.all(1.5, "#1A1A1A"),
                padding=ft.padding.only(left=16, right=12),
                content=ft.Row([
                    ft.Container(expand=True, content=field),
                    ft.Container(
                        content=password_icon,
                        on_click=toggle_password,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            )
        return ft.Container(
            height=44,
            border_radius=8,
            bgcolor="#FFFFFF",
            border=ft.border.all(1.5, "#1A1A1A"),
            padding=ft.padding.only(left=16, right=12),
            content=ft.Row([
                ft.Container(expand=True, content=field),
                ft.Text(icon, size=16, color="#666666"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

    # Window frame container (Figma design has window-like frame)
    window_frame = ft.Container(
        width=520,
        bgcolor="#FFFFFF",
        border_radius=12,
        border=ft.border.all(2, "#1A1A1A"),
        shadow=ft.BoxShadow(blur_radius=20, color="#00000015", offset=ft.Offset(0, 8)),
        content=ft.Column([
            # Title bar (like desktop app)
            ft.Container(
                height=40,
                bgcolor="#F5F5F5",
                border=ft.border.only(bottom=ft.BorderSide(1.5, "#1A1A1A")),
                padding=ft.padding.symmetric(horizontal=16),
                content=ft.Row([
                    # Window controls (3 dots)
                    ft.Row([
                        ft.Container(width=12, height=12, border_radius=6, border=ft.border.all(1.5, "#1A1A1A")),
                        ft.Container(width=12, height=12, border_radius=6, border=ft.border.all(1.5, "#1A1A1A")),
                        ft.Container(width=12, height=12, border_radius=6, border=ft.border.all(1.5, "#1A1A1A")),
                    ], spacing=6),
                    # Title
                    ft.Row([
                        ft.Text("🏠", size=14),
                        ft.Text(" MusicMood Bot Login", size=14, weight=ft.FontWeight.W_600, color="#1A1A1A"),
                    ], spacing=4),
                    # Close button
                    ft.Text("✕", size=14, color="#666666"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ),
            # Content area - split layout
            ft.Container(
                expand=True,
                content=ft.Row([
                    # Left side - Music Logo
                    ft.Container(
                        width=200,
                        bgcolor="#E8F4F5",
                        border=ft.border.only(right=ft.BorderSide(1.5, "#1A1A1A")),
                        content=ft.Column([
                            ft.Container(expand=True),
                            # Large music note in circle
                            ft.Container(
                                width=140,
                                height=140,
                                border_radius=70,
                                border=ft.border.all(3, "#1A1A1A"),
                                bgcolor="#FFFFFF",
                                alignment=ft.Alignment(0,0),
                                content=ft.Text("♪", size=72, color="#1A1A1A", weight=ft.FontWeight.W_400),
                            ),
                            ft.Container(expand=True),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ),
                    # Right side - Login Form
                    ft.Container(
                        expand=True,
                        padding=ft.padding.all(32),
                        content=ft.Column([
                            ft.Container(height=8),
                            # Email/Username field
                            ft.Text("Email/Username", size=14, weight=ft.FontWeight.W_600, color="#1A1A1A"),
                            ft.Container(height=8),
                            create_figma_input(email_field, "👤"),
                            
                            ft.Container(height=20),
                            
                            # Password field
                            ft.Text("Password", size=14, weight=ft.FontWeight.W_600, color="#1A1A1A"),
                            ft.Container(height=8),
                            create_figma_input(password_field, "🔒", is_password=True),
                            
                            ft.Container(height=8),
                            error_text,
                            
                            ft.Container(height=24),
                            
                            # Login button (dark rounded)
                            ft.Container(
                                height=48,
                                border_radius=24,
                                bgcolor="#1A1A1A",
                                alignment=ft.Alignment(0,0),
                                on_click=handle_login,
                                content=ft.Row([
                                    ft.Text("LOGIN", size=14, weight=ft.FontWeight.W_600, color="#FFFFFF"),
                                    ft.Text(" →", size=16, color="#FFFFFF"),
                                ], alignment=ft.MainAxisAlignment.CENTER),
                            ),
                            
                            ft.Container(height=20),
                            
                            # Sign up link
                            ft.Row([
                                ft.Text("Don't have an account? ", size=13, color="#666666"),
                                ft.TextButton(
                                    "Sign up",
                                    on_click=on_signup_click,
                                    style=ft.ButtonStyle(
                                        color="#1A1A1A",
                                        padding=0,
                                    ),
                                ),
                            ], alignment=ft.MainAxisAlignment.CENTER),
                        ], spacing=0),
                    ),
                ], spacing=0),
            ),
            # Footer bar
            ft.Container(
                height=32,
                bgcolor="#F5F5F5",
                border=ft.border.only(top=ft.BorderSide(1.5, "#1A1A1A")),
                padding=ft.padding.symmetric(horizontal=16),
                content=ft.Row([
                    ft.Text("v1.0.0", size=11, color="#888888"),
                    ft.Row([
                        ft.Container(width=8, height=8, border_radius=4, bgcolor="#22C55E"),
                        ft.Text(" Online", size=11, color="#888888"),
                    ], spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ),
        ], spacing=0),
    )

    # Decorative elements
    # Headphones icon (top-left)
    headphones_icon = ft.Container(
        alignment=ft.Alignment(-0.85, -0.75),
        content=ft.Text("🎧", size=80, color="#E0E0E0", opacity=0.6),
    )
    
    # Music note with playlist icon (bottom-right)
    music_playlist_icon = ft.Container(
        alignment=ft.Alignment(0.85, 0.75),
        content=ft.Column([
            ft.Text("♪", size=50, color="#D0D0D0"),
            ft.Container(
                width=40,
                content=ft.Column([
                    ft.Container(height=3, bgcolor="#D0D0D0", border_radius=2),
                    ft.Container(height=3, bgcolor="#D0D0D0", border_radius=2),
                    ft.Container(height=3, bgcolor="#D0D0D0", border_radius=2),
                ], spacing=4),
            ),
        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
    )
    
    # Main background
    main_bg = ft.Container(
        expand=True,
        bgcolor="#FAF9F6",
    )

    # Build main background with stack
    main_bg.content = ft.Stack([
        headphones_icon,
        music_playlist_icon,
        # Center the window frame
        ft.Container(
            expand=True,
            alignment=ft.Alignment(0,0),
            content=window_frame,
        ),
    ])

    return main_bg
