import flet as ft
from datetime import datetime

# Design System Colors
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
    "icon_gray": "#D8D8D8",
}

# Global state
current_page_index = 0  # 0: Login, 1: Signup, 2: Chat, 3: History

def create_border_container(content, bg_color=COLORS["white"], padding=20, border_width=3):
    """Create a hand-drawn style container with thick border and offset shadow"""
    return ft.Container(
        content=content,
        bgcolor=bg_color,
        border=ft.border.all(border_width, COLORS["border_dark"]),
        border_radius=18,
        padding=padding,
        shadow=ft.shadow.Shadow(offset=ft.Offset(8, 8), blur_radius=1, color=ft.Colors.BLACK12),
    )

def create_pill_button(text, on_click=None, is_filled=False, outline=True):
    """Create a pill-shaped button with sketch style"""
    return ft.Container(
        content=ft.Text(text, size=14, weight="bold", color=COLORS["white"] if is_filled else COLORS["border_dark"]),
        bgcolor=COLORS["button_dark"] if is_filled else COLORS["white"],
        border=ft.border.all(3, COLORS["border_dark"]),
        border_radius=999,
        padding=ft.padding.symmetric(horizontal=24, vertical=12),
        on_click=on_click,
    )

def create_input_field(label, placeholder="", is_password=False, icon=None):
    """Create styled input field"""
    return ft.Column(
        [
            ft.Text(label, size=14, weight="bold", color=COLORS["border_dark"]),
            ft.Container(
                content=ft.Row(
                    [
                        ft.TextField(
                            hint_text=placeholder,
                            password=is_password,
                            border=ft.InputBorder.NONE,
                            filled=False,
                            expand=True,
                        ),
                        ft.Icon(icon, size=20, color=COLORS["text_gray"]) if icon else ft.Container(),
                    ],
                    spacing=10,
                ),
                bgcolor=COLORS["white"],
                border=ft.border.all(3, COLORS["border_dark"]),
                border_radius=14,
                padding=12,
            )
        ],
        spacing=8,
    )

