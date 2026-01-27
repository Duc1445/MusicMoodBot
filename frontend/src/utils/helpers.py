"""
Utility helper functions for MusicMoodBot frontend
"""

import flet as ft
import threading
from datetime import datetime


def _make_progress():
    """Create progress indicator spinner"""
    return ft.Container(
        width=16,
        height=16,
        border=ft.Border(
            left=ft.BorderSide(2, "#2F2F2F"),
            top=ft.BorderSide(2, "#2F2F2F"),
            right=ft.BorderSide(2, "#EFEFEF"),
            bottom=ft.BorderSide(2, "#EFEFEF"),
        ),
        border_radius=8,
    )


def _ui_safe(page: ft.Page, fn):
    """Execute function safely on UI thread"""
    try:
        fn()
    except Exception as e:
        print(f"UI Error: {e}")
    finally:
        try:
            page.update()
        except Exception:
            pass


def format_timestamp(timestamp=None):
    """Format timestamp for display"""
    if not timestamp:
        timestamp = datetime.now()
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return timestamp
    return timestamp.strftime("%H:%M")


def run_async(fn, delay_sec=1.0):
    """Run function asynchronously with optional delay"""
    def worker():
        import time
        if delay_sec > 0:
            time.sleep(delay_sec)
        fn()
    
    threading.Thread(target=worker, daemon=True).start()
