#!/usr/bin/env python
"""
MusicMoodBot - Integrated Application
======================================
Runs both Backend API and Frontend UI together.

Features:
- Centralized settings and logging
- Clean modular architecture
- Better error handling

Usage:
    python run_app.py
"""
import sys
import os
import threading
import time
import logging

# ==================== PATH SETUP ====================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "frontend"))

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("mmb.main")


def run_backend():
    """Start FastAPI backend server in background thread"""
    try:
        import uvicorn
        from backend.main import app
        
        logger.info("Backend starting on http://localhost:8000")
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="warning",
            access_log=False
        )
    except Exception as e:
        logger.error(f"Backend error: {e}")


def run_frontend():
    """Start Flet frontend UI (refactored version)"""
    try:
        import flet as ft
        
        # Import refactored modules
        from frontend.src.config.settings import settings, logger as app_logger
        from frontend.src.utils.state_manager import app_state
        from frontend.src.services.auth_service import auth_service
        from frontend.src.services.api_client import api
        
        # Import screens
        from frontend.src.screens.login_screen import create_login_screen
        from frontend.src.screens.signup_screen import create_signup_screen
        from frontend.src.screens.chat_screen import create_chat_screen
        from frontend.src.screens.history_screen import create_history_screen
        from frontend.src.screens.profile_screen import create_profile_screen
        
        # Database (optional)
        try:
            from backend.src.database.database import init_db, seed_sample_songs
            HAS_DB = True
        except ImportError:
            HAS_DB = False
            app_logger.warning("Database module not available")
        
        def main(page: ft.Page):
            """Main Flet app entry point"""
            app_logger.info("=" * 50)
            app_logger.info("MusicMoodBot Frontend Starting...")
            app_logger.info("=" * 50)
            
            # Configure page
            page.title = "MusicMoodBot"
            page.theme_mode = ft.ThemeMode.LIGHT
            page.window.width = 1000
            page.window.height = 700
            page.padding = 0
            
            # Initialize services with Flet page
            auth_service.set_flet_page(page)
            api.set_flet_page(page)
            
            # Initialize database
            if HAS_DB:
                try:
                    init_db()
                    seed_sample_songs()
                    app_logger.info("Database initialized")
                except Exception as e:
                    app_logger.error(f"Database init error: {e}")
            
            # ==================== NAVIGATION ====================
            
            def navigate_to_chat():
                app_logger.info("→ Chat")
                page.clean()
                page.add(create_chat_screen(page, navigate_to_history, navigate_to_profile))
                page.update()
            
            def navigate_to_history():
                app_logger.info("→ History")
                page.clean()
                page.add(create_history_screen(navigate_to_chat, navigate_to_profile))
                page.update()
            
            def navigate_to_profile():
                app_logger.info("→ Profile")
                page.clean()
                page.add(create_profile_screen(navigate_to_chat, handle_logout, navigate_to_history))
                page.update()
            
            def navigate_to_login():
                app_logger.info("→ Login")
                page.clean()
                page.add(create_login_screen(navigate_to_signup, handle_login_success))
                page.update()
            
            def navigate_to_signup():
                app_logger.info("→ Signup")
                page.clean()
                page.add(create_signup_screen(navigate_to_login, handle_signup_success))
                page.update()
            
            # ==================== AUTH HANDLERS ====================
            
            def handle_login_success():
                app_logger.info(f"Login success: {app_state.user_info.get('name', 'Guest')}")
                app_state.save_state()
                navigate_to_chat()
            
            def handle_signup_success():
                app_logger.info(f"Signup success: {app_state.user_info.get('name', 'Guest')}")
                app_state.save_state()
                navigate_to_chat()
            
            def handle_logout():
                app_logger.info("User logged out")
                app_state.reset_user()
                app_state.reset_chat()
                app_state.save_state()
                auth_service.clear_token()
                navigate_to_login()
            
            # ==================== START ====================
            
            if app_state.is_logged_in():
                app_logger.info(f"Restoring session for: {app_state.user_info.get('name', 'Guest')}")
                navigate_to_chat()
            else:
                navigate_to_login()
        
        logger.info("Frontend launching...")
        ft.app(target=main)
        
    except Exception as e:
        logger.error(f"Frontend error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    print()
    print("=" * 60)
    print("🎵 MusicMoodBot")
    print("=" * 60)
    print()
    
    logger.info("Starting services...")
    
    # Start backend in background thread
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend to initialize
    time.sleep(2)
    logger.info("Backend ready: http://localhost:8000/api/docs")
    
    # Run frontend in main thread (Flet requires main thread)
    logger.info("Launching UI...")
    print("-" * 60)
    run_frontend()


if __name__ == "__main__":
    main()
