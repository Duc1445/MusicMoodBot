# 🎵 MusicMoodBot Frontend - Modular Architecture

## Overview

The frontend has been completely restructured into a **clean, modular architecture** similar to the backend. This makes it easy to fix bugs, add features, and maintain the codebase.

---

## 📁 New Directory Structure

```
frontend/
├── main.py                    # Main entry point (run this!)
├── test.py                    # Old monolithic file (kept for reference)
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── constants.py       # 🎨 All colors, moods, emojis, etc.
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py    # 🔐 Login/signup/logout logic
│   │   ├── chat_service.py    # 💬 Chat, mood, intensity logic
│   │   └── history_service.py # 📋 History loading & formatting
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── login_screen.py    # 📱 Login UI
│   │   ├── signup_screen.py   # 📝 Signup UI
│   │   ├── chat_screen.py     # 💭 Chat UI (main screen)
│   │   ├── history_screen.py  # 📖 History UI
│   │   └── profile_screen.py  # 👤 Profile UI
│   ├── components/
│   │   └── __init__.py        # (Reserved for reusable components)
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py         # 🛠️ Utility functions
│       └── state_manager.py   # 🔄 Global state management
```

---

## 🚀 How to Run

### New Way (Recommended)
```bash
cd frontend
python main.py
```

### Old Way (Still works)
```bash
cd frontend
python test.py
```

---

## 📖 Module Guide

### 1. **config/constants.py** 🎨
Centralized configuration - change everything here!

```python
COLORS = {...}              # All UI colors
MOODS = [...]               # 5 mood options
MOOD_EMOJI = {...}          # Emoji mapping for moods
INTENSITY_EMOJI = {...}     # Emoji mapping for intensity
SAMPLE_SONGS = [...]        # Demo songs
```

**When to edit:**
- Change colors/theme
- Add/remove moods
- Modify emoji associations

---

### 2. **services/auth_service.py** 🔐
User authentication logic

```python
AuthService.login(email, password)      # Login user
AuthService.signup(name, email, pw, pw) # Register user
AuthService.logout()                    # Logout user
```

**When to edit:**
- Add password hashing
- Add email validation
- Add 2FA/security features

---

### 3. **services/chat_service.py** 💬
Chat and mood recommendation logic

```python
ChatService.add_message(sender, kind, text, song)
ChatService.select_mood(mood)           # Handle mood selection
ChatService.select_intensity(intensity) # Handle intensity selection
ChatService.pick_song(mood)             # Get recommendation
ChatService.save_recommendation()       # Save to database
ChatService.reset()                     # Clear chat
```

**When to edit:**
- Change recommendation algorithm
- Add new chat features
- Modify mood/intensity logic

---

### 4. **services/history_service.py** 📋
User history loading and display

```python
HistoryService.load_user_history()      # Get all user's past chats
HistoryService.format_history_item(item) # Format for display
HistoryService.get_history_summary()    # Get stats
```

**When to edit:**
- Change history display format
- Add statistics
- Filter history

---

### 5. **screens/login_screen.py** 📱
Login UI with form validation

**When to edit:**
- Change login UI layout
- Add forgot password
- Add remember me checkbox

---

### 6. **screens/signup_screen.py** 📝
Signup UI with form validation

**When to edit:**
- Change signup UI layout
- Add terms & conditions
- Add email verification

---

### 7. **screens/chat_screen.py** 💭
Main chat interface

Key functions:
- `refresh_messages()` - Update message display
- `send_message()` - Handle user input
- `handle_mood_selection()` - Process mood choice
- `handle_emotion_click()` - Button click handler
- `make_recommendation()` - Generate suggestions

**When to edit:**
- Change chat UI layout
- Modify message bubbles
- Add new chat features

---

### 8. **screens/history_screen.py** 📖
Chat history display

**When to edit:**
- Change history layout
- Add filters/sorting
- Add export functionality

---

### 9. **screens/profile_screen.py** 👤
User profile and logout

**When to edit:**
- Add profile editing
- Add user statistics
- Add settings

---

