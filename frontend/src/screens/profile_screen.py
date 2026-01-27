"""
Profile screen for MusicMoodBot - Professional UI
"""

import flet as ft
from src.config.theme_professional import *
from src.components.ui_components_pro import *
from src.services.auth_service import auth_service
from src.utils.state_manager import app_state


def create_profile_screen(on_chat_click, on_logout_click, on_history_click):
    """Create professional profile screen"""

    def handle_logout(e):
        auth_service.logout()
        on_logout_click()

    # Create profile info section
    def build_profile_info():
        return create_glassmorphic_container(
            ft.Column([
                ft.Row([
                    ft.Text("👤 Họ và tên", size=FONT_SIZE_SM, color=TEXT_SECONDARY, weight=FONT_WEIGHT_MEDIUM),
                ]),
                ft.Text(
                    app_state.user_info.get("name") or "Người dùng",
                    size=FONT_SIZE_LG,
                    color=TEXT_PRIMARY,
                    weight=FONT_WEIGHT_SEMIBOLD
                ),
                ft.Container(height=SPACING_LG),
                ft.Row([
                    ft.Text("📧 Email", size=FONT_SIZE_SM, color=TEXT_SECONDARY, weight=FONT_WEIGHT_MEDIUM),
                ]),
                ft.Text(
                    app_state.user_info.get("email") or "user@example.com",
                    size=FONT_SIZE_MD,
                    color=TEXT_PRIMARY,
                ),
                ft.Container(height=SPACING_LG),
                ft.Row([
                    ft.Text("🆔 User ID", size=FONT_SIZE_SM, color=TEXT_SECONDARY, weight=FONT_WEIGHT_MEDIUM),
                ]),
                ft.Text(
                    str(app_state.user_info.get("user_id", "N/A")) if app_state.user_info.get("user_id") is not None else "N/A",
                    size=FONT_SIZE_MD,
                    color=TEXT_PRIMARY,
                ),
                ft.Container(height=SPACING_LG),
                create_status_badge("✓ Online", "success"),
            ],
            spacing=SPACING_SM),
            padding=SPACING_LG,
        )

    profile_info_container = build_profile_info()

    # Store reference to refresh profile when needed
    def refresh_profile():
        profile_info_container.content = build_profile_info().content
        
    return ft.Stack(
        controls=[
            ft.Container(
                expand=True,
                bgcolor=BG_DARK,
                content=ft.Row([
                    # Sidebar
                    ft.Container(
                        width=100,
                        bgcolor=BG_DARKEST,
                        padding=SPACING_MD,
                        border=ft.border.only(right=ft.BorderSide(1, BORDER_COLOR)),
                        content=ft.Column([
                            ft.Text("Menu", size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD, color=PRIMARY_ACCENT),
                            ft.Divider(height=SPACING_SM, color=BORDER_COLOR),
                            ft.Container(
                                height=50,
                                border_radius=RADIUS_MEDIUM,
                                gradient=ft.LinearGradient([PRIMARY_ACCENT, PRIMARY_ACCENT_DARK]),
                                on_click=on_chat_click,
                                content=ft.Row(
                                    spacing=SPACING_SM,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[ft.Text("💬", size=FONT_SIZE_LG), ft.Text("Chat", size=FONT_SIZE_SM, color=TEXT_PRIMARY, weight=FONT_WEIGHT_MEDIUM)],
                                ),
                            ),
                            ft.Container(height=SPACING_SM),
                            ft.Container(
                                height=50,
                                border_radius=RADIUS_MEDIUM,
                                gradient=ft.LinearGradient([INFO, PRIMARY_ACCENT]),
                                on_click=on_history_click,
                                content=ft.Row(
                                    spacing=SPACING_SM,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[ft.Text("📋", size=FONT_SIZE_LG), ft.Text("History", size=FONT_SIZE_SM, color=TEXT_PRIMARY, weight=FONT_WEIGHT_MEDIUM)],
                                ),
                            ),
                            ft.Container(height=SPACING_SM),
                            ft.Container(
                                height=50,
                                border_radius=RADIUS_MEDIUM,
                                gradient=ft.LinearGradient([MOOD_SUYTU, MOOD_BUON]),
                                content=ft.Row(
                                    spacing=SPACING_SM,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[ft.Text("👤", size=FONT_SIZE_LG), ft.Text("Profile", size=FONT_SIZE_SM, color=TEXT_PRIMARY, weight=FONT_WEIGHT_MEDIUM)],
                                ),
                            ),
                            ft.Container(height=SPACING_SM),
                            ft.Container(
                                height=50,
                                border_radius=RADIUS_MEDIUM,
                                gradient=ft.LinearGradient([ERROR, WARNING]),
                                on_click=handle_logout,
                                content=ft.Row(
                                    spacing=SPACING_SM,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[ft.Text("🚪", size=FONT_SIZE_LG), ft.Text("Logout", size=FONT_SIZE_SM, color=TEXT_PRIMARY, weight=FONT_WEIGHT_MEDIUM)],
                                ),
                            ),
                            ft.Container(expand=True),
                            ft.Text("v2.0", size=FONT_SIZE_TINY, color=TEXT_MUTED, weight=FONT_WEIGHT_MEDIUM),
                        ], spacing=SPACING_SM, alignment=ft.MainAxisAlignment.START)
                    ),
                    # Main profile area
                    ft.Container(
                        expand=True,
                        bgcolor=BG_DARK,
                        padding=SPACING_XL,
                        content=ft.Column([
                            ft.Text("👤 Hồ Sơ Của Bạn", size=FONT_SIZE_2XL, weight=FONT_WEIGHT_BOLD, color=PRIMARY_ACCENT),
                            ft.Container(height=SPACING_XL),
                            profile_info_container,
                            ft.Container(height=SPACING_XXL),
                            ft.Container(expand=True),
                            ft.Text("Profile • Professional Design", size=FONT_SIZE_SM, color=TEXT_MUTED),
                        ],
                        spacing=SPACING_SM),
                    ),
                ])
            ),
        ],
        expand=True,
    )
