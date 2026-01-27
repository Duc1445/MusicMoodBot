"""
Login screen for MusicMoodBot
"""

import flet as ft
from src.config.theme_professional import *
from src.components.ui_components_pro import *
from src.components.talking_animator import TalkingAnimator, get_talking_frame_path
from src.services.auth_service import auth_service


def create_login_screen(on_signup_click, on_login_submit):
    """Create login screen UI"""
    error_text = ft.Text("", size=FONT_SIZE_SM, color=ERROR)
    
    # Create input fields directly for value access
    email_field = ft.TextField(
        hint_text="user123",
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color=TEXT_MUTED, size=FONT_SIZE_BASE),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=FONT_SIZE_BASE),
        filled=False,
    )
    password_field = ft.TextField(
        hint_text="••••••",
        password=True,
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color=TEXT_MUTED, size=FONT_SIZE_BASE),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=FONT_SIZE_BASE),
        filled=False,
    )
    
    # Mascot image for animation
    mascot_img = ft.Image(
        src=get_talking_frame_path("eyes_open_mouth_closed"),
        width=70,
        height=70,
        fit="contain",
    )
    
    # Mascot animator (will be started after page mount)
    mascot_animator = TalkingAnimator(mascot_img)
    
    # Password visibility toggle
    show_password = {"value": False}
    
    def toggle_password_visibility(e):
        show_password["value"] = not show_password["value"]
        password_field.password = not password_field.password
        toggle_btn.content.value = "👁️" if show_password["value"] else "🔐"
        toggle_btn.update()
        password_field.update()
    
    toggle_btn = ft.Container(
        content=ft.Text("🔐", size=FONT_SIZE_LG),
    )
    toggle_btn.on_click = toggle_password_visibility

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

    # Create input containers with icons
    def create_input_field(icon: str, field: ft.TextField, toggle_btn=None) -> ft.Container:
        controls = [
            ft.Text(icon, size=FONT_SIZE_LG),
            ft.Container(expand=True, content=field),
        ]
        if toggle_btn:
            controls.append(toggle_btn)
        
        return ft.Container(
            height=44,
            border_radius=RADIUS_MEDIUM,
            bgcolor=BG_INPUT,
            border=ft.border.all(1, BORDER_COLOR),
            padding=ft.padding.only(left=SPACING_MD, right=SPACING_MD),
            content=ft.Row(
                spacing=SPACING_SM,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls,
            ),
        )

    return ft.Container(
        expand=True,
        content=ft.Stack(
            controls=[
                # Decoration mascot at top-right (đặt trước để ở phía dưới)
                ft.Container(
                    alignment=ft.Alignment(1, -0.7),
                    padding=ft.padding.only(right=20, top=20),
                    content=ft.Container(
                        width=90,
                        height=90,
                        border_radius=14,
                        bgcolor="transparent",
                        border=ft.border.all(0, "transparent"),
                        padding=6,
                        content=mascot_img,
                    ),
                ),
                # Main form container (đặt sau để ở phía trên)
                ft.Container(
                    bgcolor=BG_DARK,
                    expand=True,
                    padding=SPACING_XL,
                    content=ft.Column([
                        ft.Text("🎵 MusicMoodBot", size=FONT_SIZE_2XL, weight=FONT_WEIGHT_BOLD, color=PRIMARY_ACCENT),
                        ft.Text("Đăng Nhập", size=FONT_SIZE_XL, color=TEXT_PRIMARY),
                        ft.Container(height=SPACING_XL),
                        ft.Text("Email/Username", size=FONT_SIZE_SM, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                        create_input_field("👤", email_field),
                        ft.Container(height=SPACING_LG),
                        ft.Text("Mật khẩu", size=FONT_SIZE_SM, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                        create_input_field("🔐", password_field, toggle_btn),
                        ft.Container(height=SPACING_MD),
                        error_text,
                        ft.Container(height=SPACING_SM),
                        create_gradient_button("LOGIN →", width=300, height=44, on_click=handle_login),
                        ft.Container(height=SPACING_MD),
                        ft.Row([
                            ft.Text("Chưa có tài khoản? ", size=FONT_SIZE_SM, color=TEXT_SECONDARY),
                            ft.TextButton("Đăng ký", on_click=on_signup_click),
                        ]),
                        ft.Container(expand=True),
                        ft.Text("v2.0 | Professional Design", size=FONT_SIZE_SM, color=TEXT_MUTED),
                    ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
            ],
            expand=True,
        ),
    )
    
    # Start mascot animation after creation
    mascot_animator.start_animation("idle")
