# MusicMoodBot

> Hệ thống gợi ý nhạc theo tâm trạng sử dụng Machine Learning và NLP

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![Flet](https://img.shields.io/badge/Flet-0.80-purple.svg)](https://flet.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Cài đặt](#3-cài-đặt)
4. [Cấu trúc thư mục](#4-cấu-trúc-thư-mục)
5. [API Reference](#5-api-reference)
6. [Hướng dẫn sử dụng](#6-hướng-dẫn-sử-dụng)
7. [Testing](#7-testing)
8. [Deployment](#8-deployment)

---

## 1. Tổng quan

### 1.1 Mô tả dự án

MusicMoodBot là ứng dụng chatbot thông minh giúp người dùng tìm kiếm và nhận gợi ý bài hát phù hợp với tâm trạng hiện tại. Hệ thống sử dụng:

- **Mood Engine v5.2**: Thuật toán phân tích tâm trạng dựa trên Valence-Arousal (VA) space
- **Text Mood Detector**: Phát hiện tâm trạng từ văn bản tiếng Việt bằng NLP
- **Curator Engine**: Tạo playlist thông minh với harmonic mixing (Camelot wheel)

### 1.2 Tính năng chính

| Tính năng | Mô tả | Module |
|-----------|-------|--------|
| Mood Detection | Phát hiện tâm trạng từ text tiếng Việt | `text_mood_detector.py` |
| Song Recommendation | Gợi ý bài hát theo mood + intensity | `mood_engine.py` |
| Playlist Generation | Tạo playlist với transition mượt | `curator_engine.py` |
| User Preferences | Học thói quen người dùng | `preference_model.py` |
| Vietnamese Search | Tìm kiếm hỗ trợ tiếng Việt | `tfidf_search.py` |

### 1.3 Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend API | FastAPI | 0.115.0 |
| Frontend UI | Flet | 0.80.2 |
| Database | SQLite (WAL mode) | 3.x |
| HTTP Client | httpx | 0.28.1 |
| Authentication | JWT (PyJWT) | 2.11.0 |
| ML/NLP | Custom algorithms | v5.2 |

---

## 2. Kiến trúc hệ thống

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Flet Desktop App                      │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │    │
│  │  │  Login   │  │   Chat   │  │ History  │  │ Profile  │ │    │
│  │  │  Screen  │  │  Screen  │  │  Screen  │  │  Screen  │ │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP/REST
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Server                        │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │    │
│  │  │ /auth  │ │ /moods │ │ /songs │ │/search │ │ /recs  │ │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │  MoodEngine   │  │ CuratorEngine │  │ TextDetector  │        │
│  │    v5.2       │  │     v2.0      │  │     v1.0      │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │    songs      │  │    users      │  │   history     │        │
│  │   (2000+)     │  │               │  │               │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
│                        SQLite (WAL)                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Layer Responsibilities

| Layer | Responsibility | Components |
|-------|----------------|------------|
| Client | UI/UX, User interaction | Flet screens, components |
| API | HTTP routing, validation, auth | FastAPI routes, JWT middleware |
| Service | Business logic, ML algorithms | MoodEngine, CuratorEngine, TextDetector |
| Data | Persistence, CRUD operations | Repositories, SQLite |

---

## 3. Cài đặt

### 3.1 Yêu cầu hệ thống

- Python 3.12+
- Windows 10/11, macOS, hoặc Linux
- 4GB RAM (khuyến nghị 8GB)
- 500MB disk space

### 3.2 Cài đặt nhanh

```bash
# Clone repository
git clone https://github.com/Duc1445/MusicMoodBot.git
cd MusicMoodBot

# Tạo virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python run_app.py
```

### 3.3 Environment Variables

Tạo file `.env` tại thư mục gốc:

```env
# API Configuration
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30

# JWT Secret (production: use strong random key)
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Debug mode
DEBUG=false
```

---

## 4. Cấu trúc thư mục

```
MMB_FRONTBACK/
├── run_app.py                 # Entry point
├── requirements.txt           # Dependencies
│
├── shared/                    # Shared constants & types
│   ├── constants.py           
│   └── types.py               
│
├── backend/                   # FastAPI Backend
│   ├── main.py                
│   ├── core/                  # ML Engine exports
│   ├── repositories/          # Data access layer
│   └── src/
│       ├── api/               # API routes
│       ├── database/          # SQLite
│       ├── pipelines/         # ML/NLP algorithms
│       └── services/          
│
├── frontend/                  # Flet Frontend
│   ├── main.py                
│   ├── state/                 # State management
│   ├── infrastructure/        # HTTP client
│   └── src/
│       ├── screens/           
│       ├── components/        
│       └── services/          
│
└── docs/                      # Documentation
```

---

## 5. API Reference

Chi tiết API xem tại: [docs/API.md](docs/API.md)

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Đăng nhập |
| POST | `/api/auth/signup` | Đăng ký |
| POST | `/api/recommendations/detect-mood` | Phát hiện mood từ text |
| POST | `/api/recommendations/smart` | Gợi ý thông minh |
| GET | `/api/moods/songs/by-mood/{mood}` | Lấy songs theo mood |
| GET | `/api/search/?q={query}` | Tìm kiếm |
| GET | `/health` | Health check |

---

## 6. Hướng dẫn sử dụng

### 6.1 Chạy ứng dụng

```bash
python run_app.py
```

### 6.2 Truy cập

- **Frontend**: Cửa sổ Flet tự động mở
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 7. Testing

```bash
# Chạy tất cả tests
python -m pytest

# Với coverage
python -m pytest --cov=backend
```

---

## 8. Deployment

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Use strong `JWT_SECRET_KEY`
- [ ] Configure HTTPS
- [ ] Set up database backups

---

## License

MIT License

## Contributors

- **Duc1445** - Lead Developer

---

*Last updated: February 2026*
