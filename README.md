# 🎵 Music Mood Bot (MMB)

**Hệ thống gợi ý nhạc thông minh dựa trên tâm trạng với AI đàm thoại.**

Kết hợp FastAPI backend + Flet UI + SQLite database + Google Gemini AI để gợi ý nhạc theo tâm trạng người dùng.

---

## ⚡ Khởi Động Nhanh

```bash
# 1. Cài đặt thư viện
pip install -r requirements.txt

# 2. Chạy ứng dụng (Backend + Frontend cùng lúc)
python run_app.py

# Hoặc chạy riêng:
# Backend: python backend/run_server.py  (http://localhost:8000/api/docs)
# Frontend: python frontend/main.py
```

---

## 🏗️ Cấu Trúc Dự Án

| Thành Phần | Công Nghệ | Entry Point |
|------------|-----------|-------------|
| **Backend** | FastAPI | `backend/run_server.py` |
| **Frontend** | Flet | `frontend/main.py` |
| **Tích Hợp** | Python | `run_app.py` |
| **Database** | SQLite | `backend/src/database/music.db` |
| **ML Engine** | Python | Mô hình Valence-Arousal |
| **AI Chat** | Gemini | Google Generative AI |

---

## 🎯 Tính Năng

### ✅ Phân Tích Nhạc
- 🎵 Dự đoán tâm trạng (vui, buồn, stress, năng động, suy tư)
- 🔍 Tìm kiếm thông minh TF-IDF v2.0 với hỗ trợ tiếng Việt
- 📊 So khớp độ tương đồng bài hát

### ✅ AI Đàm Thoại
- 🤖 Bot hỏi 3-4 câu để hiểu rõ tâm trạng
- 💬 Tích hợp Google Gemini AI
- 🎭 Phân tích ngữ cảnh cuộc hội thoại
- 😊 Lời chào: "Xin chào, tớ là MMB, ngày hôm nay của bạn thế nào?"

### ✅ TF-IDF Search v2.0
- 🎯 Nhận diện ý định (tìm tên/ca sĩ/mood/genre/tương tự)
- ⚡ Fast-path cho exact match
- 🔄 LRU Cache cho 100 query gần nhất
- ✏️ Tự động sửa lỗi chính tả tiếng Việt
- 📈 Vectorized cosine similarity (nhanh gấp 10-50x)
- 🎚️ Trọng số: 60% TF-IDF + 30% Exact + 10% Fuzzy

### ✅ Gợi Ý Thông Minh
- 📈 Gợi ý cá nhân hóa theo tâm trạng
- ⏰ Gợi ý theo thời gian trong ngày
- 🎭 Lập kế hoạch chuyển đổi tâm trạng

### ✅ Quản Lý Người Dùng
- 👤 Tài khoản người dùng (đăng nhập/đăng ký)
- 📝 Lịch sử nghe nhạc
- ❤️ Học sở thích
- 📋 Quản lý playlist

### ✅ Dữ Liệu
- 💾 30+ bài hát được tải sẵn
- 📊 Thuộc tính ML (valence, arousal, energy, v.v.)
- 🔐 Xác thực an toàn

---

## 🛠️ Các Lệnh

### Chạy Ứng Dụng
```bash
# Chạy cả Backend + Frontend
python run_app.py
```

### Backend
```bash
# Chạy server riêng
python backend/run_server.py

# Test backend
pytest backend/src/test/
```

### Frontend
```bash
# Chạy UI riêng
python frontend/main.py
```

---

## 📁 Cấu Trúc File

```
run_app.py               ← Chạy cả 2 (Backend + Frontend)

backend/
├── main.py              ← FastAPI app
├── run_server.py        ← Khởi động server
├── .env                 ← Cấu hình
└── src/
    ├── api/             ← API endpoints
    ├── database/        ← DB + music.db
    ├── pipelines/       ← Mô hình ML + text_mood_detector
    ├── search/          ← TF-IDF Search v2.0
    ├── services/        ← Xử lý nghiệp vụ
    └── repo/            ← Truy cập dữ liệu

frontend/
├── main.py              ← Entry point UI
└── src/
    ├── screens/         ← Các trang (chat, history, v.v.)
    ├── components/      ← UI widgets
    ├── services/        ← Gọi Backend API
    └── config/          ← Themes & hằng số
```

---

## 📦 Database

**Chính**: `backend/src/database/music.db` (76KB)
- 30 bài hát với thuộc tính tâm trạng
- 2 tài khoản người dùng
- 11 bảng (songs, users, history, v.v.)

---

## 🔧 Cấu Hình

Tạo/sửa `backend/.env`:
```env
DATABASE_PATH=music.db
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
MOOD_ENGINE_AUTO_FIT=true
SEARCH_TOP_K=10
GEMINI_API_KEY=your_gemini_api_key
```

---

## 📚 Tài Liệu

- [backend/README.md](backend/README.md) - Hướng dẫn Backend
- [frontend/README.md](frontend/README.md) - Hướng dẫn Frontend
- [backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md) - Tài liệu API

---

## 🚀 Trạng Thái

✅ **Sẵn Sàng Production**
- Database tối ưu & hợp nhất
- Mô hình ML hoạt động
- API endpoints đã test
- UI responsive
- AI đàm thoại tích hợp
- TF-IDF v2.0 nâng cấp

---

## 📊 Công Nghệ

| Lớp | Công Nghệ |
|-----|-----------|
| Frontend | Flet (Python) |
| Backend | FastAPI |
| Database | SQLite3 |
| ML | Scikit-learn, NumPy |
| AI Chat | Google Gemini API |
| Search | TF-IDF v2.0 + Cosine Similarity |
| NLP | Xử lý tiếng Việt |

---

## 👨‍💻 Tác Giả

**Repository**: [github.com/Duc1445/MusicMoodBot](https://github.com/Duc1445/MusicMoodBot)

---

**Cập Nhật**: 2025-01-28 | **Phiên Bản**: 3.0.0
