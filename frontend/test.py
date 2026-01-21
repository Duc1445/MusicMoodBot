import flet as ft
import random
import threading
import time

COLORS = {
    "cream_bg": "#F6F3EA",
    "white": "#FFFFFF",
    "border_dark": "#111111",
    "button_dark": "#2F2F2F",
    "accent_teal": "#3FB5B3",
    "text_gray": "#6B6B6B",
    "online_green": "#2ECC71",
    "mood_sad": "#BFD7FF",
    "mood_think": "#D7C7FF",
    "mood_happy": "#BFEFC9",
    "date_yellow": "#F6D25C",
    "light_gray": "#EFEFEF",
}

# ================== STATE (GLOBAL) ==================
chat_messages = []  # {"sender":"user"/"bot","kind":"text"/"card","text":str,"song":dict}
user_info = {"name": "", "email": ""}

chat_flow = {
    "state": "await_mood",  # await_mood | await_other_mood | await_intensity | chatting
    "mood": None,
    "intensity": None,
    "busy": False,
}

# defer init after page.update()
_CHAT_BOOTSTRAP = None

SAMPLE_SONGS = [
    {"name": "Mưa Tháng Sáu", "artist": "Văn Mai Hương", "genre": "Ballad", "suy_score": 8.8,
     "reason": "Giai điệu chậm, vocal mềm, hợp mood trầm.", "moods": ["Buồn", "Suy tư"]},
    {"name": "Có Chàng Trai Viết Lên Cây", "artist": "Phan Mạnh Quỳnh", "genre": "Ballad", "suy_score": 7.2,
     "reason": "Nostalgia nhẹ, hợp khi cần thả cảm xúc.", "moods": ["Buồn", "Chill"]},
    {"name": "Ngày Chưa Giông Bão", "artist": "Bùi Lan Hương", "genre": "Indie/Pop", "suy_score": 7.9,
     "reason": "Không khí suy tư, cinematic, hợp tập trung.", "moods": ["Suy tư", "Chill"]},
    {"name": "Cô Gái M52", "artist": "HuyR x Tùng Viu", "genre": "Pop", "suy_score": 2.5,
     "reason": "Nhịp vui, bắt tai, hợp mood tích cực.", "moods": ["Vui", "Năng lượng"]},
    {"name": "Bước Qua Nhau", "artist": "Vũ.", "genre": "Indie", "suy_score": 6.9,
     "reason": "Chill nhẹ, hợp nghe đêm, không quá nặng.", "moods": ["Chill", "Suy tư"]},
    {"name": "Nơi Này Có Anh", "artist": "Sơn Tùng M-TP", "genre": "Pop", "suy_score": 3.8,
     "reason": "Tươi sáng, lời tích cực, hợp tâm trạng vui.", "moods": ["Vui"]},
]

MOOD_CHIPS = ["Vui", "Buồn", "Suy tư", "Chill", "Năng lượng", "Other"]
INTENSITY_CHIPS = ["Nhẹ", "Vừa", "Mạnh"]


