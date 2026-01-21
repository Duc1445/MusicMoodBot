# Mô-đun Repository

Tầng truy cập dữ liệu sử dụng pattern Repository.

## Các File

**song_repo.py**

Các thao tác cơ sở dữ liệu cho bài hát:

- connect(db_path): Mở kết nối SQLite
- get_table_columns(con, table): Lấy danh sách cột
- ensure_columns(con, table, column_defs): Thêm cột nếu chưa có, an toàn chạy nhiều lần
- fetch_songs(con, where, params): Lấy danh sách bài hát, hỗ trợ WHERE clause
- fetch_song_by_id(con, song_id): Lấy một bài theo ID
- update_song(con, song_id, updates): Cập nhật bài hát

**history_repo.py**

Repository cho lịch sử tâm trạng bài hát.

## Cách Sử Dụng

Nhập các hàm:

```python
from backend.src.repo.song_repo import (
    connect, fetch_songs, fetch_song_by_id, update_song, ensure_columns
)
```

Mở kết nối:

```python
con = connect("music.db")
```

Thêm cột debug nếu chưa có:

```python
ensure_columns(con, "songs", [
    "valence_score REAL",
    "arousal_score REAL",
    "mood_confidence REAL"
])
```

Lấy tất cả bài hát:

```python
all_songs = fetch_songs(con)
```

Lấy bài hát buồn hoặc lo lắng:

```python
unhappy_songs = fetch_songs(
    con,
    "mood IN (?, ?)",
    ("sad", "stress")
)
```

Lấy một bài hát theo ID:

```python
song = fetch_song_by_id(con, song_id=42)
if song:
    print(f"Bài hát: {song['title']}")
```

Cập nhật bài hát:

```python
update_song(con, song_id=42, updates={
    "mood": "energetic",
    "intensity": 3,
    "mood_score": 85.5,
    "valence_score": 75.0,
    "arousal_score": 80.0,
    "mood_confidence": 0.92
})
```

Lưu lại:

```python
con.commit()
con.close()
```
