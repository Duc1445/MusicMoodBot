"""
History screen for MusicMoodBot - Professional UI
"""

import flet as ft
from datetime import datetime
from src.config.theme_professional import *
from src.components.ui_components_pro import *
from src.services.history_service import history_service


def create_history_screen(on_chat_click, on_profile_click):
    """Create simple history screen"""
    history_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=SPACING_SM)

    def load_history():
        """Load and display user history"""
        history_list.controls.clear()
        history_items = history_service.load_user_history()

        if not history_items:
            history_list.controls.append(
                ft.Container(
                    padding=SPACING_LG,
                    content=ft.Text("Chưa có lịch sử trò chuyện.", size=FONT_SIZE_MD, color=TEXT_MUTED)
                )
            )
            return

        # Show summary
        summary = history_service.get_history_summary()
        history_list.controls.append(
            create_glassmorphic_container(
                ft.Column([
                    ft.Text("Tổng Quan", size=FONT_SIZE_MD, weight=FONT_WEIGHT_BOLD, color=TEXT_PRIMARY),
                    ft.Text(
                        f"Tổng: {summary['total']} lần",
                        size=FONT_SIZE_SM,
                        color=TEXT_SECONDARY,
                    ),
                    ft.Text(
                        f"Mood: {summary.get('most_common_mood', 'N/A')}",
                        size=FONT_SIZE_SM,
                        color=TEXT_SECONDARY,
                    ),
                ],
                spacing=4),
                padding=SPACING_SM,
            )
        )

        # Show recommendation cards
        for item in history_items:
            song_name = item.get("song_name", "Unknown")
            artist = item.get("song_artist", "Unknown")
            mood = item.get("mood") or "N/A"  # Handle None
            intensity = item.get("intensity") or "N/A"  # Handle None
            timestamp = item.get("timestamp", "")
            
            # Format time - add timezone conversion
            try:
                from datetime import timezone, timedelta
                dt = datetime.fromisoformat(timestamp)
                # Convert from UTC to local time (UTC+7 for Vietnam)
                local_dt = dt + timedelta(hours=7)
                time_str = local_dt.strftime("%d/%m %H:%M")
            except:
                time_str = timestamp[:16] if len(timestamp) >= 16 else "N/A"
            
            # Create compact card
            card = create_glassmorphic_container(
                ft.Column([
                    ft.Text(song_name, size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD, color=PRIMARY_ACCENT),
                    ft.Text(artist, size=11, color=TEXT_SECONDARY),
                    ft.Row([
                        ft.Text(f"🎵 {mood}", size=11, color=TEXT_PRIMARY),
                        ft.Text(f"📊 {intensity}", size=11, color=TEXT_PRIMARY),
                        ft.Text(f"🕐 {time_str}", size=10, color=TEXT_MUTED),
                    ], spacing=SPACING_SM, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=SPACING_SM,
            )
            history_list.controls.append(card)

    # Sidebar buttons - proper size
    sidebar = ft.Container(
        width=110,
        bgcolor=BG_DARKEST,
        padding=ft.padding.only(left=SPACING_MD, right=SPACING_MD, top=SPACING_MD, bottom=SPACING_MD),
        border=ft.border.only(right=ft.BorderSide(1, BORDER_COLOR)),
        content=ft.Column([
            ft.Container(
                height=55,
                border_radius=RADIUS_MEDIUM,
                gradient=ft.LinearGradient(colors=[PRIMARY_ACCENT, PRIMARY_ACCENT_DARK], begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0)),
                on_click=on_chat_click,
                content=ft.Row(
                    spacing=SPACING_XS,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text("💬", size=FONT_SIZE_MD),
                        ft.Text("Chat", size=FONT_SIZE_SM, color=TEXT_PRIMARY, weight=FONT_WEIGHT_MEDIUM),
                    ],
                ),
            ),
            ft.Container(height=SPACING_SM),
            ft.Container(
                height=55,
                border_radius=RADIUS_MEDIUM,
                gradient=ft.LinearGradient(colors=["#00D9FF", "#0099CC"], begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0)),
                on_click=lambda e: load_history(),
                content=ft.Row(
                    spacing=SPACING_XS,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text("📋", size=FONT_SIZE_MD),
                        ft.Text("History", size=FONT_SIZE_SM, color=TEXT_PRIMARY, weight=FONT_WEIGHT_MEDIUM),
                    ],
                ),
            ),
            ft.Container(height=SPACING_SM),
            ft.Container(
                height=55,
                border_radius=RADIUS_MEDIUM,
                gradient=ft.LinearGradient(colors=["#FF6B9D", "#C44569"], begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0)),
                on_click=on_profile_click,
                content=ft.Row(
                    spacing=SPACING_XS,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Text("👤", size=FONT_SIZE_MD),
                        ft.Text("Profile", size=FONT_SIZE_SM, color=TEXT_PRIMARY, weight=FONT_WEIGHT_MEDIUM),
                    ],
                ),
            ),
        ]),
    )

    # Header with title aligned to Chat button
    header_content = ft.Container(
        height=55,
        bgcolor=BG_DARK,
        padding=ft.padding.only(left=SPACING_MD, right=SPACING_MD, top=SPACING_XS),
        content=ft.Text(
            "📋 Lịch Sử",
            size=FONT_SIZE_LG,
            weight=FONT_WEIGHT_BOLD,
            color=PRIMARY_ACCENT,
        ),
    )

    # Main content without title
    main_content_list = ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        padding=ft.padding.only(left=SPACING_MD, right=SPACING_MD, bottom=SPACING_MD),
        content=ft.Column([
            ft.Divider(height=1, color=BORDER_COLOR),
            ft.Container(
                expand=True,
                content=history_list,
            ),
        ],
        spacing=SPACING_XS,
        scroll=ft.ScrollMode.AUTO,
        ),
    )

    # Right side column with header and content
    right_content = ft.Column([
        header_content,
        main_content_list,
    ], spacing=0, expand=True)

    # Load initial history
    load_history()
    
    return ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        content=ft.Row([sidebar, right_content], spacing=0, expand=True),
    )
