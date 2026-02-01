"""
MusicMoodBot Frontend - Main Entry Point
=========================================
Clean, modular entry point with proper imports.

Usage:
    python main.py
    
Or via Flet:
    flet run main.py
"""

import flet as ft
import sys
import os

# ==================== PATH SETUP ====================
# This ensures imports work correctly regardless of where the script is run from

current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(current_dir)

# Add to sys.path if not already there
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

# ==================== IMPORTS ====================
# Using new refactored modules

from src.config.settings import settings, logger

# Screens
from src.screens.login_screen import create_login_screen
from src.screens.signup_screen import create_signup_screen
from src.screens.chat_screen import create_chat_screen
from src.screens.history_screen import create_history_screen
from src.screens.profile_screen import create_profile_screen

# State
from src.utils.state_manager import app_state

# Services
from src.services.auth_service import auth_service
from src.services.api_client import api

# Database (optional)
try:
    from backend.src.database.database import init_db, seed_sample_songs
    HAS_DB = True
except ImportError:
    HAS_DB = False
    logger.warning("Database module not available")


def main(page: ft.Page):
    """
    Main application entry point.
    
    Sets up the page and navigation between screens.
    """
    logger.info("=" * 50)
    logger.info("MusicMoodBot Starting...")
    logger.info(f"API URL: {settings.API_BASE_URL}")
    logger.info("=" * 50)
    
    # Page configuration
    page.title = "MusicMoodBot"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1000
    page.window.height = 700
    page.padding = 0
    
    # Initialize services with Flet page
    auth_service.set_flet_page(page)
    api.set_flet_page(page)
    logger.debug("Services initialized with Flet page")
    
    # Initialize database (if available)
    if HAS_DB:
        try:
            init_db()
            seed_sample_songs()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database init error: {e}")
    
    # ==================== NAVIGATION HANDLERS ====================
    
    def navigate_to_chat():
        """Navigate to chat screen"""
        logger.info("Navigating to: Chat")
        app_state.current_screen = "chat"
        page.clean()
        chat_screen = create_chat_screen(page, navigate_to_history, navigate_to_profile)
        page.add(chat_screen)
        page.update()
    
    def navigate_to_history():
        """Navigate to history screen"""
        logger.info("Navigating to: History")
        app_state.current_screen = "history"
        page.clean()
        page.add(create_history_screen(navigate_to_chat, navigate_to_profile))
        page.update()
    
    def navigate_to_profile():
        """Navigate to profile screen"""
        logger.info("Navigating to: Profile")
        app_state.current_screen = "profile"
        page.clean()
        page.add(create_profile_screen(navigate_to_chat, handle_logout, navigate_to_history))
        page.update()
    
    def navigate_to_login():
        """Navigate to login screen"""
        logger.info("Navigating to: Login")
        app_state.current_screen = "login"
        page.clean()
        page.add(create_login_screen(navigate_to_signup, handle_login_success))
        page.update()
    
    def navigate_to_signup():
        """Navigate to signup screen"""
        logger.info("Navigating to: Signup")
        app_state.current_screen = "signup"
        page.clean()
        page.add(create_signup_screen(navigate_to_login, handle_signup_success))
        page.update()
    
    # ==================== AUTH HANDLERS ====================
    
    def handle_login_success():
        """Called after successful login"""
        logger.info(f"Login success: {app_state.user_info.get('name', 'Guest')}")
        app_state.save_state()
        navigate_to_chat()
    
    def handle_signup_success():
        """Called after successful signup"""
        logger.info(f"Signup success: {app_state.user_info.get('name', 'Guest')}")
        app_state.save_state()
        navigate_to_chat()
    
    def handle_logout():
        """Handle user logout"""
        logger.info("User logged out")
        app_state.reset_user()
        app_state.reset_chat()
        app_state.save_state()
        auth_service.clear_token()
        navigate_to_login()
    
    # ==================== START APP ====================
    
    # Check if user is already logged in
    if app_state.is_logged_in():
        logger.info(f"Restoring session for: {app_state.user_info.get('name', 'Guest')}")
        navigate_to_chat()
    else:
        navigate_to_login()


if __name__ == "__main__":
    logger.info("Starting Flet app...")
    ft.app(target=main)