def create_login_screen(on_signup_click, on_login_submit):
    email_field = ft.TextField(hint_text="user123", border=ft.InputBorder.OUTLINE, width=300)
    password_field = ft.TextField(hint_text="password", password=True, border=ft.InputBorder.OUTLINE, width=300)
    error_text = ft.Text("", size=11, color="red")

    def handle_login(e):
        if not email_field.value.strip():
            error_text.value = "Vui lòng nhập email/username!"
            error_text.update()
            return
        if not password_field.value.strip():
            error_text.value = "Vui lòng nhập mật khẩu!"
            error_text.update()
            return
        error_text.value = ""
        user_info["name"] = email_field.value
        user_info["email"] = email_field.value
        on_login_submit()

    return ft.Container(
        bgcolor=COLORS["cream_bg"],
        expand=True,
        padding=40,
        content=ft.Column([
            ft.Text("MUSICMOOD BOT", size=24, weight="bold"),
            ft.Text("Đăng Nhập", size=16),
            ft.Container(height=20),
            ft.Text("Email/Username", size=12, weight="bold"),
            email_field,
            ft.Container(height=12),
            ft.Text("Mật khẩu", size=12, weight="bold"),
            password_field,
            ft.Container(height=12),
            error_text,
            ft.Container(height=8),
            ft.Button("LOGIN →", width=300, height=40, on_click=handle_login),
            ft.Container(height=12),
            ft.Row([
                ft.Text("Chưa có tài khoản? ", size=11),
                ft.TextButton("Đăng ký", on_click=on_signup_click),
            ]),
            ft.Container(expand=True),
            ft.Text("v1.0.0 | Online", size=10),
        ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


def create_signup_screen(on_login_click, on_signup_submit):
    name_field = ft.TextField(hint_text="Nguyễn Văn A", border=ft.InputBorder.OUTLINE, width=300)
    email_field = ft.TextField(hint_text="user@example.com", border=ft.InputBorder.OUTLINE, width=300)
    password_field = ft.TextField(hint_text="", password=True, border=ft.InputBorder.OUTLINE, width=300)
    confirm_field = ft.TextField(hint_text="", password=True, border=ft.InputBorder.OUTLINE, width=300)
    error_text = ft.Text("", size=11, color="red")

    def handle_signup(e):
        if not name_field.value.strip():
            error_text.value = "Vui lòng nhập họ và tên!"
            error_text.update()
            return
        if not email_field.value.strip():
            error_text.value = "Vui lòng nhập email!"
            error_text.update()
            return
        if not password_field.value.strip():
            error_text.value = "Vui lòng nhập mật khẩu!"
            error_text.update()
            return
        if password_field.value != confirm_field.value:
            error_text.value = "Mật khẩu không khớp!"
            error_text.update()
            return
        error_text.value = ""
        user_info["name"] = name_field.value
        user_info["email"] = email_field.value
        on_signup_submit()

    return ft.Container(
        bgcolor=COLORS["white"],
        expand=True,
        padding=40,
        content=ft.Column([
            ft.Text("MUSICMOOD BOT", size=24, weight="bold"),
            ft.Text("Đăng Ký", size=16),
            ft.Container(height=20),
            ft.Text("Họ và tên", size=12, weight="bold"),
            name_field,
            ft.Container(height=12),
            ft.Text("Email", size=12, weight="bold"),
            email_field,
            ft.Container(height=12),
            ft.Text("Mật khẩu", size=12, weight="bold"),
            password_field,
            ft.Container(height=12),
            ft.Text("Nhập lại mật khẩu", size=12, weight="bold"),
            confirm_field,
            ft.Container(height=12),
            error_text,
            ft.Container(height=8),
            ft.Button("ĐĂNG KÝ", width=300, height=40, on_click=handle_signup),
            ft.Container(height=12),
            ft.Row([
                ft.Text("Đã có tài khoản? ", size=11),
                ft.TextButton("Đăng nhập", on_click=on_login_click),
            ]),
            ft.Container(height=12),
            ft.TextButton("← Quay lại", on_click=on_login_click),
            ft.Container(expand=True),
        ], alignment=ft.MainAxisAlignment.START, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )


# -------- compatibility helpers --------
def _make_chip_layout(spacing=8, run_spacing=8):
    if hasattr(ft, "Wrap"):
        return ft.Wrap(spacing=spacing, run_spacing=run_spacing)
    try:
        return ft.Row(spacing=spacing, wrap=True, run_spacing=run_spacing)
    except TypeError:
        return ft.Row(spacing=spacing, scroll=ft.ScrollMode.AUTO)


def _make_progress():
    if hasattr(ft, "ProgressRing"):
        return ft.ProgressRing(width=16, height=16, stroke_width=2)
    return ft.ProgressBar(width=80)


def _ui_safe(page: ft.Page, fn):
    if hasattr(page, "call_from_thread"):
        page.call_from_thread(fn)
        return
    if hasattr(page, "invoke_later"):
        page.invoke_later(fn)
        return
    if hasattr(page, "run_task"):
        async def _t():
            fn()
        page.run_task(_t)
        return
    fn()


def create_chat_screen(page: ft.Page, on_history_click, on_profile_click):
    global _CHAT_BOOTSTRAP

    message_field = ft.TextField(hint_text="Nhập tin nhắn…", border=ft.InputBorder.UNDERLINE, expand=True)
    send_btn = ft.Button("Gửi", width=80)
    messages_list = ft.Column(scroll=ft.ScrollMode.AUTO)

    other_mood_field = ft.TextField(hint_text="Nhập mood của bạn…", expand=True)
    other_confirm_btn = ft.Button("OK", width=70)
    other_row = ft.Row([other_mood_field, other_confirm_btn], visible=False)

    chips_title = ft.Text("", size=10, weight="bold")
    chips_wrap = _make_chip_layout(spacing=8, run_spacing=8)
    chips_section = ft.Column([chips_title, ft.Container(height=6), chips_wrap, ft.Container(height=8), other_row])

    typing_on = {"value": False}

    def set_busy(is_busy: bool):
        chat_flow["busy"] = is_busy
        message_field.disabled = is_busy
        send_btn.disabled = is_busy
        # chỉ gọi page.update() (an toàn hơn control.update)
        page.update()

    def add_msg(sender: str, kind: str = "text", text: str = "", song: dict = None):
        chat_messages.append({"sender": sender, "kind": kind, "text": text, "song": song})

    def bubble_for_text(sender: str, text: str):
        is_user = sender == "user"
        bg = COLORS["accent_teal"] if is_user else COLORS["light_gray"]
        fg = COLORS["white"] if is_user else COLORS["border_dark"]
        align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START

        return ft.Row(
            alignment=align,
            controls=[
                ft.Container(
                    content=ft.Text(text, color=fg, size=11),
                    bgcolor=bg,
                    padding=12,
                    border_radius=12,
                    width=520,
                )
            ]
        )

    def build_song_card(song: dict):
        def on_try_again(e):
            if chat_flow["busy"]:
                return
            start_bot_reply(make_recommendation_reply(try_again=True), delay_sec=1.0)

        return ft.Container(
            width=520,
            bgcolor=COLORS["white"],
            padding=16,
            border_radius=16,
            border=ft.Border(
                left=ft.BorderSide(1, COLORS["border_dark"]),
                top=ft.BorderSide(1, COLORS["border_dark"]),
                right=ft.BorderSide(1, COLORS["border_dark"]),
                bottom=ft.BorderSide(1, COLORS["border_dark"]),
            ),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text("🎵 Recommendation", size=12, weight="bold"),
                    ft.Text(song["name"], size=14, weight="bold"),
                    ft.Text(f"Artist: {song['artist']}", size=11),
                    ft.Text(f"Genre: {song['genre']}", size=11),
                    ft.Text(f"Suy Score: {song['suy_score']}/10", size=11),
                    ft.Text(f"Reason: {song['reason']}", size=11, color=COLORS["text_gray"]),
                    ft.Container(height=6),
                    ft.Row([ft.Button("Try again", on_click=on_try_again)], alignment=ft.MainAxisAlignment.END),
                ],
            ),
        )

    def refresh_messages():
        messages_list.controls.clear()

        for msg in chat_messages:
            if msg["kind"] == "text":
                messages_list.controls.append(bubble_for_text(msg["sender"], msg["text"]))
            elif msg["kind"] == "card":
                messages_list.controls.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.START,
                        controls=[build_song_card(msg["song"])],
                    )
                )

        if typing_on["value"]:
            messages_list.controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    controls=[
                        ft.Container(
                            width=220,
                            bgcolor=COLORS["light_gray"],
                            padding=12,
                            border_radius=12,
                            content=ft.Row(
                                spacing=10,
                                controls=[_make_progress(), ft.Text("Bot đang nhập...", size=11)],
                            ),
                        )
                    ],
                )
            )

        page.update()

    def make_chip(label: str, selected: bool, on_click):
        bg = COLORS["button_dark"] if selected else COLORS["white"]
        fg = COLORS["white"] if selected else COLORS["border_dark"]
        border_color = COLORS["button_dark"] if selected else COLORS["border_dark"]

        base = ft.Container(
            padding=ft.Padding(12, 6, 12, 6),
            bgcolor=bg,
            border_radius=18,
            border=ft.Border(
                left=ft.BorderSide(1, border_color),
                top=ft.BorderSide(1, border_color),
                right=ft.BorderSide(1, border_color),
                bottom=ft.BorderSide(1, border_color),
            ),
            content=ft.Text(label, size=11, color=fg),
        )

        # tương thích: ưu tiên GestureDetector, fallback Container(on_click)
        if hasattr(ft, "GestureDetector"):
            return ft.GestureDetector(on_tap=on_click, content=base)
        try:
            base.on_click = on_click
        except Exception:
            pass
        return base

    def render_chips():
        chips_wrap.controls.clear()
        st = chat_flow["state"]

        if st in ("await_mood", "await_other_mood"):
            chips_title.value = "Chọn cảm xúc (chip):"
            for label in MOOD_CHIPS:
                selected = (chat_flow["mood"] == label)

                def _handler_factory(lb):
                    def _h(e):
                        if chat_flow["busy"]:
                            return
                        handle_mood_chip(lb)
                    return _h

                chips_wrap.controls.append(make_chip(label, selected, _handler_factory(label)))

            other_row.visible = (st == "await_other_mood")

        elif st == "await_intensity":
            chips_title.value = "Chọn intensity (chip):"
            for label in INTENSITY_CHIPS:
                selected = (chat_flow["intensity"] == label)

                def _handler_factory(lb):
                    def _h(e):
                        if chat_flow["busy"]:
                            return
                        handle_intensity_chip(lb)
                    return _h

                chips_wrap.controls.append(make_chip(label, selected, _handler_factory(label)))

            other_row.visible = False

        else:
            chips_title.value = "Tùy chọn nhanh:"

            def quick_change_mood(e):
                if chat_flow["busy"]:
                    return
                chat_flow["state"] = "await_mood"
                chat_flow["mood"] = None
                chat_flow["intensity"] = None
                add_msg("bot", "text", "Bạn muốn đổi mood? Chọn 1 chip bên dưới.")
                refresh_messages()
                render_chips()

            def quick_reset(e):
                if chat_flow["busy"]:
                    return
                reset_chat()

            chips_wrap.controls.append(make_chip("Đổi mood", False, quick_change_mood))
            chips_wrap.controls.append(make_chip("Reset chat", False, quick_reset))
            other_row.visible = False

        page.update()

    def pick_song(mood: str):
        if not mood:
            return random.choice(SAMPLE_SONGS)
        candidates = [s for s in SAMPLE_SONGS if mood in s.get("moods", [])]
        return random.choice(candidates) if candidates else random.choice(SAMPLE_SONGS)

    def make_recommendation_reply(try_again: bool = False):
        mood = chat_flow["mood"] if chat_flow["mood"] else "Chill"
        intensity = chat_flow["intensity"] if chat_flow["intensity"] else "Vừa"
        song = pick_song(mood)

        text = (
            f"Ok, mình thử bài khác (mood: {mood}, intensity: {intensity}) nhé."
            if try_again
            else f"Mình đã hiểu (mood: {mood}, intensity: {intensity}). Đây là gợi ý phù hợp:"
        )

        def _apply():
            add_msg("bot", "text", text)
            add_msg("bot", "card", song=song)
            chat_flow["state"] = "chatting"
            refresh_messages()
            render_chips()

        return _apply

    def start_bot_reply(apply_fn, delay_sec: float = 1.0):
        set_busy(True)
        typing_on["value"] = True
        refresh_messages()

        def worker():
            time.sleep(delay_sec)

            def finish():
                typing_on["value"] = False
                refresh_messages()
                apply_fn()
                set_busy(False)

            _ui_safe(page, finish)

        threading.Thread(target=worker, daemon=True).start()

    def handle_mood_chip(label: str):
        chat_flow["mood"] = label

        if label == "Other":
            chat_flow["state"] = "await_other_mood"
            other_mood_field.value = ""
            add_msg("user", "text", "🧩 Mood: Other")
            add_msg("bot", "text", "Bạn nhập mood khác vào ô bên dưới rồi bấm OK.")
            refresh_messages()
            render_chips()
            return

        emoji = "😊" if label == "Vui" else ("😢" if label == "Buồn" else "🧠")
        add_msg("user", "text", f"{emoji} Mood: {label}")

        chat_flow["state"] = "await_intensity"
        refresh_messages()
        render_chips()

        def apply():
            add_msg("bot", "text", "Ok. Bạn muốn intensity mức nào? (Nhẹ / Vừa / Mạnh)")
            refresh_messages()
            render_chips()

        start_bot_reply(apply, delay_sec=0.8)

    def handle_intensity_chip(label: str):
        chat_flow["intensity"] = label
        flame = "🔥" if label == "Mạnh" else ("✨" if label == "Vừa" else "🌿")
        add_msg("user", "text", f"{flame} Intensity: {label}")
        refresh_messages()
        render_chips()
        start_bot_reply(make_recommendation_reply(try_again=False), delay_sec=1.0)

    def handle_other_confirm(e):
        if chat_flow["busy"]:
            return
        val = (other_mood_field.value or "").strip()
        if not val:
            add_msg("bot", "text", "Mood 'Other' chưa có nội dung. Bạn nhập lại giúp mình.")
            refresh_messages()
            return

        chat_flow["mood"] = val
        chat_flow["state"] = "await_intensity"
        add_msg("user", "text", f"🧩 Mood (Other): {val}")

        other_row.visible = False
        refresh_messages()
        render_chips()

        def apply():
            add_msg("bot", "text", "Ok. Bạn muốn intensity mức nào? (Nhẹ / Vừa / Mạnh)")
            refresh_messages()
            render_chips()

        start_bot_reply(apply, delay_sec=0.8)

    other_confirm_btn.on_click = handle_other_confirm

    def handle_fallback_message():
        st = chat_flow["state"]
        if st in ("await_mood", "await_other_mood"):
            add_msg("bot", "text", "Mình chưa hiểu ý bạn. Hãy chọn 1 mood bằng chip bên dưới (hoặc chọn Other).")
        elif st == "await_intensity":
            add_msg("bot", "text", "Bạn chọn intensity bằng chip: Nhẹ / Vừa / Mạnh nhé.")
        else:
            add_msg("bot", "text", "Bạn có thể bấm 'Đổi mood' để chọn lại, hoặc 'Reset chat' để làm mới.")
        refresh_messages()

    def send_message(e):
        if chat_flow["busy"]:
            return
        text = (message_field.value or "").strip()
        if not text:
            return

        add_msg("user", "text", text)
        message_field.value = ""
        page.update()

        st = chat_flow["state"]
        refresh_messages()

        if st in ("await_mood", "await_other_mood", "await_intensity"):
            start_bot_reply(handle_fallback_message, delay_sec=0.8)
            return

        def apply():
            add_msg("bot", "text", f"Mình đã nhận: “{text}”. Nếu muốn đổi gợi ý, bấm 'Try again' hoặc 'Đổi mood'.")
            refresh_messages()
            render_chips()

        start_bot_reply(apply, delay_sec=0.8)

    send_btn.on_click = send_message
    message_field.on_submit = send_message

    def reset_chat():
        chat_messages.clear()
        chat_flow["state"] = "await_mood"
        chat_flow["mood"] = None
        chat_flow["intensity"] = None
        typing_on["value"] = False
        chat_flow["busy"] = False
        message_field.disabled = False
        send_btn.disabled = False

        add_msg("bot", "text", "Chào bạn. Hôm nay bạn cảm thấy thế nào? Chọn mood bằng chip bên dưới.")
        refresh_messages()
        render_chips()

    def on_emotion_click(emotion):
        def handler(e):
            if chat_flow["busy"]:
                return
            if chat_flow["state"] in ("await_mood", "await_other_mood"):
                handle_mood_chip("Vui" if emotion == "Vui" else "Buồn")
            else:
                add_msg("user", "text", f"{'😊' if emotion=='Vui' else '😢'} Cảm xúc: {emotion}")
                refresh_messages()
        return handler

    def on_reset_click(e):
        if chat_flow["busy"]:
            return
        reset_chat()

    # ---- IMPORTANT: do NOT init here (screen not mounted yet)
    def bootstrap_after_mounted():
        if len(chat_messages) == 0:
            reset_chat()
        else:
            refresh_messages()
            render_chips()

    _CHAT_BOOTSTRAP = bootstrap_after_mounted

    return ft.Container(
        expand=True,
        content=ft.Row([
            ft.Container(
                width=200,
                bgcolor=COLORS["light_gray"],
                padding=20,
                border=ft.Border(right=ft.BorderSide(2, COLORS["border_dark"])),
                content=ft.Column([
                    ft.Text("Menu", size=14, weight="bold"),
                    ft.Divider(height=2, color=COLORS["border_dark"]),
                    ft.Button("💬 Chat", width=180),
                    ft.Container(height=8),
                    ft.Button("📋 Lịch sử", width=180, on_click=on_history_click),
                    ft.Container(height=8),
                    ft.Button("👤 Hồ sơ", width=180, on_click=on_profile_click),
                    ft.Container(height=8),
                    ft.Button("🧹 Reset", width=180, on_click=on_reset_click),
                    ft.Container(expand=True),
                    ft.Text("MUSICMOOD v1.0", size=9),
                ])
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column([
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("MusicMoodBot", size=16, weight="bold"),
                            ft.Button("Reset chat", on_click=on_reset_click),
                        ],
                    ),
                    ft.Divider(height=2, color=COLORS["border_dark"]),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Text("Hôm nay", size=10, weight="bold", color=COLORS["white"]),
                        bgcolor=COLORS["button_dark"],
                        padding=ft.Padding(12, 4, 12, 4),
                        border_radius=20,
                    ),
                    ft.Container(height=12),

                    ft.Container(expand=True, content=messages_list),

                    ft.Container(height=10),
                    ft.Container(
                        bgcolor=COLORS["white"],
                        padding=12,
                        border_radius=12,
                        border=ft.Border(
                            left=ft.BorderSide(1, COLORS["border_dark"]),
                            top=ft.BorderSide(1, COLORS["border_dark"]),
                            right=ft.BorderSide(1, COLORS["border_dark"]),
                            bottom=ft.BorderSide(1, COLORS["border_dark"]),
                        ),
                        content=chips_section,
                    ),

                    ft.Container(height=12),
                    ft.Row([
                        ft.Button("😊 Vui", width=140, on_click=on_emotion_click("Vui")),
                        ft.Button("😢 Buồn", width=140, on_click=on_emotion_click("Buồn")),
                    ]),

                    ft.Container(height=12),
                    ft.Text("CDIO PROJECT • VARIANT 1", size=8),
                    ft.Container(height=8),

                    ft.Row([message_field, send_btn]),
                ])
            ),
        ])
    )


