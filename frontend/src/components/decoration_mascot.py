"""
Decoration Mascot Component
A cute, animated mascot that serves as decoration on non-chat screens
Continuously blinks and moves slightly to keep the interface lively
"""

import flet as ft
import threading
import time
from src.components.talking_animator import TalkingAnimator, get_talking_frame_path
from src.config.theme_professional import *


class DecorationMascot:
    """Animated mascot that serves as page decoration"""
    
    def __init__(self, page: ft.Page, position: str = "bottom-right"):
        """
        Create a decoration mascot
        
        Args:
            page: Flet page reference
            position: "bottom-right", "bottom-left", "top-right", "top-left"
        """
        self.page = page
        self.position = position
        self.animator = None
        self.is_running = False
        
        # Create mascot image
        self.mascot_img = ft.Image(
            src=get_talking_frame_path("eyes_open_mouth_closed"),
            width=100,
            height=100,
            fit="contain",
        )
        
        # Create container
        self.mascot_container = ft.Container(
            width=130,
            height=130,
            border_radius=20,
            bgcolor=GLASS_MEDIUM,
            border=ft.border.all(2, PRIMARY_ACCENT),
            padding=10,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.mascot_img],
            ),
            shadow=ft.BoxShadow(
                blur_radius=12,
                color="#00D9FF40",
                offset=ft.Offset(0, 4),
            ),
        )
    
    def get_positioned_container(self) -> ft.Stack:
        """Get mascot in a positioned stack for placement"""
        # Position mapping
        position_map = {
            "bottom-right": ft.Alignment(1, 1),
            "bottom-left": ft.Alignment(-1, 1),
            "top-right": ft.Alignment(1, -1),
            "top-left": ft.Alignment(-1, -1),
        }
        
        alignment = position_map.get(self.position, ft.Alignment(1, 1))
        
        return ft.Stack(
            controls=[
                ft.Container(
                    expand=True,
                    content=ft.Container(),  # Invisible filler
                ),
                ft.Container(
                    content=self.mascot_container,
                    alignment=alignment,
                    padding=20,
                ),
            ],
            expand=True,
        )
    
    def start(self):
        """Start mascot animation"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Create animator for continuous idle animation
        self.animator = TalkingAnimator(self.mascot_img)
        self.animator.start_animation("idle")
    
    def stop(self):
        """Stop mascot animation"""
        if self.animator:
            self.animator.stop()
        self.is_running = False


def create_decoration_mascot(
    position: str = "bottom-right",
) -> tuple:
    """
    Create a decoration mascot that can be placed on a page
    
    Args:
        position: "bottom-right", "bottom-left", "top-right", "top-left"
    
    Returns:
        Tuple of (container, mascot_object)
    """
    # Create simple decoration without animation first
    mascot_img = ft.Image(
        src=get_talking_frame_path("eyes_open_mouth_closed"),
        width=100,
        height=100,
        fit="contain",
    )
    
    mascot_container = ft.Container(
        width=130,
        height=130,
        border_radius=20,
        bgcolor=GLASS_MEDIUM,
        border=ft.border.all(2, PRIMARY_ACCENT),
        padding=10,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[mascot_img],
        ),
        shadow=ft.BoxShadow(
            blur_radius=12,
            color="#00D9FF40",
            offset=ft.Offset(0, 4),
        ),
    )
    
    # Position mapping
    position_map = {
        "bottom-right": ft.Alignment(1, 1),
        "bottom-left": ft.Alignment(-1, 1),
        "top-right": ft.Alignment(1, -1),
        "top-left": ft.Alignment(-1, -1),
    }
    
    alignment = position_map.get(position, ft.Alignment(1, 1))
    
    positioned = ft.Stack(
        controls=[
            ft.Container(
                expand=True,
                content=ft.Container(),  # Invisible filler
            ),
            ft.Container(
                content=mascot_container,
                alignment=alignment,
                padding=20,
            ),
        ],
        expand=True,
    )
    
    return positioned, mascot_img
