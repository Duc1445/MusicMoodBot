# 📦 src/ - Source Code

Thư mục chứa **toàn bộ code chính** của ứng dụng.

## 📁 Cấu trúc

```
src/
├── config/       ⚙️ Cấu hình & Hằng số
├── services/     🔧 Business logic & API calls
├── screens/      🎨 UI Screens (toàn bộ trang)
├── components/   🧩 Reusable UI Components
├── utils/        🛠️ Helper functions & Utilities
└── database/     💾 Database Operations
```

## 🎯 Mỗi folder làm gì?

- **config/** - Màu sắc, tâm trạng, emoji, cấu hình ứng dụng
- **services/** - Xử lý logic (auth, chat, history, v.v.)
- **screens/** - Các trang chính (login, chat, history, v.v.)
- **components/** - UI components dùng lại được
- **utils/** - Hàm tiện ích, state management
- **database/** - Kết nối & thao tác database

## 🚀 Cách import

```python
# Từ config
from src.config.constants import COLORS, MOODS

# Từ services
from src.services.chat_service import ChatService

# Từ screens
from src.screens.chat_screen import create_chat_screen

# Từ utils
from src.utils.state_manager import app_state
```
