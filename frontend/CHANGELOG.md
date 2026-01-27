# CHANGELOG

## [2.0.0] - 2026-01-27

### 🎉 Major Restructure

**Tổ chức lại cấu trúc dự án:**
- ✅ Tạo `frontend/backend/` - Backend module độc lập
- ✅ Di chuyển database.py và musicmood.db vào frontend/backend/
- ✅ Cập nhật imports trong tất cả services
- ✅ Xóa dependency vào backend folder ngoài

**Files mới:**
- `frontend/backend/__init__.py`
- `frontend/backend/README.md`
- `frontend/README.md` (updated)
- `frontend/requirements.txt`
- `frontend/.gitignore` (updated)

**Files đã xóa:**
- `app.py` (demo cũ)
- `frontend.py` (demo cũ)
- `test.py`, `demo_*.py`, `create_mascots.py`, `test_components.py`

### 🐛 Bug Fixes

**History Screen:**
- ✅ Fix sidebar buttons quá nhỏ (80px → 110px, 40px → 55px)
- ✅ Fix timezone display (thêm UTC+7 conversion)
- ✅ Fix hiển thị "None" → "N/A" cho mood/intensity null
- ✅ Fix query từ `chat_history` → `recommendations` table
- ✅ Fix field mapping: `name` → `song_name`, `artist` → `song_artist`

**Database:**
- ✅ Sử dụng `get_user_recommendations()` thay vì `get_user_chat_history()`
- ✅ Database path updated: `frontend/backend/musicmood.db`

### 📦 Cấu Trúc Mới

```
frontend/
├── backend/              # Backend module
│   ├── database.py
│   ├── musicmood.db
│   └── README.md
├── src/
│   ├── components/
│   ├── config/
│   ├── screens/
│   ├── services/
│   └── utils/
├── main.py
├── requirements.txt
└── README.md
```

### 🔧 Maintenance

- Tất cả imports đã được cập nhật
- Không còn dependency vào backend folder ngoài
- Self-contained frontend app
- Dễ deploy và maintain

---

## [1.0.0] - 2026-01-27

### Initial Release

- Professional glassmorphism UI
- Login/Signup screens
- Chat screen với mood & intensity selection
- History screen với recommendation cards
- Profile screen
- SQLite database backend
- Authentication system
- Music recommendation engine
