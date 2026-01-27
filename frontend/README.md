# MusicMoodBot Frontend

## 📁 Cấu Trúc Dự Án

```
frontend/
├── backend/                    # Backend module (database, APIs)
│   ├── __init__.py
│   ├── database.py            # SQLite database operations
│   └── musicmood.db           # Database file
│
├── src/                       # Source code chính
│   ├── components/            # UI components tái sử dụng
│   │   ├── ui_components_pro.py
│   │   └── __init__.py
│   │
│   ├── config/                # Configuration files
│   │   ├── constants.py       # App constants
│   │   ├── theme_professional.py  # Theme colors & styles
│   │   └── __init__.py
│   │
│   ├── screens/               # App screens
│   │   ├── login_screen.py
│   │   ├── signup_screen.py
│   │   ├── chat_screen.py
│   │   ├── history_screen.py
│   │   ├── profile_screen.py
│   │   └── __init__.py
│   │
│   ├── services/              # Business logic layer
│   │   ├── auth_service.py    # Authentication
│   │   ├── chat_service.py    # Chat & recommendations
│   │   ├── history_service.py # History management
│   │   └── __init__.py
│   │
│   └── utils/                 # Utility functions
│       ├── state_manager.py   # Global state management
│       └── __init__.py
│
├── assets/                    # Static assets (images, icons)
├── docs/                      # Documentation
├── main.py                    # Application entry point
└── README.md                  # This file
```

## 🚀 Chạy Ứng Dụng

```bash
cd frontend
python main.py
```

## 📦 Dependencies

```bash
pip install flet
```

## 🎨 Kiến Trúc

### Backend Layer (`backend/`)
- **database.py**: Quản lý SQLite database với WAL mode
  - User management
  - Song catalog
  - Recommendations tracking
  - Chat history

### Service Layer (`src/services/`)
- **auth_service.py**: Xử lý đăng nhập, đăng ký
- **chat_service.py**: Gợi ý nhạc theo mood & intensity
- **history_service.py**: Quản lý lịch sử gợi ý

### UI Layer (`src/screens/` + `src/components/`)
- **Glassmorphism theme**: Hiện đại, trong suốt
- **Responsive design**: Tối ưu cho desktop
- **Clean components**: Tái sử dụng cao

## 📝 Database Schema

### Users
- user_id, username, email, password
- Stats: total_songs_listened, favorite_mood, favorite_artist

### Songs
- song_id, name, artist, genre
- suy_score, moods, reason

### Recommendations
- recommendation_id, user_id, song_id
- mood, intensity, timestamp

## 🛠️ Maintenance Guide

### Thêm Screen Mới
1. Tạo file trong `src/screens/new_screen.py`
2. Import trong `main.py`
3. Thêm navigation logic trong main()

### Thêm Service Mới
1. Tạo file trong `src/services/new_service.py`
2. Import database functions: `from backend.database import ...`
3. Implement business logic

### Sửa Theme
- Edit `src/config/theme_professional.py`
- Update colors, fonts, spacing constants
- All screens auto-update

### Debug Database
```python
# In Python console
from backend.database import _get_connection
conn = _get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
print(cursor.fetchall())
```

## 🗂️ Files Không Cần Thiết (Có thể xóa)
- `app.py` - Demo cũ
- `frontend.py` - Demo cũ
- `test.py` - Test cũ
- `demo_*.py` - Demo files
- `create_mascots.py` - Mascot system (đã remove)
- `test_components.py` - Test file
