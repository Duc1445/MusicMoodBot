"""
Animated Mascot Component for Chat
Shows mascot with scale/shake animation when chatting
Supports talking animations with different mouth/eye states
"""

import flet as ft
import os
import threading
from src.config.theme_professional import *


def get_mascot_emote_path(mood: str = "listening"):
    """Get path to mascot emote image"""
    # Map moods to emote files
    mood_map = {
        "Vui": "mascot_happy.png",
        "Buồn": "mascot_sad.png",
        "Suy tư": "mascot_thinking.png",
        "Chill": "mascot_listening.png",
        "Nâng lương": "mascot_love.png",
    }
    
    filename = mood_map.get(mood, "mascot_listening.png")
    
    # Get absolute path from project root
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    mascot_path = os.path.join(current_dir, "..", "mascot", "emote", filename)
    
    return mascot_path


def create_mascot_bubble(mood: str = "listening"):
    """
    Create a new mascot bubble instance
    Each message gets its own mascot instance
    """
    
    mascot_img = ft.Image(
        src=get_mascot_emote_path(mood),
        width=80,
        height=80,
        fit="contain",
    )
    
    # Container for mascot
    mascot_container = ft.Container(
        width=120,
        height=120,
        border_radius=16,
        bgcolor=BG_CARD,
        border=ft.border.all(2, PRIMARY_ACCENT),
        padding=10,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[mascot_img],
        ),
    )
    
    return mascot_container, mascot_img


def create_animated_mascot_bubble(mood: str = "listening"):
    """
    Create animated mascot bubble with simple animation
    Shows mascot in a chat-like bubble format
    """
    
    mascot_img = ft.Image(
        src=get_mascot_emote_path(mood),
        width=80,
        height=80,
        fit="contain",
    )
    
    # Simple container for mascot
    animated_mascot = ft.Container(
        width=120,
        height=120,
        border_radius=16,
        bgcolor=BG_CARD,
        border=ft.border.all(2, PRIMARY_ACCENT),
        padding=10,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[mascot_img],
        ),
    )
    
    # Return both the component and function to update mascot
    def update_mascot(new_mood: str):
        """Update mascot image based on mood"""
        mascot_img.src = get_mascot_emote_path(new_mood)
        mascot_img.update()
    
    def animate_mascot():
        """Trigger scale animation with padding change"""
        original_padding = animated_mascot.padding
        original_width = animated_mascot.width
        original_height = animated_mascot.height
        
        # Pulse effect - change padding
        animated_mascot.padding = 15
        animated_mascot.width = 130
        animated_mascot.height = 130
        animated_mascot.update()
        
        # Reset after animation
        def reset_scale():
            animated_mascot.padding = original_padding
            animated_mascot.width = original_width
            animated_mascot.height = original_height
            animated_mascot.update()
        
        # Schedule reset
        import threading
        timer = threading.Timer(0.3, reset_scale)
        timer.start()
    
    return animated_mascot, update_mascot, animate_mascot

def animate_mascot_container(container):
    """Pulse animation for mascot container"""
    import threading
    
    # Scale up
    container.width = 130
    container.height = 130
    container.update()
    
    # Reset to original size
    def reset():
        container.width = 120
        container.height = 120
        container.update()
    
    threading.Timer(0.4, reset).start()


def update_mascot_image(mascot_img, mood: str):
    """Update mascot emote image based on mood"""
    mascot_img.src = get_mascot_emote_path(mood)
    mascot_img.update()