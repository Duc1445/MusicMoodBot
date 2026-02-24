# 🔧 Tools - Các Công Cụ Tiện Ích

Các script tiện ích để bảo trì và cấu hình.

## 📋 Danh Sách Tools

### `calculate_music_attributes.py` ⭐ **QUAN TRỌNG**
Tự động tính toán thuộc tính dự đoán tâm trạng bị thiếu trong cơ sở dữ liệu.

```bash
python tools/calculate_music_attributes.py
```

**Chức năng:**
- Tải tất cả bài hát từ music.db
- Huấn luyện mood engine trên bộ dữ liệu
- Tính toán cho mỗi bài:
  - `mood` - Phân loại tâm trạng (vui, buồn, suy tư, năng lượng)
  - `intensity` - Mức cường độ (1=Nhẹ, 2=Vừa, 3=Mạnh)
  - `valence_score` - Tích cực nhạc (0-100)
  - `arousal_score` - Năng lượng nhạc (0-100)
  - `mood_score` - Điểm tâm trạng tổng hợp
  - `mood_confidence` - Phần trăm tự tin
- Cập nhật tất cả bản ghi trong cơ sở dữ liệu
- Hiển thị tiến trình và tóm tắt

**Yêu cầu đầu vào:**
- `music.db` phải có bài hát với các đặc trưng âm thanh:
  - energy, happiness, danceability
  - acousticness, tempo, loudness
  - Các tính năng tùy chọn khác

**Output:**
```
[1/30] Lạc Trôi - Sơn Tùng MTP
  Valence: 24.05 | Arousal: 72.82
  Mood: suy tư | Intensity: Mạnh
  Confidence: 67.04%

Cập nhật thành công 30 bài!
✓ 30/30 bài giờ đã có đầy đủ thuộc tính
```

### `check_db.py`
Kiểm tra và xác thực cấu trúc cơ sở dữ liệu.

```bash
python tools/check_db.py
```

**Chức năng:**
- Liệt kê tất cả bảng trong cơ sở dữ liệu
- Hiển thị định nghĩa cột cho bảng bài hát
- Đếm tổng số bài
- Hiển thị bản ghi bài mẫu
- Hiển thị tên cột và loại

**Ví dụ Output:**
```
Bảng: [('songs',), ('sqlite_sequence',), ('recommendation_history',)]

Cột Bài hát:
  song_id (INTEGER) KHÓA CHÍNH
  song_name (TEXT)
  artist (TEXT)
  genre (TEXT)
  mood (TEXT)
  ... và nhiều hơn nữa

Tổng bài: 30
Mẫu: (1, 'Lạc Trôi', 'Sơn Tùng MTP', 'Pop', 'stress', 3, ...)
```

---

Xem [STRUCTURE.md](../STRUCTURE.md) để biết thêm.
