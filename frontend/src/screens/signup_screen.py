"""
Signup screen for MusicMoodBot - Professional UI
"""

import flet as ft
from src.config.theme_professional import *
from src.components.ui_components_pro import *
from src.components.talking_animator import TalkingAnimator, get_talking_frame_path
from src.services.auth_service import auth_service


def create_signup_screen(on_login_click, on_signup_submit):
    """Create professional signup screen"""
    # Mascot image for animation
    mascot_img = ft.Image(
        src=get_talking_frame_path("eyes_open_mouth_closed"),
        width=70,
        height=70,
        fit="contain",
    )
    
    # Mascot animator (will be started after creation)
    mascot_animator = TalkingAnimator(mascot_img)
    
    # Create text fields directly for value access
    name_field = ft.TextField(
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_text="Nguyễn Văn A",
        hint_style=ft.TextStyle(color=TEXT_MUTED, size=FONT_SIZE_BASE),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=FONT_SIZE_BASE),
        filled=False,
    )
    email_field = ft.TextField(
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_text="user@example.com",
        hint_style=ft.TextStyle(color=TEXT_MUTED, size=FONT_SIZE_BASE),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=FONT_SIZE_BASE),
        filled=False,
    )
    password_field = ft.TextField(
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_text="Mật khẩu",
        hint_style=ft.TextStyle(color=TEXT_MUTED, size=FONT_SIZE_BASE),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=FONT_SIZE_BASE),
        password=True,
        filled=False,
    )
    confirm_field = ft.TextField(
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_text="Nhập lại mật khẩu",
        hint_style=ft.TextStyle(color=TEXT_MUTED, size=FONT_SIZE_BASE),
        text_style=ft.TextStyle(color=TEXT_PRIMARY, size=FONT_SIZE_BASE),
        password=True,
        filled=False,
    )
    error_text = ft.Text("", size=FONT_SIZE_SM, color=ERROR)
    
    # Password visibility toggles
    show_password = {"value": False}
    show_confirm = {"value": False}
    
    def toggle_password_visibility(e):
        show_password["value"] = not show_password["value"]
        password_field.password = not password_field.password
        toggle_password_btn.content.value = "👁️" if show_password["value"] else "🔐"
        toggle_password_btn.update()
        password_field.update()
    
    def toggle_confirm_visibility(e):
        show_confirm["value"] = not show_confirm["value"]
        confirm_field.password = not confirm_field.password
        toggle_confirm_btn.content.value = "👁️" if show_confirm["value"] else "🔐"
        toggle_confirm_btn.update()
        confirm_field.update()
    
    toggle_password_btn = ft.Container(
        content=ft.Text("🔐", size=FONT_SIZE_LG),
    )
    toggle_password_btn.on_click = toggle_password_visibility
    
    toggle_confirm_btn = ft.Container(
        content=ft.Text("🔐", size=FONT_SIZE_LG),
    )
    toggle_confirm_btn.on_click = toggle_confirm_visibility

    def handle_signup(e):
        success, message = auth_service.signup(
            name_field.value,
            email_field.value,
            password_field.value,
            confirm_field.value
        )
        
        if success:
            error_text.value = ""
            name_field.value = ""
            email_field.value = ""
            password_field.value = ""
            confirm_field.value = ""
            on_signup_submit()
        else:
            error_text.value = message
            error_text.update()

    # Create input containers with icons and fields
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
                    expand=True,
                    bgcolor=BG_DARK,
                    padding=SPACING_LG,
                    content=ft.Column([
                        ft.Text("MusicMoodBot", size=FONT_SIZE_XL, weight=FONT_WEIGHT_BOLD, color=PRIMARY_ACCENT),
                        ft.Text("Đăng Ký Tài Khoản", size=FONT_SIZE_LG, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                        ft.Container(height=SPACING_LG),
                        ft.Container(
                            expand=True,
                            content=ft.Column([
                                create_glassmorphic_container(
                                    ft.Column([
                                        ft.Text("Họ và tên", size=FONT_SIZE_SM, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                                        create_input_field("👤", name_field),
                                        ft.Container(height=SPACING_MD),
                                        ft.Text("Email", size=FONT_SIZE_SM, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                                        create_input_field("✉️", email_field),
                                        ft.Container(height=SPACING_MD),
                                        ft.Text("Mật khẩu", size=FONT_SIZE_SM, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                                        create_input_field("🔐", password_field, toggle_password_btn),
                                        ft.Container(height=SPACING_MD),
                                        ft.Text("Nhập lại mật khẩu", size=FONT_SIZE_SM, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                                        create_input_field("🔐", confirm_field, toggle_confirm_btn),
                                        ft.Container(height=SPACING_MD),
                                        error_text,
                                        ft.Container(height=SPACING_SM),
                                        create_gradient_button("ĐĂNG KÝ", on_click=handle_signup),
                                    ], spacing=SPACING_SM),
                                    padding=SPACING_LG,
                                ),
                                ft.Container(height=SPACING_LG),
                                ft.Row([
                                    ft.Text("Đã có tài khoản?", size=FONT_SIZE_SM, color=TEXT_SECONDARY),
                                    ft.TextButton("Đăng nhập", on_click=on_login_click),
                                ], alignment=ft.MainAxisAlignment.CENTER),
                            ],
                            spacing=SPACING_MD,
                            scroll=ft.ScrollMode.AUTO),
                        ),
                    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ),
            ],
            expand=True,
        ),
    )
    
    # Start mascot animation after creation
    mascot_animator.start_animation("idle")