# ===== FRAME 1: LOGIN SCREEN =====
def create_login_screen():
    page_content = ft.Container(
        bgcolor=COLORS["cream_bg"],
        expand=True,
        content=ft.Column(
            [
                # Modal window
                ft.Container(
                    content=ft.Column(
                        [
                            # Top bar (macOS style)
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Row([
                                            ft.Icon("circle_outline", size=12, color=COLORS["border_dark"]),
                                            ft.Icon("circle_outline", size=12, color=COLORS["border_dark"]),
                                            ft.Icon("circle_outline", size=12, color=COLORS["border_dark"]),
                                        ], spacing=8),
                                        ft.Row([
                                            ft.Icon("music_note", size=16, color=COLORS["border_dark"]),
                                            ft.Text("MusicMood Bot Login", size=12, weight="bold"),
                                        ], spacing=8, expand=True),
                                        ft.Icon("close", size=16, color=COLORS["border_dark"]),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                bgcolor=COLORS["light_gray"],
                                padding=16,
                                border_radius=ft.border_radius.only(top_left=18, top_right=18),
                            ),
                            # Divider
                            ft.Divider(height=3, color=COLORS["border_dark"]),
                            # Body (2 columns)
                            ft.Row(
                                [
                                    # Left column
                                    ft.Container(
                                        content=ft.Center(
                                            content=ft.Container(
                                                content=ft.Icon("music_note", size=80, color=COLORS["border_dark"]),
                                                border=ft.border.all(3, COLORS["border_dark"]),
                                                border_radius=999,
                                                width=260,
                                                height=260,
                                            ),
                                        ),
                                        expand=True,
                                        bgcolor=COLORS["white"],
                                    ),
                                    # Vertical divider
                                    ft.Container(width=3, bgcolor=COLORS["border_dark"]),
                                    # Right column
                                    ft.Container(
                                        content=ft.Column(
                                            [
                                                create_input_field("Email/Username", "user123", icon="person"),
                                                create_input_field("Password", "", is_password=True, icon="lock"),
                                                ft.Container(height=10),
                                                create_pill_button("LOGIN →", is_filled=True),
                                                ft.Row(
                                                    [
                                                        ft.Text("Don't have an account? ", size=12),
                                                        ft.Text("Sign up", size=12, color=COLORS["accent_teal"], text_decoration="underline"),
                                                    ],
                                                    spacing=0,
                                                ),
                                            ],
                                            spacing=16,
                                        ),
                                        expand=True,
                                        bgcolor=COLORS["white"],
                                        padding=24,
                                    ),
                                ],
                                expand=True,
                            ),
                            # Bottom bar
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Text("v1.0.0", size=11, color=COLORS["text_gray"]),
                                        ft.Row([
                                            ft.Icon("circle", size=10, color=COLORS["online_green"]),
                                            ft.Text("Online", size=11, color=COLORS["text_gray"]),
                                        ], spacing=6),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                bgcolor=COLORS["light_gray"],
                                padding=12,
                                border_radius=ft.border_radius.only(bottom_left=18, bottom_right=18),
                            ),
                        ],
                        spacing=0,
                    ),
                    width=860,
                    height=560,
                    bgcolor=COLORS["white"],
                    border=ft.border.all(3, COLORS["border_dark"]),
                    border_radius=18,
                    shadow=ft.shadow.Shadow(offset=ft.Offset(8, 8), blur_radius=1, color=ft.Colors.BLACK12),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    return page_content

# ===== FRAME 2: SIGN UP SCREEN =====
def create_signup_screen():
    page_content = ft.Container(
        bgcolor=COLORS["white"],
        expand=True,
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            # Top bar
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon("arrow_back", size=20, color=COLORS["border_dark"]),
                                        ft.Text("MUSICMOOD BOT\nSIGN UP", size=14, weight="bold", text_align="center", expand=True),
                                        ft.Icon("more_vert", size=20, color=COLORS["border_dark"]),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                padding=16,
                                border_radius=ft.border_radius.only(top_left=18, top_right=18),
                            ),
                            # Divider
                            ft.Divider(height=3, color=COLORS["border_dark"]),
                            # Body
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Center(
                                            content=ft.Container(
                                                content=ft.Icon("smart_toy", size=40, color=COLORS["border_dark"]),
                                                border=ft.border.all(3, COLORS["border_dark"]),
                                                border_radius=12,
                                                padding=12,
                                                width=60,
                                                height=60,
                                            )
                                        ),
                                        create_input_field("Full Name", "John Doe"),
                                        create_input_field("Email", "user@example.com"),
                                        create_input_field("Password", "", is_password=True),
                                        create_input_field("Confirm Password", "", is_password=True),
                                        ft.Container(height=8),
                                        create_pill_button("SIGN UP", is_filled=True),
                                        ft.Row(
                                            [
                                                ft.Text("Already have an account? ", size=12),
                                                ft.Text("Login", size=12, color=COLORS["accent_teal"], text_decoration="underline"),
                                            ],
                                            spacing=0,
                                            alignment=ft.MainAxisAlignment.CENTER,
                                        ),
                                    ],
                                    spacing=14,
                                ),
                                padding=20,
                            ),
                        ],
                        spacing=0,
                    ),
                    width=420,
                    height=760,
                    bgcolor=COLORS["white"],
                    border=ft.border.all(3, COLORS["border_dark"]),
                    border_radius=18,
                    shadow=ft.shadow.Shadow(offset=ft.Offset(8, 8), blur_radius=1, color=ft.Colors.BLACK12),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    return page_content

