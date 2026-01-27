# 🔧 services/ - Business Logic & API

Chứa **logic xử lý chính** - xác thực, chat, lịch sử, v.v.

## 📄 Files

- **auth_service.py** - Đăng nhập, đăng ký, đăng xuất
- **chat_service.py** - Xử lý chat, chọn tâm trạng, gợi ý bài hát
- **history_service.py** - Tải lịch sử chat

## 🎯 Mỗi service làm gì?

### auth_service.py

```python
# Đăng nhập
AuthService.login(email, password) → (success, message)

# Đăng ký
AuthService.signup(name, email, password) → (success, message)

# Đăng xuất
AuthService.logout()
```

### chat_service.py

```python
# Thêm tin nhắn
ChatService.add_message(sender, kind, text, song)

# Chọn tâm trạng
ChatService.select_mood(mood) → bot_response

# Chọn cường độ
ChatService.select_intensity(intensity) → recommendation

# Gợi ý bài hát
ChatService.pick_song(mood) → song_dict
```

### history_service.py

```python
# Tải lịch sử
HistoryService.load_user_history() → list

# Format lịch sử
HistoryService.format_history_item(item) → string

# Thống kê
HistoryService.get_history_summary() → dict
```

## 🎨 Khi nào edit?

- Thay đổi logic đăng nhập/đăng ký
- Sửa lỗi chat
- Thay đổi cách gợi ý bài hát
- Thêm tính năng mới

## ⚠️ Lưu ý

- Các service **không phụ thuộc vào UI**
- Có thể test từng service riêng lẻ
- Trả về `(success, message)` hoặc data dict
