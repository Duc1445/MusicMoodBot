# Music Mood Prediction API v2.1.0

## Tổng quan

Đây là phiên bản mở rộng đáng kể của Music Mood Prediction API với nhiều tính năng mới.

## 🆕 Tính năng mới trong v2.1.0

### 1. **Time-Based Recommendations** (Đề xuất theo thời gian)
- Đề xuất nhạc dựa trên thời điểm trong ngày
- Đề xuất theo hoạt động (tập thể dục, làm việc, thư giãn...)
- Lên lịch nhạc cho cả ngày
- Tạo playlist theo thời lượng

```
GET  /api/v2/recommendations/now           - Đề xuất cho thời điểm hiện tại
POST /api/v2/recommendations/activity      - Đề xuất theo hoạt động
GET  /api/v2/recommendations/hour/{hour}   - Đề xuất theo giờ cụ thể
POST /api/v2/recommendations/day-schedule  - Lịch nhạc cả ngày
POST /api/v2/recommendations/duration      - Playlist theo thời lượng
POST /api/v2/recommendations/weather       - Đề xuất theo thời tiết
```

### 2. **User Preference Learning** (Học sở thích người dùng)
- Ghi nhận tương tác người dùng
- Xây dựng profile sở thích
- Đề xuất cá nhân hóa
- Tìm người dùng tương tự

```
POST /api/v2/users/interactions              - Ghi nhận tương tác
GET  /api/v2/users/{id}/preferences          - Xem profile sở thích
POST /api/v2/users/personalized-recommendations - Đề xuất cá nhân hóa
GET  /api/v2/users/{id}/similar-users        - Tìm người dùng tương tự
GET  /api/v2/users/{id}/stats                - Thống kê người dùng
```

### 3. **Export/Import & Backup**
- Xuất dữ liệu ra JSON/CSV
- Nhập dữ liệu từ file
- Backup và restore database

```
POST /api/v2/export/songs    - Xuất bài hát
POST /api/v2/import/songs    - Nhập bài hát
POST /api/v2/backup/create   - Tạo backup
GET  /api/v2/backup/list     - Danh sách backup
GET  /api/v2/export/list     - Danh sách file xuất
```

### 4. **Database Optimization**
- Connection pooling
- Query caching
- Database optimization (VACUUM, ANALYZE)

```
GET  /api/v2/db/stats     - Thống kê connection pool
POST /api/v2/db/optimize  - Tối ưu database
```

### 5. **Event System** (Hệ thống sự kiện)
- Publish-subscribe pattern
- Notification service
- Activity logging

### 6. **Smart Queue** (Hàng đợi thông minh)
- Auto-queue bài hát tương tự
- Smart shuffle với constraints
- Học từ hành vi skip
- Lịch sử phát

---

## 📁 Cấu trúc Module mới

```
backend/src/
├── services/
│   ├── cache_service.py        # LRU cache với TTL
│   ├── playlist_service.py     # Quản lý playlist
│   ├── analytics_service.py    # Phân tích & insights
│   ├── time_recommender.py     # Đề xuất theo thời gian
│   ├── preference_learning.py  # Học sở thích
│   ├── export_service.py       # Xuất/nhập dữ liệu
│   ├── event_system.py         # Hệ thống sự kiện
│   └── queue_service.py        # Hàng đợi thông minh
├── pipelines/
│   ├── mood_transition.py      # Chuyển đổi mood
│   └── song_similarity.py      # Độ tương đồng bài hát
├── repo/
│   └── db_pool.py              # Connection pooling
└── api/
    └── extended_api.py         # 40+ API endpoints mới
```

---

## 🔧 API Endpoints

### Mood & Search (v1)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | /api/moods/moods | Danh sách mood |
| POST | /api/moods/update-all | Cập nhật mood cho tất cả bài |
| GET | /api/moods/songs/by-mood/{mood} | Lọc bài theo mood |
| GET | /api/moods/stats | Thống kê mood |
| GET | /api/moods/search | Tìm kiếm TF-IDF |
| POST | /api/moods/smart-recommend | Đề xuất thông minh |

