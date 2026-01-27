# 💾 database/ - Database Operations

Chứa **code liên quan database** - kết nối, queries, v.v.

## 📝 Lưu ý

Hiện tại, database operations được quản lý từ **backend**.

Frontend gọi backend qua API:

```python
from backend.database import add_user, get_user, add_chat_history
```

## 📋 Nếu cần local database operations

Tạo files ở đây để:

- Lưu cache local
- Offline mode
- Sync với backend

## 🎨 Ví dụ có thể tạo

```python
# local_cache.py
def cache_user_data(user):
    """Lưu user data vào local"""

def get_cached_user():
    """Lấy user data từ cache"""

# db_sync.py
def sync_with_backend():
    """Đồng bộ local database với backend"""
```

## ⚠️ Lưu ý

- Backend xử lý **main database** (SQLite)
- Frontend chỉ gọi backend API
- Chỉ tạo files ở đây nếu cần **local caching/offline**
