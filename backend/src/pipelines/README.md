# Mô-đun Pipelines

Các mô hình học máy để dự đoán tâm trạng.

## Các File

**mood_engine.py**

Mô hình chính sử dụng Valence-Arousal + xác suất Gaussian.

### Các Lớp Chính:

**EngineConfig:** Cấu hình tham số mô hình

- Giới hạn chuẩn hóa tốc độ
- Trọng số các đặc điểm cho tính kích thích
- Trọng số các đặc điểm cho tính vui vẻ
- Tham số huấn luyện prototype
- Ngưỡng mức độ cường độ
- Cấu hình thích ứng thể loại

**Prototype2D:** Đại diện Gaussian của tâm trạng

- Lưu giá trị trung bình và độ lệch chuẩn
- Tính log-likelihood cho phân loại

**MoodEngine:** Lớp mô hình chính

- fit(songs): Huấn luyện mô hình
- predict(song): Dự đoán tâm trạng
- mood_probabilities(song, v, a): Xác suất cho mỗi tâm trạng
- infer_intensity_int(arousal): Chuyển kích thích thành mức độ 1-3
- valence_score(song): Tính vui vẻ
- arousal_score(song): Tính kích thích

### Logic Mô Hình:

**Tính Vui Vẻ:**

Kết hợp: mức vui vẻ (85%) + khả năng nhảy (15%)

**Tính Kích Thích:**

Kết hợp:

- Năng lượng 45%
- Tốc độ chuẩn hóa 20%
- Công suất âm thanh chuẩn hóa 20%
- Khả năng nhảy 10%
- Trừ acoustic 5%

**Phân Loại Tâm Trạng:**

1. Tạo nhãn yếu từ vui vẻ và kích thích
   - Sôi động: Vui vẻ cao, Kích thích cao
   - Vui vẻ: Vui vẻ cao, Kích thích thấp
   - Buồn: Vui vẻ thấp, Kích thích thấp
   - Lo lắng: Vui vẻ thấp, Kích thích cao
   - Tức giận: Vui vẻ thấp, Kích thích cao + công suất cao

2. Huấn luyện Gaussian prototype cho mỗi tâm trạng

3. Dùng xác suất để phân loại bài hát mới

4. Hỗ trợ prototype riêng cho từng thể loại

## Cách Sử Dụng

Tạo mô hình với cấu hình mặc định:

```python
from backend.src.pipelines.mood_engine import MoodEngine, EngineConfig
engine = MoodEngine()
```

Hoặc cấu hình tùy chỉnh:

```python
cfg = EngineConfig(
    w_energy=0.5,
    use_genre_tokens=True
)
engine = MoodEngine(cfg=cfg)
```

Huấn luyện mô hình:

```python
engine.fit(songs)
```

Dự đoán tâm trạng:

```python
song = {"energy": 80, "valence": 70, "tempo": 120, ...}
result = engine.predict(song)
print(result)
```

Kết quả trả về:

- mood: sôi động
- intensity: 3
- mood_score: 75.0
- valence_score: 70.0
- arousal_score: 80.0
- mood_confidence: 0.87
