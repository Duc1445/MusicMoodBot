# 🧩 components/ - Reusable UI Components

Chứa **UI components** có thể dùng lại - button, input, card, v.v.

## 📝 Lưu ý

Hiện tại folder này trống. Khi cần tái sử dụng UI elements từ nhiều screens, hãy tạo components ở đây.

## 📋 Ví dụ components có thể tạo

```python
# message_bubble.py
def create_message_bubble(text, sender):
    """Tạo bubble hiển thị tin nhắn"""

# song_card.py
def create_song_card(song):
    """Tạo card gợi ý bài hát"""

# mood_button.py
def create_mood_button(mood, on_click):
    """Tạo nút chọn tâm trạng"""

# intensity_selector.py
def create_intensity_selector(on_click):
    """Tạo bộ chọn cường độ"""
```

## 🎨 Khi nào tạo components?

- Có UI element **dùng lại ở nhiều nơi**
- Code UI bị **lặp lại** nhiều lần
- Muốn **tách riêng** logic UI

## 🚀 Cách sử dụng

```python
# Trong screens
from src.components.song_card import create_song_card

card = create_song_card(song_data)
```

## ⚠️ Lưu ý

- Components **nhỏ, có thể tái sử dụng**
- Không chứa **business logic**
- Nhận dữ liệu từ **props/parameters**
- Gửi events qua **callbacks**
