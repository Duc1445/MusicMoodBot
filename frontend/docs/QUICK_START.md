## 🎵 MusicMood Bot - Quick Start Guide

### ⚡ Chạy App Ngay
```bash
cd h:\MusicMoodBot-frontend
python frontend/test.py
```

### 👤 Test Account
```
Email: testuser hoặc test@example.com
Password: password123
```
Hoặc tạo tài khoản mới qua nút "Đăng ký"

---

## 📊 Các Tính Năng Chính

### ✅ 1. Database (musicmood.db)
- Lưu trữ users, chat history, recommendations, songs
- Tự động tạo khi chạy app
- Dữ liệu được persist

### ✅ 2. Chat Feature
1. Chọn mood 😊😢🧠
2. Chọn intensity 🌿✨🔥
3. Nhận gợi ý bài hát
4. Try again hoặc đổi mood

### ✅ 3. History Tracking
- Mỗi action được lưu
- Xem lại tại screen "📋 Lịch Sử"
- Hiển thị mood, intensity, thời gian, bài hát

### ✅ 4. User Authentication
- Đăng ký: Email + Password + Tên
- Đăng nhập: Kiểm tra từ DB
- Đăng xuất: Quay lại login

### ✅ 5. All Buttons Working
| Menu Item | Function |
|-----------|----------|
| 💬 Chat | Về chat screen |
| 📋 Lịch Sử | Xem history |
| 👤 Hồ Sơ | Xem profile |
| 🧹 Reset | Làm mới chat |
| 🔓 Đăng Xuất | Logout |
| Try Again | Bài hát mới |
| Đổi Mood | Chọn lại mood |

---

## 🎯 User Flow

```
Login/Signup 
    ↓
Chat Screen (Select Mood & Intensity)
    ↓
Get Recommendation
    ↓
Try Again / Change Mood / View History
    ↓
Profile → Logout
```

---

## 📁 Files Created/Modified

```
✅ NEW: backend/database.py (Database operations)
✅ NEW: test_features.py (Unit tests)
✅ NEW: USAGE_GUIDE.md (Full documentation)
✅ NEW: FIXES_REPORT.md (Changes report)
✅ NEW: QUICK_START.md (This file)
✅ MODIFIED: frontend/test.py (Added DB integration)
```

---

## 🔧 Database Operations

### Create User
```python
from backend.database import add_user
user_id = add_user("username", "email@example.com", "password")
```

### Save Chat
```python
from backend.database import add_chat_history
add_chat_history(user_id, mood="Vui", intensity="Vừa")
```

### Get History
```python
from backend.database import get_user_chat_history
history = get_user_chat_history(user_id, limit=20)
```

### Save Recommendation
```python
from backend.database import add_recommendation
add_recommendation(user_id, song_id, mood="Vui", intensity="Vừa")
```

---

## 🧪 Testing

Run tests:
```bash
python test_features.py
```

Expected output:
```
✅ Database initialized
✅ User created
✅ Login successful
✅ Chat history saved
✅ History retrieved
✅ Songs loaded
✅ Recommendations saved
✅ Stats updated
```

---

## 🎵 Sample Songs (Auto-loaded)

1. **Mưa Tháng Sáu** - Văn Mai Hương (8.8/10)
2. **Có Chàng Trai Viết Lên Cây** - Phan Mạnh Quỳnh (7.2/10)
3. **Ngày Chưa Giông Bão** - Bùi Lan Hương (7.9/10)
4. **Cô Gái M52** - HuyR x Tùng Viu (2.5/10)
5. **Bước Qua Nhau** - Vũ. (6.9/10)
6. **Nơi Này Có Anh** - Sơn Tùng M-TP (3.8/10)

---

## 🐛 Troubleshooting

### App không chạy?
```bash
pip install flet
python frontend/test.py
```

### Database error?
```bash
python backend/database.py
# Tạo fresh database
```

### Can't login?
- Kiểm tra email/password
- Hoặc tạo account mới

---

## 📈 Future Enhancements

- [ ] Hashing password
- [ ] API backend
- [ ] More songs database
- [ ] AI mood detection
- [ ] Playlist generation
- [ ] Social sharing

---

## 💡 Tips

1. Mỗi login = Một session mới
2. History được lưu per user
3. Buttons có click animation
4. Database auto-backup (SQLite)

---

**Status:** ✅ Working  
**Last Updated:** 22/01/2026  
**Version:** 1.0.1
