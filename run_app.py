#!/usr/bin/env python
"""
MusicMoodBot - Integrated Application
Runs both Backend API and Frontend UI together
"""
import sys
import os
import threading
import time

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "frontend"))

def run_backend():
    """Start FastAPI backend server in background thread"""
    try:
        import uvicorn
        from backend.main import app
        
        print("🔧 Backend starting on http://localhost:8000")
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="warning",
            access_log=False
        )
    except Exception as e:
        print(f"❌ Backend error: {e}")

def run_frontend():
    """Start Flet frontend UI"""
    try:
        import flet as ft
        from backend.src.database.database import init_db, seed_sample_songs
        from frontend.src.screens.login_screen import create_login_screen
        from frontend.src.screens.signup_screen import create_signup_screen
        from frontend.src.screens.chat_screen import create_chat_screen
        from frontend.src.screens.history_screen import create_history_screen
        from frontend.src.screens.profile_screen import create_profile_screen
        from frontend.src.config.constants import APP_NAME
        from frontend.src.utils.state_manager import app_state
        
        def main(page: ft.Page):
            page.title = APP_NAME
            page.theme_mode = ft.ThemeMode.DARK
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
            
            def on_history_click():
                app_state.current_screen = "history"
                page.clean()
                page.add(create_history_screen(on_chat_click, on_profile_click))
            
            def on_chat_click():
                app_state.current_screen = "chat"
                page.clean()
                page.add(create_chat_screen(page, on_history_click, on_profile_click))
            
            def on_show_login():
                page.clean()
                page.add(create_login_screen(
                    on_signup_click=lambda: on_show_signup(),
                    on_login_submit=on_login_success
                ))
            
            def on_show_signup():
                page.clean()
                page.add(create_signup_screen(
                    on_login_click=lambda: on_show_login(),
                    on_signup_submit=on_signup_success
                ))
            
            # Start with login
            on_show_login()
        
        print("🎨 Frontend starting...")
        ft.app(target=main)
        
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("\n" + "="*60)
    print("🎵 MusicMoodBot - Integrated Application")
    print("="*60)
    print()
    print("📦 Starting services...")
    print()
    
    # Start backend in background thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend to initialize
    time.sleep(2)
    print("✅ Backend ready: http://localhost:8000/api/docs")
    print()
    
    # Run frontend in main thread (Flet requires main thread)
    print("🚀 Launching UI...")
    print("-"*60)
    run_frontend()

if __name__ == "__main__":
    main()


#python run_app.py