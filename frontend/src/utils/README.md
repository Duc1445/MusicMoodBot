# 🛠️ utils/ - Helper Functions & Utilities

Chứa **hàm tiện ích** - state management, async, helpers, v.v.

## 📄 Files

- **state_manager.py** - Quản lý trạng thái toàn cục
- **helpers.py** - Hàm tiện ích (format time, async, v.v.)

## 🎯 Mỗi file làm gì?

### state_manager.py

```python
# Trạng thái toàn cục
app_state = AppState()

# Truy cập state
app_state.user_info      # {"name": "...", "email": "..."}
app_state.chat_messages  # [{"sender": "user", "text": "..."}, ...]
app_state.chat_flow      # {"state": "await_mood", "mood": "..."}

# Cập nhật state
app_state.reset_chat()
app_state.reset_user()
```

### helpers.py

```python
# Tạo loading spinner
_make_progress()

# Thực thi an toàn trong UI thread
_ui_safe(page, lambda: ...)

# Format thời gian
format_timestamp(timestamp)

# Thực thi bất đồng bộ
run_async(function, delay)
```

## 🎨 Khi nào edit?

- Thêm hàm tiện ích mới
- Thay đổi state structure
- Sửa lỗi state management
- Thêm helper functions

## ⚠️ Lưu ý

- **state_manager.py** là **single source of truth** cho state
- Tất cả screens/services dùng **cùng một app_state**
- Helpers **không lưu state**, chỉ tiện ích
