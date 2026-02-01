"""
Chat Screen - Refactored
=========================
Clean, modular chat screen with separated concerns.

Structure:
- Uses components from `components/chat/`
- Uses centralized settings from `config/settings.py`
- Uses state from `utils/state_manager.py`

Author: MusicMoodBot Team
"""

import flet as ft
import threading
import time
from datetime import datetime

# Centralized config
from ..config.settings import settings, logger, CHAT_STATE_AWAIT_MOOD, CHAT_STATE_AWAIT_INTENSITY

# Components
from ..components.chat import (
    create_bot_message,
    create_user_message,
    create_song_card,
    create_typing_indicator
)
from ..components.chat.mood_chips import create_mood_chip, create_intensity_chip

# Services
from ..services.api_client import api
from ..services.chat_service import chat_service

# State
from ..utils.state_manager import app_state
from ..utils.helpers import _make_progress, _ui_safe


class ChatScreenController:
    """
    Controller for chat screen logic.
    Separates business logic from UI.
    """
    
    def __init__(self, page: ft.Page, on_refresh: callable):
        self.page = page
        self.on_refresh = on_refresh
        logger.debug("ChatScreenController initialized")
    
    def set_busy(self, is_busy: bool):
        """Set busy state"""
        app_state.set_busy(is_busy)
    
    def start_bot_reply(self, apply_fn: callable, delay_sec: float = 0.3):
        """Start bot typing indicator and apply function after delay"""
        self.set_busy(True)
        app_state.set_typing(True)
        self.on_refresh()
        
        def worker():
            if delay_sec > 0:
                time.sleep(delay_sec)
            
            def finish():
                app_state.set_typing(False)
                apply_fn()
                self.set_busy(False)
                self.on_refresh()
            
            _ui_safe(self.page, finish)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def handle_mood_selection(self, mood: str):
        """Handle mood chip click"""
        logger.info(f"Mood selected: {mood}")
        
        app_state.add_message("user", "text", f"Mood: {mood}")
        app_state.chat_flow["mood"] = mood
        app_state.record_mood_selection(mood)
        self.on_refresh()
        
        def apply():
            app_state.chat_flow["state"] = CHAT_STATE_AWAIT_INTENSITY
            app_state.add_message("bot", "text", "Bạn muốn mức độ nào? (Nhẹ / Vừa / Mạnh)")
        
        self.start_bot_reply(apply, delay_sec=0.5)
    
    def handle_intensity_selection(self, intensity: str):
        """Handle intensity chip click"""
        logger.info(f"Intensity selected: {intensity}")
        
        app_state.add_message("user", "text", f"Intensity: {intensity}")
        app_state.chat_flow["intensity"] = intensity
        app_state.chat_flow["state"] = "chatting"
        self.on_refresh()
        
        def apply():
            self.make_recommendation()
        
        self.start_bot_reply(apply, delay_sec=0.3)
    
    def make_recommendation(self, try_again: bool = False):
        """Generate and display recommendation with Top 3 songs"""
        import random
        
        mood = app_state.chat_flow["mood"] or "Chill"
        intensity = app_state.chat_flow["intensity"] or "Vừa"
        
        if try_again:
            all_intensities = ["Nhẹ", "Vừa", "Mạnh"]
            new_intensity = random.choice(all_intensities)
            while new_intensity == intensity:
                new_intensity = random.choice(all_intensities)
            intensity = new_intensity
            app_state.chat_flow["intensity"] = intensity
        
        # Get 3 different songs
        songs = []
        used_names = set()
        for _ in range(3):
            song = chat_service.pick_song(mood)
            song_name = song.get("name", "") if isinstance(song, dict) else ""
            if song_name not in used_names:
                songs.append(song)
                used_names.add(song_name)
        
        while len(songs) < 3:
            song = chat_service.pick_song(mood)
            song_name = song.get("name", "") if isinstance(song, dict) else ""
            if song_name not in used_names:
                songs.append(song)
                used_names.add(song_name)
        
        text = (
            f"Dựa trên cảm xúc và thể loại bạn chọn, đây là Top 3 bài hát phù hợp nhất cho bạn hôm nay:"
            if not try_again
            else f"Đây là gợi ý khác cho bạn (mood: {mood}, intensity: {intensity}):"
        )
        
        app_state.add_message("bot", "text", text)
        
        for song in songs:
            app_state.add_message("bot", "card", song=song)
            song_id = song.get("song_id") if isinstance(song, dict) else None
            chat_service.save_recommendation(song_id=song_id)
        
        app_state.chat_flow["state"] = CHAT_STATE_AWAIT_MOOD
        app_state.chat_flow["mood"] = None
        app_state.increment_recommendation_count()
    
    def handle_text_message(self, text: str):
        """Handle user text message with smart recommendation"""
        logger.info(f"Text message: {text[:50]}...")
        
        app_state.add_message("user", "text", text)
        self.on_refresh()
        
        st = app_state.chat_flow["state"]
        text_lower = text.lower()
        
        if st == CHAT_STATE_AWAIT_MOOD or st == "chatting":
            self._handle_smart_recommend(text)
            return
        
        if st == CHAT_STATE_AWAIT_INTENSITY:
            self._handle_intensity_text(text_lower)
            return
        
        # Default response
        def apply():
            app_state.add_message("bot", "text", 
                f"Mình đã nhận: \"{text}\". Nếu muốn đổi gợi ý, hãy chọn mood mới!")
        self.start_bot_reply(apply, delay_sec=0.3)
    
    def _handle_smart_recommend(self, text: str):
        """Call backend API for smart recommendation"""
        def apply():
            try:
                user_id = str(app_state.user_info.get("user_id", ""))
                response = api.moods.smart_recommend(text, user_id=user_id, limit=3)
                
                if response.is_success and response.data:
                    data = response.data
                    detected = data.get("detected_mood", {})
                    
                    mood_vi = detected.get("mood", "Chill")
                    intensity = detected.get("intensity", "Vừa")
                    confidence = detected.get("confidence", 0.5)
                    keywords = detected.get("keywords", [])
                    emoji = detected.get("emoji", "🎵")
                    songs = data.get("recommendations", [])
                    
                    app_state.chat_flow["mood"] = mood_vi
                    app_state.chat_flow["intensity"] = intensity
                    app_state.chat_flow["state"] = CHAT_STATE_AWAIT_MOOD
                    
                    if confidence >= settings.MIN_CONFIDENCE_THRESHOLD and songs:
                        keyword_text = f" (từ khóa: {', '.join(keywords[:3])})" if keywords else ""
                        app_state.add_message("bot", "text", 
                            f"{emoji} Mình nhận thấy bạn đang cảm thấy '{mood_vi}'{keyword_text}. "
                            f"Đây là Top {len(songs)} bài hát phù hợp cho bạn:")
                        
                        for song in songs:
                            normalized = chat_service._normalize_song(song)
                            if song.get("recommendation_reason"):
                                normalized["reason"] = song.get("recommendation_reason")
                            app_state.add_message("bot", "card", song=normalized)
                            chat_service.save_recommendation(song_id=song.get("song_id"))
                        
                        app_state.increment_recommendation_count()
                    else:
                        app_state.add_message("bot", "text", 
                            f"Mình chưa rõ lắm. Bạn có thể chọn mood bằng nút bên dưới hoặc mô tả rõ hơn nhé! 😊")
                else:
                    app_state.add_message("bot", "text", 
                        "Mình hiểu rồi! Bạn có thể chọn mood bằng nút bên dưới hoặc tiếp tục chia sẻ 😊")
            except Exception as ex:
                logger.error(f"Smart recommend error: {ex}")
                app_state.add_message("bot", "text", 
                    "Mình hiểu rồi! Bạn có thể chọn mood bằng nút bên dưới hoặc tiếp tục chia sẻ 😊")
        
        self.start_bot_reply(apply, delay_sec=0.5)
    
    def _handle_intensity_text(self, text_lower: str):
        """Handle intensity detection from text"""
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
            def apply():
                app_state.chat_flow["intensity"] = detected_intensity
                app_state.chat_flow["state"] = "chatting"
                self.make_recommendation()
            self.start_bot_reply(apply, delay_sec=0.3)
        else:
            def apply():
                app_state.add_message("bot", "text", "Hãy chọn intensity: Nhẹ, Vừa, hoặc Mạnh")
            self.start_bot_reply(apply, delay_sec=0.3)
    
    def reset_chat(self):
        """Reset chat to initial state"""
        logger.info("Resetting chat")
        app_state.reset_chat()
        app_state.add_message("bot", "text", settings.CHAT_WELCOME_MESSAGE)
    
    def bootstrap(self):
        """Initialize chat screen"""
        logger.info("Bootstrapping chat screen")
        app_state.set_typing(False)
        app_state.set_busy(False)
        
        if len(app_state.chat_messages) == 0:
            self.reset_chat()
        
        self.on_refresh()