# ===== FRAME 3: CHAT SCREEN =====
def create_chat_screen():
    def create_menu_item(icon, label, selected=False):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=20, color=COLORS["white"] if selected else COLORS["border_dark"]),
                    ft.Text(label, size=13, color=COLORS["white"] if selected else COLORS["border_dark"]),
                ],
                spacing=12,
            ),
            bgcolor=COLORS["accent_teal"] if selected else COLORS["white"],
            border=ft.border.all(3, COLORS["border_dark"]),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            margin=ft.margin.only(bottom=8),
        )

    page_content = ft.Row(
        [
            # Sidebar
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Menu", size=16, weight="bold", color=COLORS["border_dark"]),
                        ft.Divider(height=3, color=COLORS["border_dark"]),
                        create_menu_item("chat", "Đoạn chat", selected=True),
                        create_menu_item("history", "Lịch sử"),
                        create_menu_item("person", "Hồ sơ"),
                        ft.Spacer(),
                        ft.Text("MUSICMOOD V1.0", size=10, color=COLORS["text_gray"]),
                    ],
                    spacing=12,
                ),
                width=300,
                padding=16,
                border_radius=0,
                border=ft.border.only(right=ft.BorderSide(3, COLORS["border_dark"])),
            ),
            # Main content
            ft.Container(
                content=ft.Column(
                    [
                        # Top bar
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Row([
                                        ft.Icon("music_note", size=24, color=COLORS["border_dark"]),
                                        ft.Text("MusicMoodBot", size=16, weight="bold"),
                                    ], spacing=8),
                                    ft.Row([
                                        ft.Icon("settings", size=20, color=COLORS["border_dark"]),
                                        ft.Container(
                                            content=ft.Text("U", size=12, weight="bold", color=COLORS["white"]),
                                            border=ft.border.all(2, COLORS["border_dark"]),
                                            border_radius=999,
                                            width=32,
                                            height=32,
                                            bgcolor=COLORS["button_dark"],
                                            alignment=ft.alignment.center,
                                        ),
                                    ], spacing=12),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            padding=12,
                            border_radius=0,
                            border=ft.border.only(bottom=ft.BorderSide(3, COLORS["border_dark"])),
                        ),
                        # Chat area
                        ft.Column(
                            [
                                # Date pill
                                ft.Center(
                                    content=ft.Container(
                                        content=ft.Text("Today", size=12, weight="bold", color=COLORS["white"]),
                                        bgcolor=COLORS["button_dark"],
                                        border=ft.border.all(2, COLORS["border_dark"]),
                                        border_radius=999,
                                        padding=ft.padding.symmetric(horizontal=16, vertical=6),
                                    ),
                                ),
                                ft.Container(height=8),
                                # Bot message
                                ft.Row(
                                    [
                                        ft.Container(
                                            content=ft.Text("B", size=14, weight="bold", color=COLORS["white"]),
                                            border=ft.border.all(2, COLORS["border_dark"]),
                                            border_radius=999,
                                            width=36,
                                            height=36,
                                            bgcolor=COLORS["button_dark"],
                                            alignment=ft.alignment.center,
                                        ),
                                        ft.Column(
                                            [
                                                ft.Row([
                                                    ft.Text("MusicMoodBot", size=12, weight="bold"),
                                                    ft.Text("10:00 AM", size=11, color=COLORS["text_gray"]),
                                                ], spacing=8),
                                                ft.Container(
                                                    content=ft.Text(
                                                        "Chào bạn! Hôm nay bạn cảm thấy thế nào? Mình sẽ giúp bạn chọn nhạc phù hợp nhé!",
                                                        size=13,
                                                        color=COLORS["border_dark"],
                                                    ),
                                                    border=ft.border.all(3, COLORS["border_dark"]),
                                                    border_radius=14,
                                                    padding=12,
                                                    bgcolor=COLORS["white"],
                                                    shadow=ft.shadow.Shadow(offset=ft.Offset(4, 4), blur_radius=0, color=ft.Colors.BLACK12),
                                                ),
                                                # Quick reply buttons
                                                ft.Row(
                                                    [
                                                        create_pill_button("😊 Vui"),
                                                        create_pill_button("😢 Buồn"),
                                                        create_pill_button("⚡ Năng động"),
                                                    ],
                                                    spacing=8,
                                                    wrap=True,
                                                ),
                                            ],
                                            spacing=8,
                                            expand=True,
                                        ),
                                    ],
                                    spacing=12,
                                    alignment=ft.MainAxisAlignment.START,
                                ),
                                ft.Spacer(),
                                ft.Center(content=ft.Text("CDIO PROJECT • VARIANT 1", size=9, color=ft.Colors.GREY_400, italic=True)),
                            ],
                            expand=True,
                            spacing=12,
                        ),
                        # Input bar
                        ft.Row(
                            [
                                ft.Icon("add", size=20, color=COLORS["border_dark"]),
                                ft.TextField(
                                    hint_text="Nhập tin nhắn…",
                                    expand=True,
                                    border=ft.InputBorder.UNDERLINE,
                                    border_color=COLORS["border_dark"],
                                ),
                                ft.Container(
                                    content=ft.Text("GỬI >", size=12, weight="bold", color=COLORS["white"]),
                                    bgcolor=COLORS["accent_teal"],
                                    border=ft.border.all(2, COLORS["border_dark"]),
                                    border_radius=12,
                                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                                ),
                            ],
                            spacing=12,
                            alignment=ft.MainAxisAlignment.START,
                        ),
                    ],
                    spacing=12,
                ),
                expand=True,
                padding=12,
            ),
        ],
        expand=True,
    )
    return page_content

