# API Documentation

> MusicMoodBot REST API v1.0

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Authentication](#2-authentication)
3. [Endpoints](#3-endpoints)
4. [Error Handling](#4-error-handling)
5. [Rate Limiting](#5-rate-limiting)

---

## 1. Giới thiệu

### 1.1 Base URL

```
Development: http://localhost:8000
Production:  https://api.musicmoodbot.com
```

### 1.2 Content-Type

Tất cả request và response sử dụng `application/json`

### 1.3 Authentication Header

```http
Authorization: Bearer <access_token>
```

---

## 2. Authentication

### 2.1 POST /api/auth/signup

Đăng ký tài khoản mới.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "status": "success",
  "user_id": "integer"
}
```

**Response 400:**
```json
{
  "status": "error",
  "detail": "Username already exists"
}
```

---

### 2.2 POST /api/auth/login

Đăng nhập và nhận JWT token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "status": "success",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 1,
  "username": "duc"
}
```

**Response 401:**
```json
{
  "status": "error",
  "detail": "Invalid credentials"
}
```

---

### 2.3 GET /api/auth/verify

Xác thực token còn hiệu lực.

**Headers:**
```http
Authorization: Bearer <token>
```

**Response 200:**
```json
{
  "valid": true,
  "user_id": 1,
  "username": "duc"
}
```

---

## 3. Endpoints

### 3.1 Health Check

#### GET /health

Kiểm tra trạng thái server.

**Response 200:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-02-01T12:00:00Z"
}
```

---

### 3.2 Mood Detection

#### POST /api/recommendations/detect-mood

Phát hiện tâm trạng từ văn bản tiếng Việt.

**Request Body:**
```json
{
  "text": "Hôm nay tôi cảm thấy rất vui vẻ!"
}
```

**Response 200:**
```json
{
  "status": "success",
  "mood": "happy",
  "intensity": "medium",
  "confidence": 0.85,
  "emotions": ["joy", "excited"]
}
```

**Mood Values:**
- `happy` - Vui vẻ
- `sad` - Buồn
- `energetic` - Năng động
- `calm` - Bình tĩnh
- `romantic` - Lãng mạn
- `angry` - Tức giận
- `melancholic` - U sầu
- `uplifting` - Phấn khích
- `peaceful` - Yên bình
- `neutral` - Trung tính

**Intensity Values:**
- `low`
- `medium`
- `high`

---

### 3.3 Song Recommendations

#### POST /api/recommendations/smart

Gợi ý bài hát thông minh dựa trên text.

**Request Body:**
```json
{
  "text": "Tôi muốn nghe nhạc buồn",
  "limit": 10,
  "user_id": 1
}
```

**Response 200:**
```json
{
  "status": "success",
  "detected_mood": "sad",
  "detected_intensity": "medium",
  "songs": [
    {
      "id": 123,
      "title": "Buồn",
      "artist": "Đức Phúc",
      "mood": "sad",
      "intensity": "medium",
      "valence": 0.25,
      "energy": 0.35,
      "key": "C",
      "camelot": "8B",
      "spotify_id": "abc123"
    }
  ],
  "narrative": "Dựa trên tâm trạng của bạn..."
}
```

---

#### GET /api/moods/songs/by-mood/{mood}

Lấy danh sách bài hát theo mood.

**Path Parameters:**
- `mood` (required): Tên mood (happy, sad, etc.)

**Query Parameters:**
- `intensity` (optional): low, medium, high
- `limit` (optional): Số lượng kết quả (default: 20)
- `offset` (optional): Vị trí bắt đầu (default: 0)

**Response 200:**
```json
{
  "status": "success",
  "mood": "happy",
  "total_count": 150,
  "songs": [
    {
      "id": 1,
      "title": "Happy",
      "artist": "Pharrell Williams",
      "mood": "happy",
      "intensity": "high",
      "valence": 0.92,
      "energy": 0.85
    }
  ]
}
```

---

### 3.4 Search

#### GET /api/search/

Tìm kiếm bài hát (hỗ trợ tiếng Việt).

**Query Parameters:**
- `q` (required): Từ khóa tìm kiếm
- `limit` (optional): Số kết quả (default: 20)

**Response 200:**
```json
{
  "status": "success",
  "query": "em của ngày hôm qua",
  "total_results": 5,
  "songs": [
    {
      "id": 456,
      "title": "Em Của Ngày Hôm Qua",
      "artist": "Sơn Tùng M-TP",
      "match_score": 0.95
    }
  ]
}
```

---

### 3.5 Playlist Generation

#### POST /api/recommendations/playlist

Tạo playlist với harmonic mixing.

**Request Body:**
```json
{
  "seed_song_id": 123,
  "length": 10,
  "mood_progression": "maintain"
}
```

**mood_progression Values:**
- `maintain` - Giữ nguyên mood
- `uplift` - Chuyển sang vui hơn
- `wind_down` - Chuyển sang bình tĩnh

**Response 200:**
```json
{
  "status": "success",
  "playlist": {
    "name": "Curated Mix",
    "total_duration_ms": 3600000,
    "songs": [
      {
        "id": 123,
        "title": "Song 1",
        "artist": "Artist 1",
        "camelot": "8A",
        "transition_quality": 1.0
      },
      {
        "id": 124,
        "title": "Song 2",
        "artist": "Artist 2",
        "camelot": "8B",
        "transition_quality": 0.95
      }
    ]
  }
}
```

---

### 3.6 User History

#### GET /api/history/{user_id}

Lấy lịch sử nghe nhạc.

**Response 200:**
```json
{
  "status": "success",
  "user_id": 1,
  "history": [
    {
      "song_id": 123,
      "title": "Song Title",
      "artist": "Artist",
      "played_at": "2025-02-01T10:00:00Z",
      "duration_played": 180
    }
  ]
}
```

---

#### POST /api/history/add

Thêm bài hát vào lịch sử.

**Request Body:**
```json
{
  "user_id": 1,
  "song_id": 123,
  "duration_played": 180,
  "action": "play"
}
```

**action Values:**
- `play` - Nghe bài hát
- `skip` - Bỏ qua
- `like` - Thích
- `dislike` - Không thích

---

## 4. Error Handling

### 4.1 Error Response Format

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "detail": "Human readable message",
  "timestamp": "2025-02-01T12:00:00Z"
}
```

### 4.2 Common Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 400 | `INVALID_REQUEST` | Request body không hợp lệ |
| 401 | `UNAUTHORIZED` | Token không hợp lệ hoặc hết hạn |
| 403 | `FORBIDDEN` | Không có quyền truy cập |
| 404 | `NOT_FOUND` | Resource không tồn tại |
| 422 | `VALIDATION_ERROR` | Lỗi validation dữ liệu |
| 429 | `RATE_LIMITED` | Quá giới hạn request |
| 500 | `INTERNAL_ERROR` | Lỗi server |

---

## 5. Rate Limiting

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Authentication | 10 requests | 1 minute |
| Search | 60 requests | 1 minute |
| Recommendations | 30 requests | 1 minute |
| General | 100 requests | 1 minute |

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706788800
```

---

## Appendix

### A. Full Mood List

| Mood | Emoji | Description | Valence Range | Energy Range |
|------|-------|-------------|---------------|--------------|
| happy | 😊 | Vui vẻ | 0.7 - 1.0 | 0.5 - 0.8 |
| sad | 😢 | Buồn | 0.0 - 0.3 | 0.2 - 0.5 |
| energetic | ⚡ | Năng động | 0.5 - 0.8 | 0.8 - 1.0 |
| calm | 😌 | Bình tĩnh | 0.4 - 0.6 | 0.1 - 0.4 |
| romantic | 💕 | Lãng mạn | 0.5 - 0.8 | 0.3 - 0.5 |
| angry | 😡 | Tức giận | 0.1 - 0.4 | 0.7 - 1.0 |
| melancholic | 🌧️ | U sầu | 0.2 - 0.4 | 0.2 - 0.4 |
| uplifting | 🌟 | Phấn khích | 0.6 - 0.9 | 0.6 - 0.9 |
| peaceful | 🕊️ | Yên bình | 0.5 - 0.7 | 0.1 - 0.3 |
| neutral | 😐 | Trung tính | 0.4 - 0.6 | 0.4 - 0.6 |

---

*Document Version: 1.0.0*
*Last Updated: February 2025*
