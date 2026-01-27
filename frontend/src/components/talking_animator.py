"""
Talking Animation System for Mascot
Handles different mouth/eye states during bot responses
"""

import flet as ft
import os
import threading


# Maps for talking frame sequences
TALKING_FRAMES = {
    "idle": {
        "frames": ["eyes_open_mouth_closed"],
        "blink_interval": 4.0,  # Blink every 4 seconds
        "blink_duration": 0.12,
        "blink_frame": "eyes_closed_mouth_closed",
    },
    "listening": {
        "sequence": ["eyes_open_mouth_closed", "eyes_open_mouth_open_o"],
        "frame_duration": 0.2,
    },
    "speaking": {
        "sequence": ["eyes_open_mouth_closed", "eyes_open_mouth_open_o"],
        "frame_duration": 0.14,
    },
    "happy": {
        "sequence": ["eyes_closed_mouth_open_smile", "eyes_closed_mouth_open_smile_2"],
        "frame_duration": 0.2,
    },
    "singing": {
        "sequence": ["eyes_closed_mouth_closed", "eyes_closed_mouth_open_o"],
        "frame_duration": 0.16,
    },
}


def get_talking_frame_path(frame_name: str):
    """Get path to talking animation frame"""
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    frame_path = os.path.join(
        current_dir, 
        "..", 
        "mascot", 
        "emote", 
        "Talking",
        f"mascot_{frame_name}.png"
    )
    return frame_path


class TalkingAnimator:
    """Manages talking animations for mascot"""
    
    def __init__(self, mascot_img: ft.Image):
        self.mascot_img = mascot_img
        self.current_state = "idle"
        self.animation_thread = None
        self.stop_animation = False
        self.blink_thread = None
    
    def start_animation(self, state: str = "speaking"):
        """Start animation for given state"""
        if state not in TALKING_FRAMES:
            state = "speaking"
        
        self.current_state = state
        self.stop_animation = False
        
        # Stop any existing animation
        if self.animation_thread:
            self.stop_animation = True
            self.animation_thread.join(timeout=1)
        
        # Start new animation thread
        self.animation_thread = threading.Thread(
            target=self._run_animation,
            args=(state,),
            daemon=True
        )
        self.animation_thread.start()
        
        # Start blink for idle
        if state == "idle":
            self._start_blink()
    
    def _run_animation(self, state: str):
        """Run animation loop"""
        config = TALKING_FRAMES.get(state)
        if not config:
            return
        
        sequence = config.get("sequence", [])
        frame_duration = config.get("frame_duration", 0.2)
        
        if not sequence:
            return
        
        frame_index = 0
        
        while not self.stop_animation:
            # Check if mascot image is still valid and on page
            try:
                if not self.mascot_img.page:
                    # Image not on page anymore, stop animation
                    break
            except:
                # Image was removed or invalid
                break
            
            frame_name = sequence[frame_index % len(sequence)]
            frame_path = get_talking_frame_path(frame_name)
            
            try:
                self.mascot_img.src = frame_path
                self.mascot_img.update()
            except:
                # Update failed (control not on page), stop animation
                break
            
            frame_index += 1
            threading.Event().wait(frame_duration)
    
    def _start_blink(self):
        """Start blinking animation for idle state"""
        if self.blink_thread:
            return
        
        config = TALKING_FRAMES.get("idle")
        if not config:
            return
        
        blink_interval = config.get("blink_interval", 4.0)
        blink_duration = config.get("blink_duration", 0.12)
        blink_frame = config.get("blink_frame", "eyes_closed_mouth_closed")
        main_frame = "eyes_open_mouth_closed"
        
        def blink_loop():
            while not self.stop_animation and self.current_state == "idle":
                # Wait before blink
                threading.Event().wait(blink_interval)
                
                if self.stop_animation or self.current_state != "idle":
                    break
                
                # Check if mascot is still on page
                try:
                    if not self.mascot_img.page:
                        break
                except:
                    break
                
                # Blink
                try:
                    self.mascot_img.src = get_talking_frame_path(blink_frame)
                    self.mascot_img.update()
                except:
                    break
                
                threading.Event().wait(blink_duration)
                
                # Open eyes again
                try:
                    self.mascot_img.src = get_talking_frame_path(main_frame)
                    self.mascot_img.update()
                except:
                    break
        
        self.blink_thread = threading.Thread(target=blink_loop, daemon=True)
        self.blink_thread.start()
    
    def stop(self):
        """Stop all animations"""
        self.stop_animation = True
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
        if self.blink_thread:
            self.blink_thread.join(timeout=1)