# ===== FRAME 4: HISTORY SCREEN =====
def create_history_screen():
    def create_mood_tag(mood, time_str):
        mood_colors = {
            "BUỒN": COLORS["mood_sad"],
            "SUY TƯ": COLORS["mood_think"],
            "VUI": COLORS["mood_happy"],
        }
        return ft.Container(
            content=ft.Row([
                ft.Icon("sentiment_satisfied" if mood == "VUI" else "sentiment_dissatisfied", size=12, color=COLORS["border_dark"]),
                ft.Text(f"{mood} • {time_str}", size=10, weight="bold", color=COLORS["border_dark"]),
            ], spacing=4),
            bgcolor=mood_colors.get(mood, COLORS["mood_happy"]),
            border=ft.border.all(2, COLORS["border_dark"]),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
        )

    def create_history_card(mood, time_str, title, artist, date, date_color):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        bgcolor=COLORS["text_gray"],
                        width=100,
                        height=100,
                        border=ft.border.all(2, COLORS["border_dark"]),
                        border_radius=10,
                    ),
                    ft.Column(
                        [
                            create_mood_tag(mood, time_str),
                            ft.Text(title, size=14, weight="bold", color=COLORS["border_dark"]),
                            ft.Text(artist, size=12, color=COLORS["text_gray"]),
                            ft.Row([
                                ft.Icon("history", size=14, color=COLORS["text_gray"]),
                                ft.Text("Chi tiết đề xuất →", size=12, color=COLORS["accent_teal"]),
                            ], spacing=4),
                        ],
                        spacing=6,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Icon("delete", size=16, color=COLORS["border_dark"]),
                            ft.Container(
                                content=ft.Text(date, size=10, weight="bold", color=COLORS["border_dark"]),
                                bgcolor=date_color,
                                border=ft.border.all(2, COLORS["border_dark"]),
                                border_radius=8,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=16,
            ),
            border=ft.border.all(3, COLORS["border_dark"]),
            border_radius=18,
            padding=16,
            bgcolor=COLORS["white"],
            shadow=ft.shadow.Shadow(offset=ft.Offset(6, 6), blur_radius=0, color=ft.Colors.BLACK12),
            margin=ft.margin.only(bottom=12),
        )

    page_content = ft.Row(
        [
            # Sidebar
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("MusicMood\nBOT", size=14, weight="bold", text_align="center"),
                        ft.Divider(height=3, color=COLORS["border_dark"]),
                        ft.Container(
                            content=ft.Row([ft.Icon("chat", size=16), ft.Text("Chat")], spacing=8),
                            padding=10,
                            bgcolor=COLORS["white"],
                            border=ft.border.all(2, COLORS["border_dark"]),
                            border_radius=8,
                            margin=ft.margin.only(bottom=6),
                        ),
                        ft.Container(
                            content=ft.Row([ft.Icon("history", size=16), ft.Text("Lịch sử")], spacing=8),
                            padding=10,
                            bgcolor=COLORS["accent_teal"],
                            border=ft.border.all(3, COLORS["border_dark"]),
                            border_radius=8,
                            margin=ft.margin.only(bottom=6),
                        ),
                        ft.Container(
                            content=ft.Row([ft.Icon("person", size=16), ft.Text("Cá nhân")], spacing=8),
                            padding=10,
                            bgcolor=COLORS["white"],
                            border=ft.border.all(2, COLORS["border_dark"]),
                            border_radius=8,
                        ),
                        ft.Spacer(),
                        ft.Row([
                            ft.Icon("settings", size=16),
                            ft.Text("Cài đặt", size=12),
                        ], spacing=8),
                    ],
                    spacing=10,
                ),
                width=240,
                padding=16,
                border=ft.border.only(right=ft.BorderSide(3, COLORS["border_dark"])),
            ),
            # Main content
            ft.Container(
                content=ft.Column(
                    [
                        # Header
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text("ARCHIVE", size=11, weight="bold", color=COLORS["white"]),
                                    bgcolor=COLORS["button_dark"],
                                    border=ft.border.all(2, COLORS["border_dark"]),
                                    border_radius=999,
                                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                                ),
                                ft.Row([
                                    ft.Icon("calendar_today", size=16, color=COLORS["border_dark"]),
                                    ft.Text("Tháng 10, 2023", size=12, weight="bold"),
                                ], spacing=6),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Text("Lịch sử nghe nhạc", size=24, weight="bold", color=COLORS["border_dark"]),
                        ft.Text(
                            "Xem lại hành trình cảm xúc và những gợi ý âm nhạc từ MusicMood Bot của bạn.",
                            size=12,
                            color=COLORS["text_gray"],
                        ),
                        ft.Container(height=8),
                        # Filter bar
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Lọc theo cảm xúc:", size=12, weight="bold"),
                                    ft.Row(
                                        [
                                            ft.Container(
                                                content=ft.Text("Tất cả", size=11, weight="bold", color=COLORS["white"]),
                                                bgcolor=COLORS["button_dark"],
                                                border=ft.border.all(2, COLORS["border_dark"]),
                                                border_radius=999,
                                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                            ),
                                            create_pill_button("Vui"),
                                            create_pill_button("Buồn"),
                                            create_pill_button("Năng động"),
                                            create_pill_button("Thư giãn"),
                                        ],
                                        spacing=8,
                                        wrap=True,
                                    ),
                                ],
                                spacing=10,
                            ),
                            border=ft.border.all(3, COLORS["border_dark"]),
                            border_radius=18,
                            padding=16,
                            bgcolor=COLORS["white"],
                        ),
                        ft.Container(height=8),
                        # History cards
                        ft.Column(
                            [
                                create_history_card("BUỒN", "14:30 PM", "Mưa Tháng Sáu", "Văn Mai Hương", "20/10/2023", COLORS["date_yellow"]),
                                create_history_card("SUY TƯ", "20:15 PM", "Ngày Chưa Giông Bão", "Bùi Lan Hương", "19/10/2023", COLORS["text_gray"]),
                                create_history_card("VUI", "09:00 AM", "Có Chàng Trai Viết Lên Cây", "Phan Mạnh Quỳnh", "18/10/2023", COLORS["mood_happy"]),
                            ],
                            spacing=0,
                            expand=True,
                        ),
                    ],
                    spacing=12,
                    expand=True,
                ),
                expand=True,
                padding=16,
            ),
        ],
        expand=True,
    )
    return page_content

def main(page: ft.Page):
    page.title = "MusicMood Bot"
    page.window_width = 1440
    page.window_height = 900
    page.padding = 0
    page.bgcolor = COLORS["white"]
    
    # Content switcher
    content_area = ft.Container(expand=True)
    
    def show_screen(index):
        global current_page_index
        current_page_index = index
        if index == 0:
            content_area.content = create_login_screen()
        elif index == 1:
            content_area.content = create_signup_screen()
        elif index == 2:
            content_area.content = create_chat_screen()
        elif index == 3:
            content_area.content = create_history_screen()
        page.update()
    
    # Show login screen by default
    show_screen(0)
    
    # Add navigation buttons (development only, can be removed)
    nav_row = ft.Row(
        [
            ft.ElevatedButton("Login", on_click=lambda e: show_screen(0)),
            ft.ElevatedButton("Sign Up", on_click=lambda e: show_screen(1)),
            ft.ElevatedButton("Chat", on_click=lambda e: show_screen(2)),
            ft.ElevatedButton("History", on_click=lambda e: show_screen(3)),
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
    )
    
    page.add(
        ft.Column(
            [
                nav_row,
                content_area,
            ],
            spacing=0,
            expand=True,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)