def create_profile_screen(on_chat_click):
    return ft.Container(
        expand=True,
        content=ft.Row([
            ft.Container(
                width=200,
                bgcolor=COLORS["light_gray"],
                padding=20,
                border=ft.Border(right=ft.BorderSide(2, COLORS["border_dark"])),
                content=ft.Column([
                    ft.Text("Menu", size=14, weight="bold"),
                    ft.Divider(height=2, color=COLORS["border_dark"]),
                    ft.Button("💬 Chat", width=180, on_click=on_chat_click),
                    ft.Container(height=8),
                    ft.Button("📋 Lịch sử", width=180),
                    ft.Container(height=8),
                    ft.Button("👤 Hồ sơ", width=180),
                    ft.Container(expand=True),
                    ft.Text("MUSICMOOD v1.0", size=9),
                ])
            ),
            ft.Container(
                expand=True,
                padding=40,
                content=ft.Column([
                    ft.Text("👤 Hồ Sơ Của Bạn", size=24, weight="bold"),
                    ft.Container(height=20),
                    ft.Container(
                        bgcolor=COLORS["light_gray"],
                        padding=20,
                        border_radius=12,
                        content=ft.Column([
                            ft.Text("Họ và tên", size=12, weight="bold"),
                            ft.Text(user_info["name"] if user_info["name"] else "Nguyễn Văn A", size=14),
                            ft.Container(height=16),
                            ft.Text("📧 Email", size=12, weight="bold"),
                            ft.Text(user_info["email"] if user_info["email"] else "user@example.com", size=14),
                            ft.Container(height=16),
                            ft.Text("📅 Ngày đăng ký", size=12, weight="bold"),
                            ft.Text("19/01/2026", size=14),
                            ft.Container(height=20),
                            ft.Divider(height=1, color=COLORS["border_dark"]),
                            ft.Container(height=20),
                            ft.Text("📊 Thống kê", size=12, weight="bold"),
                            ft.Text("• Tổng bài hát đã nghe: 42", size=11),
                            ft.Text("• Cảm xúc yêu thích: Vui 😊", size=11),
                            ft.Text("• Nghệ sĩ yêu thích: Đại Mỉ", size=11),
                        ])
                    ),
                    ft.Container(expand=True),
                    ft.Button("Đăng xuất", width=300, height=40),
                ])
            ),
        ])
    )


