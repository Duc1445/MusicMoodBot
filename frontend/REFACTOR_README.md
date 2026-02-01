# MusicMoodBot v2 - Refactored Architecture

## 📁 Cấu trúc mới

```
frontend/
├── main_v2.py              # Entry point mới (refactored)
├── src/
│   ├── config/
│   │   ├── settings.py     # ⭐ TẤT CẢ settings ở đây
│   │   ├── constants.py    # (legacy - sẽ deprecated)
│   │   └── theme_*.py      # Theme configs
│   │
│   ├── utils/
│   │   ├── state_manager_v2.py  # ⭐ State quản lý tập trung
│   │   ├── state_manager.py     # (legacy)
│   │   └── helpers.py           # UI helpers
│   │
│   ├── services/
│   │   ├── api_client.py       # HTTP client + Auth
│   │   ├── chat_service_v2.py  # ⭐ Chat logic (refactored)
│   │   ├── chat_service.py     # (legacy)
│   │   └── auth_service.py     # Auth handling
│   │
│   ├── components/
│   │   └── chat/
│   │       ├── __init__.py          # Export all components
│   │       ├── message_bubble.py    # Bot/User message UI
│   │       ├── song_card.py         # Song card UI
│   │       ├── mood_chips.py        # Mood/Intensity chips
│   │       └── typing_indicator.py  # Typing indicator
│   │
│   └── screens/
│       ├── chat_screen_v2.py   # ⭐ Chat screen (refactored)
│       ├── chat_screen.py      # (legacy)
│       ├── login_screen.py
│       ├── signup_screen.py
│       ├── history_screen.py
│       └── profile_screen.py

run_app_v2.py               # ⭐ Chạy cả backend + frontend
run_app.py                  # (legacy)
```

## 🚀 Chạy ứng dụng

```bash
# Cách mới (refactored)
python run_app_v2.py

# Hoặc chỉ frontend
python frontend/main_v2.py
```

## ⭐ Những gì đã thay đổi

### 1. Config tập trung (`settings.py`)
```python
from ..config.settings import settings, logger

# Tất cả settings ở 1 chỗ
print(settings.API_BASE_URL)
print(settings.TEAL_PRIMARY)

# Logging có sẵn
logger.info("Something happened")
logger.debug("Debug info")
```

### 2. State Manager mới (`state_manager_v2.py`)
```python
from ..utils.state_manager_v2 import app_state

# Thêm message
app_state.add_message("bot", "text", "Hello!")

# Check login
if app_state.is_logged_in():
    ...

# Set typing indicator
app_state.set_typing(True)
app_state.set_busy(True)
```

### 3. Chat Components tách riêng
```python
from ..components.chat import (
    create_bot_message,
    create_user_message,
    create_song_card,
    create_typing_indicator
)

# Sử dụng
msg = create_bot_message("Hello!")
card = create_song_card({"name": "Song A", "artist": "Artist B"})
```

### 4. Chat Screen với Controller pattern
```python
# chat_screen_v2.py sử dụng ChatScreenController
# Tách business logic ra khỏi UI

class ChatScreenController:
    def handle_mood_selection(self, mood: str): ...
    def handle_intensity_selection(self, intensity: str): ...
    def handle_text_message(self, text: str): ...
    def make_recommendation(self): ...
```

## 📋 Import đúng cách

**LUÔN dùng relative imports trong frontend:**
```python
# ✅ ĐÚNG
from ..config.settings import settings
from ..utils.state_manager_v2 import app_state
from ..services.api_client import api

# ❌ SAI (gây ra 2 instance khác nhau)
from src.config.settings import settings
from frontend.src.utils.state_manager import app_state
```

## 🐛 Debug

Logs sẽ hiển thị như sau:
```
11:32:24 | INFO    | mmb | Creating chat screen
11:32:24 | INFO    | mmb | Mood selected: Vui
11:32:24 | DEBUG   | mmb | Message added: bot/text - 3 total
```

Để bật DEBUG logging, sửa trong `settings.py`:
```python
logger = setup_logger("mmb", "DEBUG")  # Thay "INFO" bằng "DEBUG"
```

## 🔄 Migration từ legacy

Nếu muốn chuyển hoàn toàn sang v2:

1. Đổi import trong các screen khác:
   ```python
   from ..utils.state_manager_v2 import app_state  # thay vì state_manager
   ```

2. Đổi import trong services:
   ```python
   from ..config.settings import settings, logger
   ```

3. Xóa các file legacy (sau khi test kỹ):
   - `state_manager.py`
   - `chat_screen.py` 
   - `chat_service.py`
   - `constants.py`
