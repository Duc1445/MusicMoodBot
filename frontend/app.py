import flet as ft

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

chat_messages = []
user_info = {"name": "", "email": ""}

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

def create_chat_screen(on_history_click, on_profile_click):
    message_field = ft.TextField(hint_text="Nhập tin nhắn…", border=ft.InputBorder.UNDERLINE, expand=True)
    messages_list = ft.Column(scroll=ft.ScrollMode.AUTO)
    
    def refresh_messages():
        messages_list.controls.clear()
        for msg in chat_messages:
            if msg["sender"] == "user":
                messages_list.controls.append(
                    ft.Container(
                        content=ft.Text(msg["text"], color=COLORS["white"], size=11),
                        bgcolor=COLORS["accent_teal"],
                        padding=12,
                        border_radius=12,
                    )
                )
            else:
                messages_list.controls.append(
                    ft.Container(
                        content=ft.Text(msg["text"], size=11),
                        bgcolor=COLORS["light_gray"],
                        padding=12,
                        border_radius=12,
                    )
                )
        messages_list.update()
    
    def send_message(e):
        if message_field.value.strip():
            chat_messages.append({"sender": "user", "text": message_field.value})
            chat_messages.append({"sender": "bot", "text": f"🤖 MusicMood: Bạn vừa nói: '{message_field.value}'\n\n🎵 Đang tìm bài hát phù hợp với bạn..."})
            message_field.value = ""
            refresh_messages()
    
    def on_emotion_click(emotion):
        def handler(e):
            emoji = "😊" if emotion == "Vui" else "😢"
            chat_messages.append({"sender": "user", "text": f"{emoji} Cảm xúc: {emotion}"})
            chat_messages.append({"sender": "bot", "text": f"🤖 MusicMood: Tuyệt vời! Tôi sẽ giới thiệu nhạc {emotion.lower()} cho bạn.\n\n🎵 Gợi ý: 'Có chàng trai viết lên cây' - Nguyễn Hương\n\n📊 Thích nhất: 32% người nghe thích bài này"})
            refresh_messages()
        return handler
    
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
                    ft.Container(expand=True),
                    ft.Text("MUSICMOOD v1.0", size=9),
                ])
            ),
            ft.Container(
                expand=True,
                padding=20,
                content=ft.Column([
                    ft.Text("MusicMoodBot", size=16, weight="bold"),
                    ft.Divider(height=2, color=COLORS["border_dark"]),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Text("Hôm nay", size=10, weight="bold", color=COLORS["white"]),
                        bgcolor=COLORS["button_dark"],
                        padding=ft.Padding(12, 4, 12, 4),
                        border_radius=20,
                    ),
                    ft.Container(height=16),
                    ft.Container(expand=True, content=messages_list),
                    ft.Container(height=12),
                    ft.Row([
                        ft.Button("😊 Vui", width=140, on_click=on_emotion_click("Vui")),
                        ft.Button("😢 Buồn", width=140, on_click=on_emotion_click("Buồn")),
                    ]),
                    ft.Container(height=12),
                    ft.Text("CDIO PROJECT • VARIANT 1", size=8),
                    ft.Container(height=8),
                    ft.Row([
                        message_field,
                        ft.Button("Gửi", on_click=send_message, width=80),
                    ])
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
                    ft.Row([
                        ft.Container(
                            content=ft.Text("ARCHIVE", size=10, weight="bold", color=COLORS["white"]),
                            bgcolor=COLORS["button_dark"],
                            padding=ft.Padding(10, 4, 10, 4),
                            border_radius=20,
                        ),
                        ft.Text("Tháng 10, 2023", size=11, weight="bold"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text("Lịch sử nghe nhạc", size=18, weight="bold"),
                    ft.Text("Xem lại hành trình cảm xúc và gợi ý âm nhạc từ MusicMood Bot.", size=10),
                    ft.Container(height=12),
                    ft.Container(
                        bgcolor=COLORS["light_gray"],
                        padding=12,
                        border_radius=12,
                        content=ft.Column([
                            ft.Text("Lọc theo cảm xúc:", size=11, weight="bold"),
                            ft.Container(height=6),
                            ft.Row([
                                ft.Button("Tất cả", width=80),
                                ft.Button("Vui", width=80),
                                ft.Button("Buồn", width=80),
                            ]),
                        ])
                    ),
                    ft.Container(height=16),
                    ft.Container(
                        bgcolor=COLORS["light_gray"],
                        padding=12,
                        border_radius=12,
                        content=ft.Column([
                            ft.Row([
                                ft.Container(width=60, height=60, bgcolor=COLORS["text_gray"], border_radius=8),
                                ft.Column([
                                    ft.Container(content=ft.Text("BUỒN • 14:30 PM", size=9, weight="bold"), bgcolor=COLORS["mood_sad"], padding=ft.Padding(8, 3, 8, 3), border_radius=8),
                                    ft.Text("Mưa Tháng Sáu", size=11, weight="bold"),
                                    ft.Text("Văn Mai Hương", size=10),
                                    ft.TextButton("Chi tiết đề xuất →", icon="arrow_forward"),
                                ], expand=True),
                                ft.Column([
                                    ft.Icon("delete"),
                                    ft.Container(content=ft.Text("20/10/2023", size=9), bgcolor=COLORS["date_yellow"], padding=ft.Padding(6, 3, 6, 3), border_radius=6),
                                ]),
                            ]),
                        ])
                    ),
                    ft.Container(height=12),
                    ft.Container(
                        bgcolor=COLORS["light_gray"],
                        padding=12,
                        border_radius=12,
                        content=ft.Column([
                            ft.Row([
                                ft.Container(width=60, height=60, bgcolor=COLORS["text_gray"], border_radius=8),
                                ft.Column([
                                    ft.Container(content=ft.Text("SUY TƯ • 20:15 PM", size=9, weight="bold"), bgcolor=COLORS["mood_think"], padding=ft.Padding(8, 3, 8, 3), border_radius=8),
                                    ft.Text("Ngày Chưa Giông Bão", size=11, weight="bold"),
                                    ft.Text("Bùi Lan Hương", size=10),
                                    ft.TextButton("Chi tiết đề xuất →", icon="arrow_forward"),
                                ], expand=True),
                                ft.Column([
                                    ft.Icon("delete"),
                                    ft.Container(content=ft.Text("19/10/2023", size=9), bgcolor=COLORS["light_gray"], padding=ft.Padding(6, 3, 6, 3), border_radius=6),
                                ]),
                            ]),
                        ])
                    ),
                ])
            ),
        ])
    )

def main(page: ft.Page):
    page.title = "MusicMood Bot"
    page.window_width = 1440
    page.window_height = 900
    page.padding = 0
    
    content_area = ft.Container(expand=True)
    
    def show_login(e=None):
        global chat_messages
        chat_messages = []
        content_area.content = create_login_screen(on_signup_click=show_signup, on_login_submit=show_chat)
        page.update()
    
    def show_signup(e=None):
        content_area.content = create_signup_screen(on_login_click=show_login, on_signup_submit=show_chat)
        page.update()
    
    def show_chat(e=None):
        content_area.content = create_chat_screen(on_history_click=show_history, on_profile_click=show_profile)
        page.update()
    
    def show_history(e=None):
        content_area.content = create_history_screen(on_chat_click=show_chat)
        page.update()
    
    def show_profile(e=None):
        content_area.content = create_profile_screen(on_chat_click=show_chat)
        page.update()
    
    show_login()
    page.add(content_area)

if __name__ == "__main__":
    ft.app(main)