def create_history_screen(on_chat_click):
    return ft.Container(
        expand=True,
        content=ft.Row([
            ft.Container(
                width=200,
                bgcolor=COLORS["light_gray"],
                padding=20,
                border=ft.Border(right=ft.BorderSide(2, COLORS["border_dark"])),
                content=ft.Column([
                    ft.Text("MusicMood\nBOT", size=12, weight="bold", text_align="center"),
                    ft.Divider(height=2, color=COLORS["border_dark"]),
                    ft.Button("💬 Chat", width=180, on_click=on_chat_click),
                    ft.Container(height=8),
                    ft.Button("📋 Lịch sử", width=180),
                    ft.Container(expand=True),
                    ft.Button("⚙️ Cài đặt", width=180),
                ])
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column([
                    ft.Text("Lịch sử nghe nhạc", size=18, weight="bold"),
                    ft.Text("Xem lại hành trình cảm xúc và gợi ý âm nhạc từ MusicMood Bot.", size=10),
                ])
            ),
        ])
    )


def main(page: ft.Page):
    global _CHAT_BOOTSTRAP

    page.title = "MusicMood Bot"
    page.window_width = 1440
    page.window_height = 900
    page.padding = 0

    content_area = ft.Container(expand=True)

    def show_login(e=None):
        global chat_messages
        chat_messages = []
        chat_flow["state"] = "await_mood"
        chat_flow["mood"] = None
        chat_flow["intensity"] = None
        chat_flow["busy"] = False
        content_area.content = create_login_screen(on_signup_click=show_signup, on_login_submit=show_chat)
        page.update()

    def show_signup(e=None):
        content_area.content = create_signup_screen(on_login_click=show_login, on_signup_submit=show_chat)
        page.update()

    def show_chat(e=None):
        global _CHAT_BOOTSTRAP
        _CHAT_BOOTSTRAP = None
        content_area.content = create_chat_screen(page, on_history_click=show_history, on_profile_click=show_profile)
        page.update()
        # init AFTER mounted
        if _CHAT_BOOTSTRAP:
            _CHAT_BOOTSTRAP()

    def show_history(e=None):
        content_area.content = create_history_screen(on_chat_click=show_chat)
        page.update()

    def show_profile(e=None):
        content_area.content = create_profile_screen(on_chat_click=show_chat)
        page.update()

    show_login()
    page.add(content_area)


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(main)