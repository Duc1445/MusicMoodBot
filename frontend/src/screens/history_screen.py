"""
History screen for MusicMoodBot - Figma Design 1:1
"""

import flet as ft
from datetime import datetime
from src.config.theme_professional import *
from src.services.history_service import history_service


# Figma color scheme
TEAL_PRIMARY = "#4DB6AC"
TEAL_DARK = "#00897B"
SIDEBAR_BG = "#FAFAFA"
YELLOW_BADGE = "#FFF59D"
GREEN_BADGE = "#A5D6A7"
PURPLE_BADGE = "#CE93D8"


def create_history_screen(on_chat_click, on_profile_click):
    """Create history screen matching Figma design exactly"""
    
    history_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=16)
    selected_filter = {"value": "Tất cả"}

    def create_filter_chip(label: str, is_active: bool = False):
        """Create filter chip for mood filtering"""
        def on_click(e):
            selected_filter["value"] = label
            load_history()
        
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=20,
            bgcolor="#1A1A1A" if is_active else "#FFFFFF",
            border=ft.border.all(1, "#1A1A1A" if is_active else "#E0E0E0"),
            on_click=on_click,
            content=ft.Text(label, size=13, 
                          color="#FFFFFF" if is_active else "#1A1A1A",
                          weight=ft.FontWeight.W_500),
        )

    def get_mood_badge_color(mood: str):
        """Get badge color based on mood"""
        mood_colors = {
            "Vui": "#A5D6A7",  # Green
            "Buồn": "#90CAF9",  # Blue
            "Suy tư": "#CE93D8",  # Purple
            "Năng động": "#FFE082",  # Yellow
            "Thư giãn": "#80DEEA",  # Cyan
            "Tập trung": "#FFAB91",  # Orange
        }
        return mood_colors.get(mood, "#E0E0E0")

    def create_history_card(item: dict):
        """Create history card (Figma style with album art)"""
        song_name = item.get("song_name", "Unknown Song")
        artist = item.get("song_artist", item.get("artist", "Unknown Artist"))
        mood = item.get("mood") or "N/A"
        timestamp = item.get("timestamp", "")
        
        # Format date with local timezone
        try:
            from datetime import timezone
            # Parse as UTC and convert to local
            dt = datetime.fromisoformat(timestamp)
            # Add UTC timezone if naive, then convert to local
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            local_dt = dt.astimezone()
            date_str = local_dt.strftime("%d/%m/%Y")
            time_str = local_dt.strftime("%H:%M")
        except:
            date_str = "N/A"
            time_str = ""

        badge_color = get_mood_badge_color(mood)

        return ft.Container(
            padding=ft.padding.all(16),
            border_radius=16,
            bgcolor="#FFFFFF",
            border=ft.border.all(1, "#E8E8E8"),
            shadow=ft.BoxShadow(blur_radius=8, color="#00000008", offset=ft.Offset(0, 2)),
            content=ft.Row([
                # Album art placeholder
                ft.Container(
                    width=100,
                    height=100,
                    border_radius=12,
                    bgcolor="#E0F2F1",
                    alignment=ft.Alignment(0,0),
                    content=ft.Text("🎵", size=40, color=TEAL_PRIMARY),
                ),
                ft.Container(width=16),
                # Song info
                ft.Column([
                    # Mood badge + time
                    ft.Row([
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            border_radius=12,
                            bgcolor=badge_color,
                            content=ft.Row([
                                ft.Text("😊" if mood == "Vui" else "🎵", size=12),
                                ft.Text(f" {mood.upper()}", size=11, weight=ft.FontWeight.W_600, color="#1A1A1A"),
                            ], spacing=0),
                        ),
                        ft.Container(width=8),
                        ft.Text(time_str, size=12, color="#888888"),
                    ]),
                    ft.Container(height=8),
                    # Song name
                    ft.Text(song_name, size=16, weight=ft.FontWeight.W_700, color="#1A1A1A"),
                    # Artist
                    ft.Row([
                        ft.Text("🎤", size=12),
                        ft.Text(f" {artist}", size=13, color="#666666"),
                    ], spacing=0),
                    ft.Container(height=8),
                    # Actions
                    ft.Row([
                        ft.Container(
                            width=32,
                            height=32,
                            border_radius=16,
                            bgcolor="#F5F5F5",
                            alignment=ft.Alignment(0,0),
                            content=ft.Text("🔄", size=14),
                        ),
                        ft.Container(width=8),
                        ft.Text("Chi tiết đề xuất →", size=13, color=TEAL_PRIMARY, 
                               weight=ft.FontWeight.W_500),
                    ]),
                ], spacing=0, expand=True),
                # Date badge
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border_radius=16,
                    bgcolor=TEAL_PRIMARY,
                    content=ft.Text(date_str, size=11, color="#FFFFFF", weight=ft.FontWeight.W_500),
                ),
                # Play/Pause button
                ft.Container(
                    width=36,
                    height=36,
                    border_radius=18,
                    bgcolor="#F0F0F0",
                    alignment=ft.Alignment(0,0),
                    content=ft.Text("⏸", size=16, color="#666666"),
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.START),
        )

    def load_history():
        """Load and display user history"""
        history_list.controls.clear()
        
        # Filter chips
        filter_row = ft.Container(
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            bgcolor="#FFFFFF",
            border_radius=12,
            content=ft.Row([
                ft.Text("≡ Lọc theo cảm xúc:", size=13, color="#666666"),
                ft.Container(width=12),
                create_filter_chip("Tất cả", selected_filter["value"] == "Tất cả"),
                create_filter_chip("Vui", selected_filter["value"] == "Vui"),
                create_filter_chip("Buồn", selected_filter["value"] == "Buồn"),
                create_filter_chip("Năng động", selected_filter["value"] == "Năng động"),
                create_filter_chip("Thư giãn", selected_filter["value"] == "Thư giãn"),
                create_filter_chip("Tập trung", selected_filter["value"] == "Tập trung"),
            ], spacing=8),
        )
        history_list.controls.append(filter_row)
        history_list.controls.append(ft.Container(height=8))

        history_items = history_service.load_user_history()

        if not history_items:
            history_list.controls.append(
                ft.Container(
                    padding=ft.padding.all(40),
                    alignment=ft.Alignment(0,0),
                    content=ft.Column([
                        ft.Text("📭", size=60),
                        ft.Container(height=16),
                        ft.Text("Chưa có lịch sử nghe nhạc", size=16, color="#888888"),
                        ft.Text("Hãy bắt đầu chat để nhận gợi ý nhạc!", size=14, color="#AAAAAA"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                )
            )
            return

        # Filter items by mood if needed
        filtered_items = history_items
        if selected_filter["value"] != "Tất cả":
            filtered_items = [item for item in history_items 
                            if item.get("mood") == selected_filter["value"]]

        for item in filtered_items:
            history_list.controls.append(create_history_card(item))

        # Footer with loading icon
        history_list.controls.append(
            ft.Container(
                height=80,
                alignment=ft.Alignment(0,0),
                content=ft.Container(
                    width=50,
                    height=50,
                    border_radius=25,
                    border=ft.border.all(2, "#E0E0E0"),
                    alignment=ft.Alignment(0,0),
                    content=ft.Text("⏱", size=24, color="#CCCCCC"),
                ),
            )
        )

    # Sidebar menu item
    def create_menu_item(icon: str, label: str, is_active: bool = False, on_click=None):
        return ft.Container(
            height=44,
            border_radius=8,
            bgcolor=TEAL_PRIMARY if is_active else "transparent",
            padding=ft.padding.only(left=12),
            on_click=on_click,
            content=ft.Row([
                ft.Text(icon, size=16, color="#FFFFFF" if is_active else "#666666"),
                ft.Container(width=8),
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, 
                       color="#FFFFFF" if is_active else "#1A1A1A"),
            ], alignment=ft.MainAxisAlignment.START),
        )

    # Load history on create
    load_history()

    # Main layout
    return ft.Container(
        expand=True,
        bgcolor="#FFFFFF",
        content=ft.Row([
            # Sidebar
            ft.Container(
                width=180,
                bgcolor=SIDEBAR_BG,
                border=ft.border.only(right=ft.BorderSide(1, "#E0E0E0")),
                padding=ft.padding.all(16),
                content=ft.Column([
                    # Logo
                    ft.Row([
                        ft.Container(
                            width=32,
                            height=32,
                            border_radius=16,
                            bgcolor=TEAL_PRIMARY,
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
                    create_menu_item("🕐", "Lịch sử", is_active=True),
                    ft.Container(height=4),
                    create_menu_item("👤", "Cá nhân", on_click=lambda e: on_profile_click()),
                    ft.Container(expand=True),
                    # Settings
                    ft.Row([
                        ft.Text("⚙️", size=14),
                        ft.Text(" Cài đặt", size=13, color="#888888"),
                    ]),
                ]),
            ),
            # Main content
            ft.Container(
                expand=True,
                bgcolor="#F8F8F8",
                padding=ft.padding.all(32),
                content=ft.Column([
                    # Header
                    ft.Row([
                        ft.Column([
                            # Archive badge
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                border_radius=4,
                                bgcolor="#1A1A1A",
                                content=ft.Text("ARCHIVE", size=11, color="#FFFFFF", weight=ft.FontWeight.W_600),
                            ),
                            ft.Container(height=8),
                            # Title
                            ft.Text("Lịch sử nghe nhạc", size=32, weight=ft.FontWeight.W_800, color="#1A1A1A"),
                            ft.Container(height=4),
                            ft.Text("Xem lại hành trình cảm xúc và những gợi ý âm nhạc từ MusicMood Bot của bạn.",
                                   size=14, color="#666666"),
                        ], expand=True),
                        # Date picker
                        ft.Container(
                            padding=ft.padding.symmetric(horizontal=16, vertical=10),
                            border_radius=8,
                            bgcolor="#FFFFFF",
                            border=ft.border.all(1, "#E0E0E0"),
                            content=ft.Row([
                                ft.Text("📅", size=14),
                                ft.Text(" Tháng 2, 2026", size=13, color="#1A1A1A"),
                            ]),
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=24),
                    # History list
                    ft.Container(
                        expand=True,
                        content=history_list,
                    ),
                ]),
            ),
        ], spacing=0),
    )
