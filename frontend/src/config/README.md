# ⚙️ config/ - Cấu hình & Hằng số

Chứa **tất cả cấu hình** của ứng dụng - màu sắc, tâm trạng, emoji, v.v.

## 📄 Files

- **constants.py** - Tất cả hằng số (colors, moods, emojis, v.v.)

## 📝 Nội dung

```python
# Màu sắc
COLORS = {
    "cream_bg": "#FFFAF0",
    "white": "#FFFFFF",
    ...
}

# Tâm trạng
MOODS = ["Vui", "Buồn", "Suy tư", "Chill", "Năng lượng"]

# Emoji
MOOD_EMOJI = {
    "Vui": "😊",
    ...
}
```

## 🎨 Khi nào edit?

- Đổi màu sắc giao diện
- Thêm/xóa tâm trạng
- Thêm emoji mới
- Thay đổi cấu hình toàn cục

## ⚠️ Lưu ý

Không đặt **logic** vào đây, chỉ **hằng số** thuần.
