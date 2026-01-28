import flet as ft
import sys
import os

# Setup paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(current_dir)  # Parent directory (MMB_FRONTBACK)
sys.path.insert(0, current_dir)
sys.path.insert(0, workspace_dir)

from backend.src.database.database import init_db, seed_sample_songs
from src.screens.login_screen import create_login_screen
from src.screens.signup_screen import create_signup_screen
from src.screens.chat_screen import create_chat_screen
from src.screens.history_screen import create_history_screen
from src.screens.profile_screen import create_profile_screen
from src.config.constants import APP_NAME
from src.utils.state_manager import app_state

def main(page: ft.Page):
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1000
    page.window.height = 700
    
    try:
        init_db()
        seed_sample_songs()
    except Exception as e:
        print(f"Database init: {e}")
    
    def on_login_success():
        app_state.current_screen = "chat"
        page.clean()
        page.add(create_chat_screen(page, on_history_click, on_profile_click))
    
    def on_signup_success():
        app_state.current_screen = "chat"
        page.clean()
        page.add(create_chat_screen(page, on_history_click, on_profile_click))
    
    def on_profile_click():
        app_state.current_screen = "profile"
        page.clean()
        page.add(create_profile_screen(on_chat_click, on_logout_click, on_history_click))
    
    def on_logout_click():
        app_state.current_screen = "login"
        page.clean()
        on_show_login()
    
    def on_chat_click():
        app_state.current_screen = "chat"
        page.clean()
        page.add(create_chat_screen(page, on_history_click, on_profile_click))
    
    def on_history_click():
        app_state.current_screen = "history"
        page.clean()
        page.add(create_history_screen(on_chat_click, on_profile_click))
    
    def on_show_login():
        app_state.current_screen = "login"
        page.clean()
        page.add(create_login_screen(on_show_signup, on_login_success))
    
    def on_show_signup():
        app_state.current_screen = "signup"
        page.clean()
        page.add(create_signup_screen(on_show_login, on_signup_success))
    
    on_show_login()

if __name__ == "__main__":
    ft.app(target=main)
