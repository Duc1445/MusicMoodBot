# 🎯 Modular Frontend - Quick Start Guide

## ✨ What's New?

Your frontend has been **completely restructured** from a single 790-line file into a **professional modular architecture** with:
- ✅ **Services Layer** - Business logic separated from UI
- ✅ **Configuration Module** - All constants in one place
- ✅ **State Management** - Centralized global state
- ✅ **Screen Components** - Each screen isolated
- ✅ **Utilities** - Reusable helper functions

---

## 🚀 How to Run

```bash
cd frontend
python main.py
```

**That's it!** The app will start with the login screen.

---

## 📚 Module Breakdown

### 1️⃣ **Config** (`src/config/constants.py`)
Everything you want to change globally:
- Colors
- Moods & Emojis
- Sample songs
- App constants

### 2️⃣ **Services** (`src/services/`)
Business logic - separate from UI:
- **auth_service.py** - Login/Signup/Logout
- **chat_service.py** - Chat & Recommendations
- **history_service.py** - User history

### 3️⃣ **Screens** (`src/screens/`)
UI Components - one file per screen:
- **login_screen.py** - Login page
- **signup_screen.py** - Signup page
- **chat_screen.py** - Main chat interface
- **history_screen.py** - Chat history viewer
- **profile_screen.py** - User profile

### 4️⃣ **Utils** (`src/utils/`)
Helper functions:
- **state_manager.py** - Global state
- **helpers.py** - Utility functions

---

## 🔧 Common Tasks

### Change App Colors
Edit `src/config/constants.py`:
```python
COLORS = {
    "cream_bg": "#F6F3EA",  # ← Change here
    "white": "#FFFFFF",
    ...
}
```

### Add a New Mood
Edit `src/config/constants.py`:
```python
MOOD_CHIPS = ["Vui", "Buồn", "Suy tư", "Chill", "Năng lượng", "Bình tĩnh"]  # ← Add here
MOOD_EMOJI = {
    ...
    "Bình tĩnh": "☮️"  # ← Add emoji
}
```

### Fix Login Bug
Edit `src/services/auth_service.py` → `AuthService.login()` method

### Fix Chat Recommendation Logic
Edit `src/services/chat_service.py` → `ChatService.pick_song()` method

### Change Chat UI Layout
Edit `src/screens/chat_screen.py` → modify the `create_chat_screen()` function

### Add a New Screen
1. Create `src/screens/new_screen.py`
2. Add function `create_new_screen(page, ...)`
3. Edit `frontend/main.py` - add to imports and screens dict
4. Add navigation callbacks

---

## 📊 File Size Comparison

| Type | Lines | Files |
|------|-------|-------|
| **Old** (Monolithic) | 790 | 1 |
| **New** (Modular) | ~900 total | 12 |
| **Benefit** | 🎯 Each file = 50-80 lines | Easy to find & fix |

---

## 🐛 Debugging

### To Debug Auth
```python
# Open Python terminal
from src.services.auth_service import auth_service
success, msg = auth_service.login("testuser", "password123")
print(success, msg)
```

### To Check Global State
```python
from src.utils.state_manager import app_state
print(app_state.user_info)
print(app_state.chat_flow)
print(app_state.chat_messages)
```

### To Test Chat Logic
```python
from src.services.chat_service import chat_service
song = chat_service.pick_song("Vui")
print(f"Song: {song['name']} by {song['artist']}")
```

---

## 📖 Find What You Need

| I want to... | Edit this file |
|--------------|------------------|
| Change colors | `src/config/constants.py` |
| Add a mood | `src/config/constants.py` |
| Fix login | `src/services/auth_service.py` |
| Fix chat flow | `src/services/chat_service.py` |
| Fix recommendations | `src/services/chat_service.py` |
| Change login UI | `src/screens/login_screen.py` |
| Change chat UI | `src/screens/chat_screen.py` |
| Fix history display | `src/services/history_service.py` |
| Add global state | `src/utils/state_manager.py` |

---

## ✅ Verification

All files compile correctly:
```
✅ main.py
✅ src/config/constants.py
✅ src/services/auth_service.py
✅ src/services/chat_service.py
✅ src/services/history_service.py
✅ src/screens/login_screen.py
✅ src/screens/signup_screen.py
✅ src/screens/chat_screen.py
✅ src/screens/history_screen.py
✅ src/screens/profile_screen.py
✅ src/utils/state_manager.py
✅ src/utils/helpers.py
```

---

## 💡 Benefits of New Architecture

1. **Easy to Find**: Each concern has its own file/folder
2. **Easy to Fix**: Small, focused files = fewer bugs
3. **Easy to Test**: Services can be tested independently
4. **Easy to Extend**: Add features without touching existing code
5. **Easy to Maintain**: Clear structure and dependencies
6. **Professional**: Follows backend architecture pattern

---

## 🎓 Learning Path

**Start Here:**
1. Read this guide
2. Look at `FRONTEND_ARCHITECTURE.md` for detailed info
3. Run `python main.py`
4. Try editing `src/config/constants.py` (change a color)
5. Re-run to see changes

**Then:**
1. Look at `src/services/auth_service.py`
2. Look at `src/services/chat_service.py`
3. Look at `src/screens/chat_screen.py`

---

## 🆘 Troubleshooting

| Problem | Fix |
|---------|-----|
| Import error | Make sure you're in `frontend/` directory |
| File not found | Check path is relative to `frontend/` |
| State not saving | Check `state_manager.py` |
| UI not updating | Add `page.update()` or `refresh_messages()` |

---

## 📞 Quick Reference

```bash
# Run the app
python frontend/main.py

# Check syntax
python -m py_compile frontend/src/services/chat_service.py

# Test a module
python -c "from src.services.auth_service import auth_service; print('OK')"
```

---

**You're all set! Start developing!** 🚀
