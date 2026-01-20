# Mô-đun Database

Quản lý khởi tạo SQLite, schema, và dữ liệu mẫu.

## Các File

**init_db.py**

- Tạo cơ sở dữ liệu SQLite và bảng songs
- Bảng songs chứa:
  - song_id: Mã số bài hát (khóa chính)
  - Thông tin: title, artist, genre
  - Đặc điểm âm thanh: energy, valence, tempo, loudness, danceability, acousticness
  - Tâm trạng: mood, intensity, mood_score
  - Debug (tuỳ chọn): valence_score, arousal_score, mood_confidence
- An toàn chạy nhiều lần

**seed_data.py**

- Nhập dữ liệu mẫu vào cơ sở dữ liệu
- Dùng cho kiểm tra và phát triển
- Có thể mở rộng với Spotify API, TuneBat API, etc.

**music.sqbpro**

- File cơ sở dữ liệu SQLite chứa tất cả metadata và dự đoán
- Tự động tạo bởi init_db.py

## Cách Sử Dụng

Tạo schema cơ sở dữ liệu:

```bash
python -m backend.src.database.init_db
```

Nhập dữ liệu mẫu:

```bash
python -m backend.src.database.seed_data
```

Xem dữ liệu:

```bash
sqlite3 music.sqbpro
sqlite> select * from songs limit 5;
```

## Schema Cơ Sở Dữ Liệu

Bảng songs chứa các cột:

- song_id: Khóa chính
- title, artist, genre: Thông tin bài hát
- energy: Năng lượng 0-100
- valence: Mức vui vẻ 0-100
- tempo: Tốc độ BPM
- loudness: Công suất âm thanh dBFS
- danceability: Khả năng nhảy 0-100
- acousticness: Mức acoustic 0-100
- mood: Tâm trạng dự đoán
- intensity: Mức độ cường độ 1-3
- mood_score: Điểm tâm trạng 0-100 dùng để sắp xếp
- valence_score, arousal_score, mood_confidence: Debug columns

## Nguồn Dữ Liệu

Có thể lấy từ:

- Spotify API: đặc điểm âm thanh
- TuneBat API: đặc điểm nhạc và phân loại tâm trạng
- Last.fm API: thể loại và metadata
- Import CSV: dữ liệu riêng
