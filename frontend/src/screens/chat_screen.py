"""
Chat screen for MusicMoodBot - Figma Design 1:1
"""

import flet as ft
from datetime import datetime
from src.config.theme_professional import *
from src.services.chat_service import chat_service
from src.utils.state_manager import app_state


# Figma color scheme
TEAL_PRIMARY = "#4DB6AC"  # Teal/Cyan for chat
TEAL_DARK = "#00897B"
SIDEBAR_BG = "#FAFAFA"
CHAT_BG = "#F5F5F5"


def create_chat_screen(page, on_history_click, on_profile_click):
    """Create chat screen matching Figma design exactly"""
    
    message_field = ft.TextField(
        hint_text="Nhập tin nhắn...",
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color="#999999", size=14),
        text_style=ft.TextStyle(color="#1A1A1A", size=14),
        expand=True,
    )
    
    messages_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=16)

    def set_busy(is_busy: bool):
        app_state.chat_flow["busy"] = is_busy
        message_field.disabled = is_busy

    def create_bot_message(text: str, time_str: str = None):
        """Create bot message bubble (left side)"""
        if not time_str:
            time_str = datetime.now().strftime("%H:%M %p")
        return ft.Row([
            # Bot avatar
            ft.Container(
                width=36,
                height=36,
                border_radius=18,
                bgcolor=TEAL_PRIMARY,
                alignment=ft.Alignment(0,0),
                content=ft.Text("🤖", size=18),
            ),
            ft.Container(width=8),
            ft.Column([
                ft.Row([
                    ft.Text("MusicMoodBot", size=12, weight=ft.FontWeight.W_600, color="#1A1A1A"),
                    ft.Text(f"  {time_str}", size=11, color="#888888"),
                ], spacing=0),
                ft.Container(height=4),
                ft.Container(
                    padding=ft.padding.all(14),
                    border_radius=12,
                    bgcolor="#FFFFFF",
                    border=ft.border.all(1, "#E0E0E0"),
                    content=ft.Text(text, size=14, color="#1A1A1A"),
                ),
            ], spacing=0),
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)

    def create_user_message(text: str):
        """Create user message bubble (right side)"""
        return ft.Row([
            ft.Container(expand=True),
            ft.Column([
                ft.Text("You", size=12, color="#888888", text_align=ft.TextAlign.RIGHT),
                ft.Container(height=4),
                ft.Container(
                    padding=ft.padding.all(14),
                    border_radius=12,
                    bgcolor=TEAL_PRIMARY,
                    content=ft.Text(text, size=14, color="#FFFFFF"),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=0),
            ft.Container(width=8),
            # User avatar
            ft.Container(
                width=36,
                height=36,
                border_radius=18,
                bgcolor="#E0E0E0",
                alignment=ft.Alignment(0,0),
                content=ft.Text("👤", size=18),
            ),
        ], alignment=ft.MainAxisAlignment.END, vertical_alignment=ft.CrossAxisAlignment.START)

    def create_song_card(song: dict):
        """Create song recommendation card (Figma style)"""
        def on_try_again(e):
            if not app_state.chat_flow["busy"]:
                app_state.chat_flow["state"] = "chatting"
                
                def apply():
                    make_recommendation(try_again=True)
                
                do_bot_reply(apply)
        
        return ft.Container(
            margin=ft.margin.only(left=44),
            padding=ft.padding.all(16),
            border_radius=12,
            bgcolor="#FFFFFF",
            border=ft.border.all(1, "#E0E0E0"),
            content=ft.Row([
                # Song icon
                ft.Container(
                    width=50,
                    height=50,
                    border_radius=8,
                    bgcolor="#F0F0F0",
                    alignment=ft.Alignment(0,0),
                    content=ft.Text("♪", size=24, color=TEAL_PRIMARY),
                ),
                ft.Container(width=12),
                # Song info
                ft.Column([
                    ft.Text(song.get("song_name", song.get("name", "Bài hát A")), 
                           size=15, weight=ft.FontWeight.W_600, color="#1A1A1A"),
                    ft.Text(f"Nghệ sĩ {song.get('artist', 'Unknown')}", 
                           size=13, color="#666666"),
                    ft.Row([
                        ft.Text("🎵", size=12),
                        ft.Text(f" Reason: {song.get('reason', 'Phù hợp mood của bạn')}", 
                               size=12, color="#888888"),
                    ], spacing=0),
                ], spacing=4, expand=True),
                # Refresh button
                ft.Container(
                    width=40,
                    height=40,
                    border_radius=20,
                    bgcolor="#F5F5F5",
                    alignment=ft.Alignment(0,0),
                    on_click=on_try_again,
                    content=ft.Text("🔄", size=16),
                ),
                ft.Container(width=8),
                # Play button
                ft.Container(
                    width=44,
                    height=44,
                    border_radius=22,
                    bgcolor=TEAL_PRIMARY,
                    alignment=ft.Alignment(0,0),
                    content=ft.Text("▶", size=18, color="#FFFFFF"),
                ),
            ]),
        )

    def create_mood_chip(mood_name: str, emoji: str):
        """Create mood selection chip (Figma style - outlined, compact)"""
        def on_click(e):
            if app_state.chat_flow["busy"]:
                return
            if app_state.chat_flow["state"] == "await_mood":
                handle_mood_selection(mood_name)
        
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=16,
            bgcolor="#FFFFFF",
            border=ft.border.all(1, "#1A1A1A"),
            on_click=on_click,
            content=ft.Row([
                ft.Text(emoji, size=12),
                ft.Text(f" {mood_name}", size=11, weight=ft.FontWeight.W_500, color="#1A1A1A"),
            ], spacing=0),
        )

    def create_intensity_chip(intensity_name: str, emoji: str):
        """Create intensity selection chip (compact)"""
        def on_click(e):
            if app_state.chat_flow["busy"]:
                return
            if app_state.chat_flow["state"] == "await_intensity":
                handle_intensity_selection(intensity_name)
        
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=16,
            bgcolor="#FFFFFF",
            border=ft.border.all(1, TEAL_PRIMARY),
            on_click=on_click,
            content=ft.Row([
                ft.Text(emoji, size=12),
                ft.Text(f" {intensity_name}", size=11, weight=ft.FontWeight.W_500, color=TEAL_DARK),
            ], spacing=0),
        )

    # Mood chips row (compact, single line)
    mood_chips = ft.Row([
        create_mood_chip("Vui", "😊"),
        create_mood_chip("Buồn", "😢"),
        create_mood_chip("Năng động", "⚡"),
        create_mood_chip("Thư giãn", "🍃"),
        create_mood_chip("Tập trung", "🎯"),
    ], spacing=6)

    # Intensity chips row (compact, single line)
    intensity_chips = ft.Row([
        create_intensity_chip("Nhẹ", "🌸"),
        create_intensity_chip("Vừa", "🌿"),
        create_intensity_chip("Mạnh", "🔥"),
    ], spacing=6)

    mood_section = ft.Container(
        visible=(app_state.chat_flow["state"] == "await_mood"),
        margin=ft.margin.only(left=44, top=4, bottom=4),
        content=mood_chips,
    )

    intensity_section = ft.Container(
        visible=(app_state.chat_flow["state"] == "await_intensity"),
        margin=ft.margin.only(left=44, top=4, bottom=4),
        content=intensity_chips,
    )

    def refresh_messages():
        """Refresh message display"""
        messages_list.controls.clear()
        
        # Date separator
        messages_list.controls.append(
            ft.Row([
                ft.Container(expand=True),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=6),
                    border_radius=16,
                    bgcolor="#E8E8E8",
                    content=ft.Text("Today", size=12, color="#666666"),
                ),
                ft.Container(expand=True),
            ])
        )

        for msg in app_state.chat_messages:
            if msg["kind"] == "text":
                if msg["sender"] == "user":
                    messages_list.controls.append(create_user_message(msg["text"]))
                else:
                    messages_list.controls.append(create_bot_message(msg["text"]))
            elif msg["kind"] == "card":
                messages_list.controls.append(create_song_card(msg["song"]))

        # Update visibility
        mood_section.visible = (app_state.chat_flow["state"] == "await_mood")
        intensity_section.visible = (app_state.chat_flow["state"] == "await_intensity")

        if app_state.typing_on["value"]:
            messages_list.controls.append(
                ft.Row([
                    ft.Container(
                        width=36,
                        height=36,
                        border_radius=18,
                        bgcolor=TEAL_PRIMARY,
                        alignment=ft.Alignment(0,0),
                        content=ft.Text("🤖", size=18),
                    ),
                    ft.Container(width=8),
                    ft.Container(
                        padding=ft.padding.all(12),
                        border_radius=12,
                        bgcolor="#FFFFFF",
                        border=ft.border.all(1, "#E0E0E0"),
                        content=ft.Row([
                            ft.ProgressRing(width=16, height=16, stroke_width=2),
                            ft.Text(" Đang nhập...", size=13, color="#888888"),
                        ]),
                    ),
                ])
            )

        # Safe UI update - works from any thread in Flet
        try:
            page.update()
        except Exception as e:
            print(f"Page update error: {e}")

    def make_recommendation(try_again: bool = False):
        """Generate and display recommendation with Top 3 songs"""
        mood = app_state.chat_flow["mood"] or "Chill"
        intensity = app_state.chat_flow["intensity"] or "Vừa"
        
        if try_again:
            import random
            all_intensities = ["Nhẹ", "Vừa", "Mạnh"]
            new_intensity = random.choice(all_intensities)
            while new_intensity == intensity:
                new_intensity = random.choice(all_intensities)
            intensity = new_intensity
            app_state.chat_flow["intensity"] = intensity
        
        # Get 3 different songs for Top 3 with error handling
        songs = []
        used_names = set()
        max_attempts = 10
        attempts = 0
        
        while len(songs) < 3 and attempts < max_attempts:
            attempts += 1
            try:
                song = chat_service.pick_song(mood)
                # Avoid duplicate songs
                song_name = song.get("name", "") if isinstance(song, dict) else ""
                if song_name and song_name not in used_names and song_name != "No songs found":
                    songs.append(song)
                    used_names.add(song_name)
            except Exception as e:
                print(f"Error picking song: {e}")
                break
        
        # If no songs found, add a default message
        if not songs:
            chat_service.add_message("bot", "text", "Xin lỗi, không tìm thấy bài hát phù hợp. Hãy thử chọn mood khác nhé!")
            app_state.chat_flow["state"] = "await_mood"
            app_state.chat_flow["mood"] = None
            return

        text = (
            f"Dựa trên cảm xúc và thể loại bạn chọn, đây là Top {len(songs)} bài hát phù hợp nhất cho bạn hôm nay:"
            if not try_again
            else f"Đây là gợi ý khác cho bạn (mood: {mood}, intensity: {intensity}):"
        )

        chat_service.add_message("bot", "text", text)
        
        # Add all song cards
        for song in songs:
            chat_service.add_message("bot", "card", song=song)
            song_id = song.get("song_id") if isinstance(song, dict) else None
            chat_service.save_recommendation(song_id=song_id)
        
        app_state.chat_flow["state"] = "await_mood"
        app_state.chat_flow["mood"] = None

    def do_bot_reply(apply_fn):
        """Execute bot reply synchronously - no threading"""
        set_busy(True)
        
        # Execute the apply function directly
        try:
            apply_fn()
        except Exception as e:
            print(f"Error in apply_fn: {e}")
            chat_service.add_message("bot", "text", "Đã có lỗi xảy ra, vui lòng thử lại.")
        
        # Reset busy state and refresh UI
        set_busy(False)
        refresh_messages()

    def handle_mood_selection(mood: str):
        """Handle mood chip click - no threading for simple message"""
        if app_state.chat_flow["busy"]:
            return
            
        chat_service.add_message("user", "text", f"Mood: {mood}")
        app_state.chat_flow["mood"] = mood
        app_state.chat_flow["state"] = "await_intensity"
        
        # Add bot message directly without typing indicator delay
        chat_service.add_message("bot", "text", "Bạn muốn mức độ nào? (Nhẹ / Vừa / Mạnh)")
        refresh_messages()

    def handle_intensity_selection(intensity: str):
        """Handle intensity chip click - synchronous"""
        if app_state.chat_flow["busy"]:
            return
            
        chat_service.add_message("user", "text", f"Intensity: {intensity}")
        app_state.chat_flow["intensity"] = intensity
        app_state.chat_flow["state"] = "chatting"
        refresh_messages()

        def apply():
            make_recommendation()

        do_bot_reply(apply)

    def send_message(e):
        """Handle message sending"""
        if app_state.chat_flow["busy"]:
            return
        text = (message_field.value or "").strip()
        if not text:
            return

        chat_service.add_message("user", "text", text)
        message_field.value = ""
        refresh_messages()

        st = app_state.chat_flow["state"]

        # Luôn thử gọi smart_recommend để phát hiện mood từ text
        if st == "await_mood":
            def apply():
                # Gọi API để phát hiện mood và gợi ý nhạc từ text
                result = chat_service.smart_recommend(text)
                
                if result.get("success") and result.get("songs"):
                    # API đã phát hiện mood và trả về gợi ý
                    bot_message = result.get("bot_message", "Đây là gợi ý cho bạn:")
                    chat_service.add_message("bot", "text", bot_message)
                    
                    # Hiển thị các bài hát
                    for song in result.get("songs", []):
                        chat_service.add_message("bot", "card", song=song)
                    
                    # Reset state để có thể chọn mood mới
                    app_state.chat_flow["state"] = "await_mood"
                    app_state.chat_flow["mood"] = None
                    
                elif result.get("require_mood_selection"):
                    # Cần thêm thông tin - hiển thị nút mood
                    bot_msg = result.get("bot_message") or "Mình hiểu rồi! Bạn có thể chọn mood bằng nút bên dưới hoặc chia sẻ thêm cảm xúc của bạn nhé 😊"
                    chat_service.add_message("bot", "text", bot_msg)
                    app_state.chat_flow["state"] = "await_mood"  # Enable mood buttons
                else:
                    # Lỗi hoặc không có kết quả
                    chat_service.add_message("bot", "text", 
                        "Mình chưa hiểu lắm. Bạn có thể chọn mood bên dưới hoặc mô tả cảm xúc rõ hơn nhé!")
            
            do_bot_reply(apply)
            return
        
        if st == "await_intensity":
            text_lower = text.lower()
            intensity_map = {
                "nhẹ": "Nhẹ", "nhe": "Nhẹ", "light": "Nhẹ",
                "vừa": "Vừa", "vua": "Vừa", "medium": "Vừa",
                "mạnh": "Mạnh", "manh": "Mạnh", "strong": "Mạnh"
            }
            
            detected_intensity = None
            for keyword, intensity in intensity_map.items():
                if keyword in text_lower:
                    detected_intensity = intensity
                    break
            
            if detected_intensity:
                app_state.chat_flow["intensity"] = detected_intensity
                app_state.chat_flow["state"] = "chatting"
                
                def apply():
                    make_recommendation()
                    
                do_bot_reply(apply)
                return
            
            chat_service.add_message("bot", "text", "Hãy chọn intensity: Nhẹ, Vừa, hoặc Mạnh")
            refresh_messages()
            return

        # State "chatting" hoặc khác - cũng gọi smart_recommend
        def apply():
            result = chat_service.smart_recommend(text)
            
            if result.get("success") and result.get("songs"):
                bot_message = result.get("bot_message", "Đây là gợi ý mới cho bạn:")
                chat_service.add_message("bot", "text", bot_message)
                
                for song in result.get("songs", []):
                    chat_service.add_message("bot", "card", song=song)
                
                app_state.chat_flow["state"] = "await_mood"
                app_state.chat_flow["mood"] = None
            elif result.get("require_mood_selection"):
                bot_msg = result.get("bot_message") or "Mình hiểu rồi! Bạn có thể chọn mood bằng nút bên dưới hoặc chia sẻ thêm cảm xúc nhé 😊"
                chat_service.add_message("bot", "text", bot_msg)
                app_state.chat_flow["state"] = "await_mood"  # Enable mood buttons
            else:
                chat_service.add_message("bot", "text", 
                    f"Mình đã nhận: \"{text}\". Bạn có thể chọn mood mới hoặc mô tả cảm xúc rõ hơn!")
        
        do_bot_reply(apply)

    def reset_chat():
        """Reset chat"""
        chat_service.reset()
        message_field.disabled = False
        chat_service.add_message("bot", "text", 
            "Chào bạn! Hôm nay bạn cảm thấy thế nào? Mình sẽ giúp bạn chọn nhạc phù hợp nhé!")
        refresh_messages()

    def bootstrap_after_mounted():
        """Initialize chat screen after mounting"""
        if len(app_state.chat_messages) == 0:
            reset_chat()
        else:
            refresh_messages()

    app_state.set_chat_bootstrap(bootstrap_after_mounted)

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
                    ft.Container(height=8),
                    ft.Text("Menu", size=12, color="#888888"),
                    ft.Container(height=8),
                    # Menu items
                    create_menu_item("💬", "Đoạn chat", is_active=True),
                    ft.Container(height=4),
                    create_menu_item("🕐", "Lịch sử", on_click=lambda e: on_history_click()),
                    ft.Container(height=4),
                    create_menu_item("👤", "Hồ sơ", on_click=lambda e: on_profile_click()),
                    ft.Container(expand=True),
                    ft.Text("MUSICMOOD V1.0", size=10, color="#AAAAAA"),
                ]),
            ),
            # Main content
            ft.Container(
                expand=True,
                bgcolor=CHAT_BG,
                content=ft.Column([
                    # Header
                    ft.Container(
                        height=60,
                        bgcolor="#FFFFFF",
                        border=ft.border.only(bottom=ft.BorderSide(1, "#E0E0E0")),
                        padding=ft.padding.symmetric(horizontal=24),
                        content=ft.Row([
                            ft.Row([
                                ft.Container(
                                    width=40,
                                    height=40,
                                    border_radius=20,
                                    bgcolor=TEAL_PRIMARY,
                                    alignment=ft.Alignment(0,0),
                                    content=ft.Text("🤖", size=20),
                                ),
                                ft.Container(width=12),
                                ft.Column([
                                    ft.Text("MusicMoodBot", size=16, weight=ft.FontWeight.W_600, color="#1A1A1A"),
                                    ft.Row([
                                        ft.Container(width=8, height=8, border_radius=4, bgcolor="#22C55E"),
                                        ft.Text(" Online", size=12, color="#888888"),
                                    ], spacing=0),
                                ], spacing=2),
                            ]),
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.SETTINGS, icon_color="#666666", icon_size=20),
                                ft.Container(
                                    width=36,
                                    height=36,
                                    border_radius=18,
                                    bgcolor="#E0E0E0",
                                    alignment=ft.Alignment(0,0),
                                    content=ft.Text("👤", size=16),
                                ),
                            ], spacing=8),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ),
                    # Messages area
                    ft.Container(
                        expand=True,
                        padding=ft.padding.all(24),
                        content=ft.Column([
                            ft.Container(expand=True, content=messages_list),
                            mood_section,
                            intensity_section,
                        ]),
                    ),
                    # Input area
                    ft.Container(
                        height=70,
                        bgcolor="#FFFFFF",
                        border=ft.border.only(top=ft.BorderSide(1, "#E0E0E0")),
                        padding=ft.padding.symmetric(horizontal=24, vertical=12),
                        content=ft.Row([
                            # Add button
                            ft.Container(
                                width=40,
                                height=40,
                                border_radius=20,
                                bgcolor="#F0F0F0",
                                alignment=ft.Alignment(0,0),
                                content=ft.Text("➕", size=18),
                            ),
                            ft.Container(width=12),
                            # Text input
                            ft.Container(
                                expand=True,
                                height=44,
                                border_radius=22,
                                bgcolor="#F5F5F5",
                                border=ft.border.all(1, "#E0E0E0"),
                                padding=ft.padding.only(left=20, right=12),
                                content=ft.Row([
                                    ft.Container(expand=True, content=message_field),
                                ]),
                            ),
                            ft.Container(width=12),
                            # Send button
                            ft.Container(
                                width=70,
                                height=44,
                                border_radius=22,
                                bgcolor=TEAL_PRIMARY,
                                alignment=ft.Alignment(0,0),
                                on_click=send_message,
                                content=ft.Row([
                                    ft.Text("Gửi", size=14, weight=ft.FontWeight.W_600, color="#FFFFFF"),
                                    ft.Text(" ➤", size=14, color="#FFFFFF"),
                                ], alignment=ft.MainAxisAlignment.CENTER),
                            ),
                        ]),
                    ),
                    # Footer
                    ft.Container(
                        height=28,
                        bgcolor="#FFFFFF",
                        alignment=ft.Alignment(0,0),
                        content=ft.Text("CDIO PROJECT • VARIANT 1", size=10, color="#CCCCCC"),
                    ),
                ], spacing=0),
            ),
        ], spacing=0),
    )
