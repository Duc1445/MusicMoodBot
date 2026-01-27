"""
Chat screen for MusicMoodBot - Professional UI
"""

import flet as ft
import threading
import time
import os
from src.config.theme_professional import *
from src.components.ui_components_pro import *
from src.services.chat_service import chat_service
from src.services.history_service import history_service
from src.utils.state_manager import app_state
from src.utils.helpers import _make_progress, _ui_safe


def create_chat_screen(page, on_history_click, on_profile_click):
    """Create chat screen UI"""
    
    message_field = ft.TextField(
        hint_text="Nhập tin nhắn…",
        border=ft.InputBorder.UNDERLINE,
        expand=True,
        text_style=ft.TextStyle(color="#FFFFFF", size=14),
        hint_style=ft.TextStyle(color="#475569", size=14),
        color="#FFFFFF",
        cursor_color="#00D9FF",
        focused_color="#00D9FF",
        bgcolor=ft.Colors.TRANSPARENT,
    )
    send_btn = ft.Button(
        "Gửi",
        width=80,
        height=40,
        style=ft.ButtonStyle(
            color="#0F1419",
            bgcolor={"": "#00D9FF"},
        ),
    )
    messages_list = ft.Column(scroll=ft.ScrollMode.AUTO)

    def set_busy(is_busy: bool):
        app_state.chat_flow["busy"] = is_busy
        message_field.disabled = is_busy
        send_btn.disabled = is_busy

    def bubble_for_text(sender: str, text: str):
        """Create professional message bubble"""
        return create_message_bubble_professional(sender, text)

    def build_song_card(song: dict):
        """Create song recommendation card"""
        def on_try_again(e):
            if app_state.chat_flow["busy"]:
                return
            # Apply recommendation immediately without typing indicator
            make_recommendation(try_again=True)
            refresh_messages()
            page.update()

        return ft.Container(
            width=520,
            bgcolor=BG_CARD,
            padding=16,
            border_radius=16,
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text("🎵 Recommendation", size=FONT_SIZE_MD, weight=FONT_WEIGHT_BOLD, color=PRIMARY_ACCENT),
                    ft.Text(song["name"], size=FONT_SIZE_MD, weight=FONT_WEIGHT_BOLD, color=TEXT_PRIMARY),
                    ft.Text(f"Artist: {song['artist']}", size=FONT_SIZE_SM, color=TEXT_PRIMARY),
                    ft.Text(f"Genre: {song['genre']}", size=FONT_SIZE_SM, color=TEXT_PRIMARY),
                    ft.Text(f"Suy Score: {song['suy_score']}/10", size=FONT_SIZE_SM, color=TEXT_PRIMARY),
                    ft.Text(f"Reason: {song['reason']}", size=FONT_SIZE_SM, color=TEXT_SECONDARY),
                    ft.Container(height=6),
                    ft.Row([ft.Button("Try again", on_click=on_try_again)], alignment=ft.MainAxisAlignment.END),
                ],
            ),
        )

    def refresh_messages():
        """Refresh message display"""
        messages_list.controls.clear()

        for msg in app_state.chat_messages:
            if msg["kind"] == "text":
                item = bubble_for_text(msg["sender"], msg["text"])
                messages_list.controls.append(item)
            elif msg["kind"] == "card":
                messages_list.controls.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.START,
                        controls=[build_song_card(msg["song"])],
                    )
                )

        # Update visibility based on state
        mood_section.visible = (app_state.chat_flow["state"] == "await_mood")
        intensity_section.visible = (app_state.chat_flow["state"] == "await_intensity")

        if app_state.typing_on["value"]:
            messages_list.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    spacing=SPACING_SM,
                    controls=[
                        ft.Container(
                            width=220,
                            bgcolor=BG_INPUT,
                            padding=12,
                            border_radius=12,
                            content=ft.Row(
                                spacing=10,
                                controls=[_make_progress(), ft.Text("Bot đang nhập...", size=FONT_SIZE_SM)],
                            ),
                        ),
                    ],
                )
            )

        page.update()



    def make_recommendation(try_again: bool = False):
        """Generate and display recommendation"""
        mood = app_state.chat_flow["mood"] or "Chill"
        intensity = app_state.chat_flow["intensity"] or "Vừa"
        
        # If try_again, random a different intensity
        if try_again:
            import random
            all_intensities = ["Nhẹ", "Vừa", "Mạnh"]
            # Keep trying until we get a different intensity
            new_intensity = random.choice(all_intensities)
            while new_intensity == intensity:
                new_intensity = random.choice(all_intensities)
            intensity = new_intensity
            app_state.chat_flow["intensity"] = intensity  # Update state with new intensity
        
        song = chat_service.pick_song(mood)

        text = (
            f"Ok, mình thử bài khác (mood: {mood}, intensity: {intensity}) nhé."
            if try_again
            else f"Mình đã hiểu (mood: {mood}, intensity: {intensity}). Đây là gợi ý phù hợp:"
        )

        # Just add messages to state, don't call start_bot_reply again
        chat_service.add_message("bot", "text", text)
        chat_service.add_message("bot", "card", song=song)
        song_id = song.get("song_id") if isinstance(song, dict) else None
        chat_service.save_recommendation(song_id=song_id)
        
        # Reset state to allow continuous chat
        app_state.chat_flow["state"] = "await_mood"
        app_state.chat_flow["mood"] = None
        # Keep intensity so try_again can random it properly

    def start_bot_reply(apply_fn, delay_sec: float = 0.0):
        """Start bot typing indicator and apply function"""
        set_busy(True)
        app_state.typing_on["value"] = True
        refresh_messages()

        def worker():
            # Use minimal delay for responsiveness, but keep typing indicator visible briefly
            if delay_sec > 0:
                time.sleep(delay_sec)

            def finish():
                app_state.typing_on["value"] = False
                apply_fn()
                set_busy(False)
                refresh_messages()

            _ui_safe(page, finish)

        threading.Thread(target=worker, daemon=True).start()

    def handle_mood_selection(mood: str):
        """Handle mood chip click"""
        chat_service.add_message("user", "text", f"{MOOD_CONFIG[mood]['emoji']} Mood: {mood}")
        app_state.chat_flow["mood"] = mood
        app_state.chat_flow["state"] = "await_intensity"
        
        refresh_messages()
        page.update()

        def apply():
            chat_service.add_message("bot", "text", "Ok. Bạn muốn intensity mức nào? (Nhẹ / Vừa / Mạnh)")

        start_bot_reply(apply, delay_sec=0)

    def handle_emotion_click(emotion):
        """Handle emotion button click - wrapper for mood selection"""
        def handler(e):
            if app_state.chat_flow["busy"]:
                return
            if app_state.chat_flow["state"] in ("await_mood",):
                handle_mood_selection(emotion)
            else:
                chat_service.add_message("user", "text", f"{MOOD_CONFIG.get(emotion, {}).get('emoji', '🎵')} Cảm xúc: {emotion}")
                refresh_messages()
        return handler

    def handle_intensity_click(intensity: str):
        """Handle intensity button click"""
        def handler(e):
            if app_state.chat_flow["busy"]:
                return
            if app_state.chat_flow["state"] == "await_intensity":
                chat_service.add_message("user", "text", f"{INTENSITY_CONFIG[intensity]['emoji']} Intensity: {intensity}")
                app_state.chat_flow["intensity"] = intensity
                app_state.chat_flow["state"] = "chatting"
                refresh_messages()
                page.update()
                
                # Apply recommendation immediately
                make_recommendation()
                refresh_messages()
                page.update()
        return handler

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

        if st in ("await_mood", "await_intensity"):
            def apply():
                chat_service.add_message("bot", "text", "Mình chưa hiểu ý bạn. Hãy chọn 1 mood bằng nút bên dưới.")
            start_bot_reply(apply, delay_sec=0)
            return

        def apply():
            msg_text = f"Mình đã nhận: \"{text}\". Nếu muốn đổi gợi ý, bấm 'Try again'."
            chat_service.add_message("bot", "text", msg_text)

        start_bot_reply(apply, delay_sec=0)

    send_btn.on_click = send_message
    message_field.on_submit = send_message

    # Create mood and intensity sections with references for visibility control
    mood_section = ft.Column(
        controls=[
            create_glassmorphic_container(
                ft.Column([
                    ft.Text("Chọn cảm xúc:", size=11, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                    ft.Container(height=4),
                    ft.Row(
                        spacing=6,
                        wrap=True,
                        controls=[
                            ft.Container(
                                width=60,
                                height=70,
                                padding=6,
                                border_radius=12,
                                bgcolor=f"{PRIMARY_ACCENT}15",
                                border=ft.border.all(1.5, PRIMARY_ACCENT),
                                content=ft.Column(
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(MOOD_CONFIG.get(mood, {}).get('emoji', '🎵'), size=18),
                                        ft.Text(mood, size=9, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                                    ],
                                ),
                                on_click=handle_emotion_click(mood),
                            )
                            for mood in ["Vui", "Buồn", "Suy tư", "Chill", "Nâng lương"]
                        ],
                    ),
                ]),
                padding=8,
            ),
        ],
        spacing=SPACING_SM,
        visible=(app_state.chat_flow["state"] == "await_mood"),
    )
    
    intensity_section = ft.Column(
        controls=[
            create_glassmorphic_container(
                ft.Column([
                    ft.Text("Chọn mức độ:", size=11, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                    ft.Container(height=4),
                    ft.Row(
                        spacing=6,
                        wrap=True,
                        controls=[
                            ft.Container(
                                width=60,
                                height=70,
                                padding=6,
                                border_radius=12,
                                bgcolor=f"{PRIMARY_ACCENT}15",
                                border=ft.border.all(1.5, PRIMARY_ACCENT),
                                content=ft.Column(
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(INTENSITY_CONFIG.get(intensity, {}).get('emoji', '🎵'), size=18),
                                        ft.Text(intensity, size=9, weight=FONT_WEIGHT_SEMIBOLD, color=TEXT_PRIMARY),
                                    ],
                                ),
                                on_click=handle_intensity_click(intensity),
                            )
                            for intensity in ["Nhẹ", "Vừa", "Mạnh"]
                        ],
                    ),
                ]),
                padding=8,
            ),
        ],
        spacing=SPACING_SM,
        visible=(app_state.chat_flow["state"] == "await_intensity"),
    )

    def reset_chat():
        """Reset chat"""
        chat_service.reset()
        message_field.disabled = False
        send_btn.disabled = False
        chat_service.add_message("bot", "text", "Chào bạn. Hôm nay bạn cảm thấy thế nào?")
        refresh_messages()

    def on_reset_click(e):
        if app_state.chat_flow["busy"]:
            return
        reset_chat()

    def bootstrap_after_mounted():
        """Initialize chat screen after mounting"""
        if len(app_state.chat_messages) == 0:
            reset_chat()
        else:
            refresh_messages()

    # Store bootstrap function
    app_state.set_chat_bootstrap(bootstrap_after_mounted)

    return ft.Container(
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
                        gradient=ft.LinearGradient([MOOD_VUI, WARNING]),
                        on_click=on_profile_click,
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
                        on_click=on_reset_click,
                        content=ft.Row(
                            spacing=SPACING_SM,
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[ft.Text("🧹", size=FONT_SIZE_LG), ft.Text("Reset", size=FONT_SIZE_SM, color=TEXT_PRIMARY, weight=FONT_WEIGHT_MEDIUM)],
                        ),
                    ),
                    ft.Container(expand=True),
                    ft.Text("v2.0", size=FONT_SIZE_TINY, color=TEXT_MUTED, weight=FONT_WEIGHT_MEDIUM),
                ], spacing=SPACING_SM, alignment=ft.MainAxisAlignment.START)
            ),
            # Main chat area
            ft.Container(
                expand=True,
                bgcolor=BG_DARK,
                padding=SPACING_LG,
                content=ft.Column([
                    ft.Text("🎵 MusicMoodBot", size=FONT_SIZE_XL, weight=FONT_WEIGHT_BOLD, color=PRIMARY_ACCENT),
                    ft.Divider(height=SPACING_SM, color=BORDER_COLOR),
                    ft.Container(height=SPACING_SM),
                    create_section_spacer(SPACING_SM),
                    ft.Container(expand=True, content=messages_list),
                    ft.Container(height=SPACING_MD),
                    mood_section,
                    intensity_section,
                    ft.Container(height=SPACING_MD),
                    ft.Text("MusicMoodBot v2.0", size=FONT_SIZE_SM, color=TEXT_MUTED),
                    ft.Container(height=SPACING_SM),
                    ft.Row([message_field, send_btn]),
                ])
            ),
        ])
    )