def create_chat_screen(page: ft.Page, on_history_click, on_profile_click):
    """
    Create chat screen with clean architecture.
    
    Args:
        page: Flet page instance
        on_history_click: Callback for history navigation
        on_profile_click: Callback for profile navigation
        
    Returns:
        ft.Container with complete chat screen UI
    """
    logger.info("Creating chat screen")
    
    # UI Elements
    message_field = ft.TextField(
        hint_text="Nhập tin nhắn...",
        border=ft.InputBorder.NONE,
        bgcolor="transparent",
        hint_style=ft.TextStyle(color="#999999", size=14),
        text_style=ft.TextStyle(color=settings.TEXT_PRIMARY, size=14),
        expand=True,
    )
    
    messages_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=16)
    
    # Mood/Intensity sections (will be updated dynamically)
    mood_section = ft.Container(visible=True, margin=ft.margin.only(left=44, top=4, bottom=4))
    intensity_section = ft.Container(visible=False, margin=ft.margin.only(left=44, top=4, bottom=4))
    
    def refresh_messages():
        """Refresh the entire message display"""
        messages_list.controls.clear()
        
        # Date separator
        messages_list.controls.append(
            ft.Row([
                ft.Container(expand=True),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=16, vertical=6),
                    border_radius=16,
                    bgcolor="#E8E8E8",
                    content=ft.Text("Today", size=12, color=settings.TEXT_SECONDARY),
                ),
                ft.Container(expand=True),
            ])
        )
        
        # Render messages
        for msg in app_state.chat_messages:
            if msg["kind"] == "text":
                if msg["sender"] == "user":
                    messages_list.controls.append(create_user_message(msg["text"]))
                else:
                    messages_list.controls.append(create_bot_message(msg["text"]))
            elif msg["kind"] == "card":
                messages_list.controls.append(create_song_card(msg["song"]))
        
        # Update chip visibility
        current_state = app_state.chat_flow["state"]
        mood_section.visible = (current_state == CHAT_STATE_AWAIT_MOOD)
        intensity_section.visible = (current_state == CHAT_STATE_AWAIT_INTENSITY)
        
        # Rebuild mood chips with current handlers
        if mood_section.visible:
            mood_section.content = ft.Row([
                create_mood_chip("Vui", "😊", on_click=lambda e: controller.handle_mood_selection("Vui") if not app_state.chat_flow["busy"] else None),
                create_mood_chip("Buồn", "😢", on_click=lambda e: controller.handle_mood_selection("Buồn") if not app_state.chat_flow["busy"] else None),
                create_mood_chip("Năng động", "⚡", on_click=lambda e: controller.handle_mood_selection("Năng động") if not app_state.chat_flow["busy"] else None),
                create_mood_chip("Thư giãn", "🍃", on_click=lambda e: controller.handle_mood_selection("Thư giãn") if not app_state.chat_flow["busy"] else None),
                create_mood_chip("Tập trung", "🎯", on_click=lambda e: controller.handle_mood_selection("Tập trung") if not app_state.chat_flow["busy"] else None),
            ], spacing=6)
        
        if intensity_section.visible:
            intensity_section.content = ft.Row([
                create_intensity_chip("Nhẹ", "🌸", on_click=lambda e: controller.handle_intensity_selection("Nhẹ") if not app_state.chat_flow["busy"] else None),
                create_intensity_chip("Vừa", "🌿", on_click=lambda e: controller.handle_intensity_selection("Vừa") if not app_state.chat_flow["busy"] else None),
                create_intensity_chip("Mạnh", "🔥", on_click=lambda e: controller.handle_intensity_selection("Mạnh") if not app_state.chat_flow["busy"] else None),
            ], spacing=6)
        
        # Show typing indicator if active
        if app_state.typing_on["value"]:
            messages_list.controls.append(create_typing_indicator())
        
        # Update input field state
        message_field.disabled = app_state.chat_flow["busy"]
        
        page.update()
    
    # Create controller
    controller = ChatScreenController(page, refresh_messages)
    
    def send_message(e):
        """Handle send button click or enter key"""
        if app_state.chat_flow["busy"]:
            return
        
        text = (message_field.value or "").strip()
        if not text:
            return
        
        message_field.value = ""
        controller.handle_text_message(text)
    
    # Attach submit handler
    message_field.on_submit = send_message
    
    # Store bootstrap in state
    app_state.set_chat_bootstrap(controller.bootstrap)
    
    # Bootstrap immediately
    controller.bootstrap()
    
    # Helper: Create menu item
    def create_menu_item(icon: str, label: str, is_active: bool = False, on_click=None):
        return ft.Container(
            height=44,
            border_radius=8,
            bgcolor=settings.TEAL_PRIMARY if is_active else "transparent",
            padding=ft.padding.only(left=12),
            on_click=on_click,
            content=ft.Row([
                ft.Text(icon, size=16, color=settings.WHITE if is_active else settings.TEXT_SECONDARY),
                ft.Container(width=8),
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, 
                       color=settings.WHITE if is_active else settings.TEXT_PRIMARY),
            ], alignment=ft.MainAxisAlignment.START),
        )
    
    # Build complete layout
    return ft.Container(
        expand=True,
        bgcolor=settings.WHITE,
        content=ft.Row([
            # Sidebar
            ft.Container(
                width=180,
                bgcolor=settings.SIDEBAR_BG,
                border=ft.border.only(right=ft.BorderSide(1, settings.BORDER_COLOR)),
                padding=ft.padding.all(16),
                content=ft.Column([
                    # Logo
                    ft.Row([
                        ft.Container(
                            width=32,
                            height=32,
                            border_radius=16,
                            bgcolor=settings.TEAL_PRIMARY,
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text("♪", size=16, color=settings.WHITE),
                        ),
                        ft.Container(width=8),
                        ft.Column([
                            ft.Text("MusicMood", size=14, weight=ft.FontWeight.W_700, color=settings.TEXT_PRIMARY),
                            ft.Text("BOT", size=10, color=settings.TEXT_MUTED),
                        ], spacing=0),
                    ]),
                    ft.Container(height=8),
                    ft.Text("Menu", size=12, color=settings.TEXT_MUTED),
                    ft.Container(height=8),
                    create_menu_item("💬", "Đoạn chat", is_active=True),
                    ft.Container(height=4),
                    create_menu_item("🕐", "Lịch sử", on_click=lambda e: on_history_click()),
                    ft.Container(height=4),
                    create_menu_item("👤", "Hồ sơ", on_click=lambda e: on_profile_click()),
                    ft.Container(expand=True),
                    ft.Text("MUSICMOOD V2.0", size=10, color="#AAAAAA"),
                ]),
            ),
            # Main content
            ft.Container(
                expand=True,
                bgcolor=settings.CHAT_BG,
                content=ft.Column([
                    # Header
                    ft.Container(
                        height=60,
                        bgcolor=settings.WHITE,
                        border=ft.border.only(bottom=ft.BorderSide(1, settings.BORDER_COLOR)),
                        padding=ft.padding.symmetric(horizontal=24),
                        content=ft.Row([
                            ft.Row([
                                ft.Container(
                                    width=40,
                                    height=40,
                                    border_radius=20,
                                    bgcolor=settings.TEAL_PRIMARY,
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Text("🤖", size=20),
                                ),
                                ft.Container(width=12),
                                ft.Column([
                                    ft.Text("MusicMoodBot", size=16, weight=ft.FontWeight.W_600, color=settings.TEXT_PRIMARY),
                                    ft.Row([
                                        ft.Container(width=8, height=8, border_radius=4, bgcolor="#22C55E"),
                                        ft.Text(" Online", size=12, color=settings.TEXT_MUTED),
                                    ], spacing=0),
                                ], spacing=2),
                            ]),
                            ft.Row([
                                ft.IconButton(icon=ft.Icons.REFRESH, icon_color=settings.TEXT_SECONDARY, icon_size=20,
                                            on_click=lambda e: (controller.reset_chat(), refresh_messages())),
                                ft.Container(
                                    width=36,
                                    height=36,
                                    border_radius=18,
                                    bgcolor="#E0E0E0",
                                    alignment=ft.Alignment(0, 0),
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
                        bgcolor=settings.WHITE,
                        border=ft.border.only(top=ft.BorderSide(1, settings.BORDER_COLOR)),
                        padding=ft.padding.symmetric(horizontal=24, vertical=12),
                        content=ft.Row([
                            ft.Container(
                                width=40,
                                height=40,
                                border_radius=20,
                                bgcolor="#F0F0F0",
                                alignment=ft.Alignment(0, 0),
                                content=ft.Text("➕", size=18),
                            ),
                            ft.Container(width=12),
                            ft.Container(
                                expand=True,
                                height=44,
                                border_radius=22,
                                bgcolor="#F5F5F5",
                                border=ft.border.all(1, settings.BORDER_COLOR),
                                padding=ft.padding.only(left=20, right=12),
                                content=ft.Row([
                                    ft.Container(expand=True, content=message_field),
                                ]),
                            ),
                            ft.Container(width=12),
                            ft.Container(
                                width=70,
                                height=44,
                                border_radius=22,
                                bgcolor=settings.TEAL_PRIMARY,
                                alignment=ft.Alignment(0, 0),
                                on_click=send_message,
                                content=ft.Row([
                                    ft.Text("Gửi", size=14, weight=ft.FontWeight.W_600, color=settings.WHITE),
                                    ft.Text(" ➤", size=14, color=settings.WHITE),
                                ], alignment=ft.MainAxisAlignment.CENTER),
                            ),
                        ]),
                    ),
                    # Footer
                    ft.Container(
                        height=28,
                        bgcolor=settings.WHITE,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text("CDIO PROJECT • REFACTORED V2", size=10, color="#CCCCCC"),
                    ),
                ], spacing=0),
            ),
        ], spacing=0),
    )
