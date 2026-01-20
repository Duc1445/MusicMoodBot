# Mô-đun Services

Lớp xử lý nghiệp vụ chính và điều phối công cụ phân loại tâm trạng.

## Các File

**constants.py**

- Song: Kiểu dữ liệu bài hát
- MOODS: Danh sách 5 loại tâm trạng
- TABLE_SONGS: Tên bảng trong cơ sở dữ liệu

**helpers.py**

Các hàm tiện ích để xử lý dữ liệu:

- \_is_missing(): Kiểm tra giá trị bị thiếu
- \_to_float(): Chuyển đổi an toàn thành số thực
- clamp(): Giới hạn giá trị trong khoảng
- percentile(): Tính phần trăm
- robust_minmax(): Chuẩn hóa 0-100
- coerce_0_100(): Chuyển đổi giữa các tỷ lệ
- normalize_loudness_to_0_100(): Xử lý công suất âm thanh
- softmax(): Tính xác suất
- tokenize_genre(): Phân tích chuỗi thể loại

**mood_services.py**

Lớp DBMoodEngine chính:

- fit(): Huấn luyện mô hình
- predict_one(): Dự đoán tâm trạng một bài hát
- update_one(): Cập nhật cơ sở dữ liệu
- update_missing(): Cập nhật bài hát chưa có tâm trạng
- update_all(): Tính toán lại tất cả
- Tự động huấn luyện lại khi số bài hát thay đổi

**history_service.py**

- Lưu trữ lịch sử dự đoán tâm trạng
- Phân tích xu hướng

**ranking_service.py**

- Sắp xếp bài hát theo tâm trạng
- Lọc theo mức độ cường độ
- Các thuật toán xếp hạng tùy chỉnh

## Ví Dụ Sử Dụng

```python
from backend.src.services.mood_services import DBMoodEngine

engine = DBMoodEngine(
    db_path="music.db",
    add_debug_cols=True,
    auto_fit=True,
    refit_on_change=True
)

# Huấn luyện mô hình
engine.fit(force=True)

# Cập nhật bài hát chưa có tâm trạng
count = engine.update_missing()
print(f"Cập nhật {count} bài")

# Tính toán lại tất cả
count = engine.update_all()
print(f"Tính toán {count} bài hát")

# Dự đoán tâm trạng
song_dict = {"energy": 80, "valence": 70, "tempo": 120, ...}
result = engine.predict_one(song_dict)
print(f"Tâm trạng: {result['mood']}, Cường độ: {result['intensity']}")
```

## Cấu Hình

Tùy chỉnh hành vi mô hình qua EngineConfig:

- Giới hạn chuẩn hóa tốc độ
- Trọng số các đặc điểm âm thanh
- Ngưỡng mức độ cường độ
- Cấu hình thích ứng thể loại