### Playlists (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | /api/v2/playlists | Tạo playlist |
| GET | /api/v2/playlists/{id} | Lấy playlist |
| PUT | /api/v2/playlists/{id} | Cập nhật playlist |
| DELETE | /api/v2/playlists/{id} | Xóa playlist |
| POST | /api/v2/playlists/{id}/songs | Thêm bài vào playlist |
| DELETE | /api/v2/playlists/{id}/songs/{song_id} | Xóa bài khỏi playlist |
| POST | /api/v2/playlists/auto/mood/{mood} | Tạo playlist tự động theo mood |

### Similarity (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | /api/v2/songs/{id}/similar | Tìm bài tương tự |
| GET | /api/v2/songs/{id}/similar/diverse | Tìm bài đa dạng tương tự |

### Analytics (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | /api/v2/analytics/songs | Thống kê bài hát |
| GET | /api/v2/analytics/moods | Phân bố mood |
| GET | /api/v2/analytics/dashboard | Dashboard tổng hợp |
| GET | /api/v2/analytics/insights | Insights AI |

### Mood Transition (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | /api/v2/mood/transition | Tính đường chuyển mood |
| POST | /api/v2/mood/journey | Hành trình mood |
| GET | /api/v2/mood/{mood}/suggestions | Gợi ý mood tiếp theo |

### Time-Based (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | /api/v2/recommendations/now | Đề xuất cho hiện tại |
| POST | /api/v2/recommendations/activity | Theo hoạt động |
| GET | /api/v2/recommendations/hour/{hour} | Theo giờ |
| POST | /api/v2/recommendations/day-schedule | Lịch cả ngày |
| POST | /api/v2/recommendations/duration | Theo thời lượng |
| POST | /api/v2/recommendations/weather | Theo thời tiết |

### User Preferences (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | /api/v2/users/interactions | Ghi tương tác |
| GET | /api/v2/users/{id}/preferences | Xem sở thích |
| POST | /api/v2/users/personalized-recommendations | Đề xuất cá nhân |
| GET | /api/v2/users/{id}/similar-users | Người dùng tương tự |
| GET | /api/v2/users/{id}/stats | Thống kê |

### Export/Import (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | /api/v2/export/songs | Xuất bài hát |
| POST | /api/v2/import/songs | Nhập bài hát |
| POST | /api/v2/backup/create | Tạo backup |
| GET | /api/v2/backup/list | Danh sách backup |
| GET | /api/v2/export/list | Danh sách exports |

### Database & Cache (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | /api/v2/db/stats | Thống kê DB pool |
| POST | /api/v2/db/optimize | Tối ưu DB |
| GET | /api/v2/cache/stats | Thống kê cache |
| POST | /api/v2/cache/clear | Xóa cache |

### Batch Operations (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | /api/v2/batch/predict | Dự đoán mood hàng loạt |
| POST | /api/v2/batch/search | Tìm kiếm hàng loạt |

### Health (v2)
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | /api/v2/extended/health | Health check mở rộng |
| GET | /api/v2/extended/endpoints | Danh sách endpoints |

---

## 🚀 Cách chạy

```bash
cd d:\MMB_FRONTBACK
python -m uvicorn backend.main:app --reload --port 8000
```

Truy cập:
- API Docs: http://127.0.0.1:8000/api/docs
- ReDoc: http://127.0.0.1:8000/api/redoc

---

## 📊 Ví dụ sử dụng

### 1. Đề xuất nhạc cho tập thể dục
```bash
curl -X POST http://127.0.0.1:8000/api/v2/recommendations/activity \
  -H "Content-Type: application/json" \
  -d '{"activity": "exercising", "limit": 10}'
```

### 2. Tạo playlist theo mood
```bash
curl -X POST http://127.0.0.1:8000/api/v2/playlists/auto/mood/happy?song_count=15
```

### 3. Backup database
```bash
curl -X POST http://127.0.0.1:8000/api/v2/backup/create
```

### 4. Ghi nhận tương tác người dùng
```bash
curl -X POST http://127.0.0.1:8000/api/v2/users/interactions \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "song_id": 5, "event_type": "like"}'
```

---

## 📈 Thống kê phiên bản

- **Tổng số endpoints:** 50+
- **Services mới:** 8
- **Lines of code mới:** ~4000
- **Version:** 2.1.0

---

## 🔮 Tính năng tương lai

- [ ] Real-time WebSocket notifications
- [ ] Machine learning mood prediction
- [ ] Social features (share, follow)
- [ ] Music file upload & analysis
- [ ] Spotify/YouTube integration
