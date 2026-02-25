"""
Signup screen for MusicMoodBot - Figma Design 1:1
"""

import flet as ft
from src.config.theme_professional import *
from src.services.auth_service import auth_service


def create_signup_screen(on_login_click, on_signup_submit):
    """Create signup screen matching Figma design exactly"""
    error_text = ft.Text("", size=12, color="#FF4444")

    # Input fields
    name_field = ft.TextField(
        hint_text="John Doe",
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color="#999999", size=14),
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )
    email_field = ft.TextField(
        hint_text="user@example.com",
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color="#999999", size=14),
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )
    password_field = ft.TextField(
        hint_text="********",
        password=True,
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color="#999999", size=14),
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )
    confirm_password_field = ft.TextField(
        hint_text="********",
        password=True,
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color="#999999", size=14),
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )

    def handle_signup(e):
        success, message = auth_service.signup(
            name_field.value,
            email_field.value,
            password_field.value,
            confirm_password_field.value
        )
        if success:
            error_text.value = ""
            on_signup_submit()
        else:
            error_text.value = message
            error_text.update()

    # Input field (Figma style - simple with underline/border)
    def create_figma_input(label: str, field: ft.TextField) -> ft.Container:
        return ft.Column([
            ft.Text(label, size=14, weight=ft.FontWeight.W_600, color="#1A1A1A"),
            ft.Container(height=8),
            ft.Container(
                height=44,
                border_radius=8,
                bgcolor="#FFFFFF",
                border=ft.border.all(1.5, "#1A1A1A"),
                padding=ft.padding.only(left=16, right=16),
                content=field,
            ),
        ], spacing=0)

    # Phone/tablet style frame (Figma signup is mobile-like)
    phone_frame = ft.Container(
        width=380,
        height=640,
        bgcolor="#FFFFFF",
        border_radius=20,
        border=ft.border.all(2, "#1A1A1A"),
        shadow=ft.BoxShadow(blur_radius=30, color="#00000020", offset=ft.Offset(5, 10)),
        content=ft.Column([
            # Header with title only
            ft.Container(
                height=50,
                padding=ft.padding.symmetric(horizontal=16),
                content=ft.Row([
                    # Empty space for balance
                    ft.Container(width=40),
                    # Title
                    ft.Text("MusicMood Bot Sign Up", size=16, weight=ft.FontWeight.W_700, color="#1A1A1A",
                           font_family="Comic Sans MS"),
                    # Dots indicator
                    ft.Row([
                        ft.Container(width=10, height=10, border_radius=5, border=ft.border.all(1.5, "#1A1A1A")),
                        ft.Container(width=10, height=10, border_radius=5, border=ft.border.all(1.5, "#1A1A1A")),
                        ft.Container(width=10, height=10, border_radius=5, bgcolor="#1A1A1A"),
                    ], spacing=4),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ),
            
            # Robot mascot
            ft.Container(
                height=80,
                alignment=ft.Alignment(0,0),
                content=ft.Container(
                    width=60,
                    height=60,
                    border_radius=8,
                    border=ft.border.all(2, "#1A1A1A"),
                    bgcolor="#FFFFFF",
                    alignment=ft.Alignment(0,0),
                    content=ft.Text("🤖", size=32),
                ),
            ),
            
            # Form
            ft.Container(
                expand=True,
                padding=ft.padding.symmetric(horizontal=32),
                content=ft.Column([
                    create_figma_input("Full Name", name_field),
                    ft.Container(height=16),
                    create_figma_input("Email", email_field),
                    ft.Container(height=16),
                    create_figma_input("Password", password_field),
                    ft.Container(height=16),
                    create_figma_input("Confirm Password", confirm_password_field),
                    ft.Container(height=8),
                    error_text,
                    ft.Container(height=24),
                    
                    # Sign up button (outlined style)
                    ft.Container(
                        height=50,
                        border_radius=25,
                        bgcolor="#FFFFFF",
                        border=ft.border.all(2, "#1A1A1A"),
                        alignment=ft.Alignment(0,0),
                        on_click=handle_signup,
                        content=ft.Text("SIGN UP", size=16, weight=ft.FontWeight.W_700, color="#1A1A1A",
                                       font_family="Comic Sans MS"),
                    ),
                    
                    ft.Container(height=16),
                    
                    # Login link
                    ft.Row([
                        ft.TextButton(
                            content=ft.Text("Already Have Account? Login", size=13, color="#1A1A1A", weight=ft.FontWeight.W_500),
                            on_click=on_login_click,
                            style=ft.ButtonStyle(padding=0),
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], spacing=0),
            ),
        ], spacing=0),
    )

    # Decorative X mark (bottom-left, as in Figma)
    x_decoration = ft.Container(
        alignment=ft.Alignment(-0.6, 0.7),
        content=ft.Text("✕", size=60, color="#D0D0D0", opacity=0.5),
    )
    
    # Settings icon (bottom-right)
    settings_icon = ft.Container(
        alignment=ft.Alignment(0.95, 0.92),
        content=ft.Container(
            width=44,
            height=44,
            border_radius=22,
            bgcolor="#FFFFFF",
            border=ft.border.all(2, "#1A1A1A"),
            alignment=ft.Alignment(0,0),
            content=ft.Text("⚙️", size=20),
        ),
    )

    # Main background
    return ft.Container(
        expand=True,
        bgcolor="#FAF9F6",
        content=ft.Stack([
            x_decoration,
            settings_icon,
            # Center the phone frame
            ft.Container(
                expand=True,
                alignment=ft.Alignment(0,0),
                content=phone_frame,
            ),
        ]),
    )
