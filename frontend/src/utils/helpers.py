"""
Utility helper functions for MusicMoodBot frontend
Enhanced with API and validation utilities
"""

import flet as ft
import threading
import re
from datetime import datetime
from typing import Optional, Callable, Any, Dict
import requests


def _make_progress():
    """Create progress indicator spinner"""
    return ft.Container(
        width=16,
        height=16,
        border=ft.Border(
            left=ft.BorderSide(2, "#2F2F2F"),
            top=ft.BorderSide(2, "#EFEFEF"),
            right=ft.BorderSide(2, "#EFEFEF"),
            bottom=ft.BorderSide(2, "#EFEFEF"),
        ),
        border_radius=8,
    )


def _ui_safe(page: ft.Page, fn: Callable):
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


def format_timestamp(timestamp=None) -> str:
    """Format timestamp for display"""
    if not timestamp:
        timestamp = datetime.now()
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return timestamp
    return timestamp.strftime("%H:%M")


def format_date(timestamp=None) -> str:
    """Format date for display"""
    if not timestamp:
        timestamp = datetime.now()
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return timestamp
    return timestamp.strftime("%d/%m/%Y")


def run_async(fn: Callable, delay_sec: float = 1.0):
    """Run function asynchronously with optional delay"""
    def worker():
        import time
        if delay_sec > 0:
            time.sleep(delay_sec)
        fn()
    
    threading.Thread(target=worker, daemon=True).start()


def debounce(wait_ms: int = 300):
    """Decorator to debounce function calls"""
    def decorator(fn: Callable):
        timer = None
        
        def debounced(*args, **kwargs):
            nonlocal timer
            if timer:
                timer.cancel()
            timer = threading.Timer(wait_ms / 1000, lambda: fn(*args, **kwargs))
            timer.start()
        
        return debounced
    return decorator


# ==================== VALIDATION HELPERS ====================

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_password(password: str, min_length: int = 6) -> bool:
    """Validate password length"""
    return len(password.strip()) >= min_length


def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    # Remove potentially dangerous characters
    text = re.sub(r'[<>\"\'\\]', '', text)
    # Trim whitespace
    text = text.strip()
    return text


# ==================== API HELPERS ====================

def api_call(
    url: str,
    method: str = "GET",
    params: Dict = None,
    data: Dict = None,
    timeout: int = 10
) -> Optional[Dict]:
    """
    Make API call with error handling.
    
    Args:
        url: API endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        params: Query parameters
        data: Request body (for POST/PUT)
        timeout: Request timeout in seconds
        
    Returns:
        Response JSON or None on error
    """
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, params=params, json=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = requests.put(url, params=params, json=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(url, params=params, timeout=timeout)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        print(f"API Timeout: {url}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"API Connection Error: {url}")
        return None
    except Exception as e:
        print(f"API Exception: {e}")
        return None


def check_api_health(base_url: str) -> bool:
    """Check if API is available"""
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


# ==================== UI HELPERS ====================

def create_snackbar(page: ft.Page, message: str, color: str = "#2ECC71"):
    """Show snackbar notification"""
    page.snack_bar = ft.SnackBar(
        content=ft.Text(message, color="#FFFFFF"),
        bgcolor=color,
        duration=3000
    )
    page.snack_bar.open = True
    page.update()


def create_error_snackbar(page: ft.Page, message: str):
    """Show error snackbar"""
    create_snackbar(page, message, color="#E74C3C")


def create_success_snackbar(page: ft.Page, message: str):
    """Show success snackbar"""
    create_snackbar(page, message, color="#2ECC71")


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_time_of_day() -> str:
    """Get current time of day for context"""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def get_greeting() -> str:
    """Get greeting based on time of day"""
    time_of_day = get_time_of_day()
    greetings = {
        "morning": "Chào buổi sáng!",
        "afternoon": "Chào buổi chiều!",
        "evening": "Chào buổi tối!",
        "night": "Đêm khuya rồi!"
    }
    return greetings.get(time_of_day, "Xin chào!")


# ==================== DATA HELPERS ====================

def normalize_song_data(song: Dict) -> Dict:
    """Normalize song data from different sources"""
    return {
        "song_id": song.get("song_id", song.get("id")),
        "name": song.get("song_name", song.get("name", "Unknown")),
        "artist": song.get("artist", song.get("artist_name", "Unknown")),
        "genre": song.get("genre", "Pop"),
        "mood": song.get("mood", ""),
        "intensity": song.get("intensity", 2),
        "suy_score": round(float(song.get("mood_score", 5) or 5), 1),
        "reason": song.get("recommendation_reason", song.get("reason", "")),
        "moods": song.get("moods", [song.get("mood", "")])
    }


def format_song_display(song: Dict) -> str:
    """Format song for display"""
    name = song.get("name", song.get("song_name", "Unknown"))
    artist = song.get("artist", song.get("artist_name", "Unknown"))
    return f"{name} - {artist}"