### 10. **utils/state_manager.py** 🔄
Global application state

```python
app_state = AppState()
app_state.chat_messages    # Current chat messages
app_state.user_info        # Logged in user info
app_state.chat_flow        # Current chat state
```

**When to edit:**
- Add new global state
- Modify state initialization
- Add state reset logic

---

### 11. **utils/helpers.py** 🛠️
Utility functions

```python
_make_progress()           # Typing indicator
_ui_safe(page, fn)         # Safe UI updates
format_timestamp()         # Format dates
run_async()               # Async execution
```

**When to edit:**
- Add new helper functions
- Add UI utilities

---

## 🐛 Common Maintenance Tasks

### Fix a Login Bug
→ Edit `services/auth_service.py`

### Change Colors
→ Edit `config/constants.py` (COLORS dict)

### Fix Chat Message Flow
→ Edit `services/chat_service.py`

### Update Recommendation Algorithm
→ Edit `services/chat_service.py` (`pick_song` & `generate_reason`)

### Change UI Layout
→ Edit relevant `screens/*.py` file

### Add New Screen
1. Create `screens/new_screen.py`
2. Import in `main.py`
3. Add to screens dict
4. Add navigation callbacks

### Add New Mood/Intensity
→ Edit `config/constants.py`:
```python
MOOD_CHIPS = [..., "New Mood"]
MOOD_EMOJI = {..., "New Mood": "🆕"}
```

---

## 🧪 Testing Each Module

### Test Auth Service
```python
from src.services.auth_service import auth_service
success, msg = auth_service.login("testuser", "password123")
print(success, msg)
```

### Test Chat Service
```python
from src.services.chat_service import chat_service
chat_service.select_mood("Vui")
song = chat_service.pick_song("Vui")
print(song["name"])
```

### Test History Service
```python
from src.services.history_service import history_service
history = history_service.load_user_history()
summary = history_service.get_history_summary()
print(summary)
```

---

## 📊 File Dependencies

```
main.py
├── config/constants.py
├── screens/login_screen.py
│   └── services/auth_service.py
├── screens/signup_screen.py
│   └── services/auth_service.py
├── screens/chat_screen.py
│   ├── services/chat_service.py
│   └── utils/helpers.py
├── screens/history_screen.py
│   └── services/history_service.py
└── screens/profile_screen.py
    └── services/auth_service.py

services/auth_service.py
├── backend/database.py
└── utils/state_manager.py

services/chat_service.py
├── backend/database.py
├── config/constants.py
└── utils/state_manager.py

services/history_service.py
├── backend/database.py
└── utils/state_manager.py
```

---

## 🚀 Future Enhancements

### Easy to Add:
- [ ] Persistent user preferences
- [ ] Dark mode toggle
- [ ] Notification sounds
- [ ] Chat export to PDF
- [ ] User statistics dashboard
- [ ] Search in history
- [ ] Playlist recommendations
- [ ] Multi-language support

### Medium Complexity:
- [ ] Real-time collaborative playlists
- [ ] Friend recommendations
- [ ] Advanced mood analytics
- [ ] Custom mood creation

### Complex:
- [ ] ML-based recommendations
- [ ] Spotify integration
- [ ] Social sharing
- [ ] Mobile app version

---

## 📝 Notes

- **State Management**: All app state is in `utils/state_manager.py` - easy to debug
- **No Globals**: Services use dependency injection and state manager
- **Easy Testing**: Each module can be tested independently
- **Scalable**: Easy to add new features without touching existing code
- **Maintainable**: Clear separation of concerns

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Import errors | Make sure you're in `frontend/` directory |
| App won't start | Check `python main.py` vs `python test.py` |
| State not persisting | Check `state_manager.py` initialization |
| UI not updating | Check `refresh_messages()` calls in chat_screen |
| Database issues | Check backend is properly initialized |

---

## Version Info

- **Frontend Version**: 2.0 (Modular)
- **Structure**: Service-oriented architecture
- **Framework**: Flet
- **Status**: ✅ Production Ready

---

**Now you can easily find, fix, and enhance any feature!** 🎊
