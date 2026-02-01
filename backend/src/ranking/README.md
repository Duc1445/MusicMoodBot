# Mô-đun Preference Model (Mô Hình Ưu Thích)

## Giới thiệu

Module `ranking` chứa các mô hình Machine Learning để dự đoán **sở thích âm nhạc của người dùng** dựa trên các đặc tính âm thanh của bài hát.

**Mục đích chính:**

- Học tập từ phản hồi của người dùng (thích/không thích)
- Dự đoán liệu người dùng có thích bài hát mới hay không
- Hỗ trợ gợi ý âm nhạc cá nhân hóa

---

## Cách hoạt động

### Thuật toán: Logistic Regression

Chúng tôi sử dụng **Logistic Regression** - một thuật toán học máy đơn giản nhưng hiệu quả:

```
Bài hát
   ↓
[Trích xuất 7 đặc tính âm thanh]
   ↓
[Chuẩn hóa dữ liệu]
   ↓
[Logistic Regression Model]
   ↓
Xác suất thích bài hát (0-1)
```

### 7 Đặc tính Âm thanh (Features)

Mô hình sử dụng 7 đặc tính để dự đoán sở thích:

| Đặc tính                         | Mô tả                           | Giá trị    | Ý nghĩa                         |
| -------------------------------- | ------------------------------- | ---------- | ------------------------------- |
| **energy** (năng lượng)          | Mức năng lượng của bài hát      | 0-100      | Cao = sôi động, Thấp = yên tĩnh |
| **happiness** (hạnh phúc)        | Mức độ vui vẻ                   | 0-100      | Cao = vui vẻ, Thấp = buồn       |
| **tempo**                        | Tốc độ nhạc                     | 50-200 BPM | Cao = nhanh, Thấp = chậm        |
| **loudness** (âm lượng)          | Độ lớn của bài hát              | -20 ~ 0 dB | Cao = lớn, Thấp = nhỏ           |
| **danceability** (khả năng nhảy) | Dễ nhảy hay không               | 0-100      | Cao = dễ nhảy, Thấp = khó nhảy  |
| **acousticness** (tính âm cổ)    | Mức độ sử dụng nhạc cụ acoustic | 0-100      | Cao = acoustic, Thấp = điện tử  |
| **intensity** (cường độ)         | Cường độ tổng thể               | 1-3        | 1=thấp, 2=trung bình, 3=cao     |

**Ví dụ:**

- Bài hát energetic, happy, fast tempo → Người yêu nhạc sôi động sẽ thích
- Bài hát acoustic, slow tempo, thấp intensity → Người yêu nhạc buồn sẽ thích

---

## Các Lớp Chính

### 1. Class `PreferenceModel`

Lớp chính để huấn luyện và dự đoán sở thích của người dùng.

#### Phương thức: `__init__()`

```python
model = PreferenceModel(random_state=42)
```

**Thông số:**

- `random_state`: Số ngẫu nhiên để tái tạo kết quả (mặc định = 42)

---

#### Phương thức: `fit(songs, preferences)`

Huấn luyện mô hình từ phản hồi của người dùng.

```python
songs = [
    {"energy": 80, "happiness": 75, "tempo": 130, "loudness": -5,
     "danceability": 85, "acousticness": 10, "intensity": 3},
    {"energy": 30, "happiness": 35, "tempo": 80, "loudness": -10,
     "danceability": 20, "acousticness": 70, "intensity": 1},
]

preferences = [1, 0]  # 1 = thích, 0 = không thích

model = PreferenceModel()
model.fit(songs, preferences)
```

**Quá trình bên trong:**

1. Trích xuất 7 đặc tính từ mỗi bài hát
2. Chuẩn hóa các đặc tính (StandardScaler)
3. Huấn luyện Logistic Regression model
4. Lưu trữ trọng số của mô hình

**Yêu cầu:**

- Số lượng bài hát = Số lượng phản hồi
- Phản hồi phải là 0 hoặc 1

---

#### Phương thức: `predict(song)`

Dự đoán liệu người dùng có thích bài hát hay không.

```python
new_song = {
    "energy": 85, "happiness": 80, "tempo": 135, "loudness": -4,
    "danceability": 88, "acousticness": 5, "intensity": 3
}

prediction = model.predict(new_song)
# Kết quả: 1 (thích) hoặc 0 (không thích)
```

**Kết quả:**

- `1` = Dự đoán người dùng sẽ **thích** bài hát
- `0` = Dự đoán người dùng sẽ **không thích** bài hát

---

#### Phương thức: `predict_proba(song)`

Dự đoán **xác suất** người dùng thích bài hát (chi tiết hơn).

```python
prob_dislike, prob_like = model.predict_proba(new_song)

print(f"Xác suất không thích: {prob_dislike:.2%}")  # e.g., 15%
print(f"Xác suất thích: {prob_like:.2%}")           # e.g., 85%
```

**Ứng dụng:**

- `prob_like >= 0.7` → Gợi ý bài hát này với độ tin cậy cao
- `0.4 < prob_like < 0.6` → Bài hát có thể hay không (không chắc)
- `prob_like < 0.3` → Không gợi ý bài hát này

---

#### Phương thức: `batch_predict(songs)`

Dự đoán cho nhiều bài hát cùng lúc.

```python
songs = [song1, song2, song3, ...]
predictions = model.batch_predict(songs)
# Kết quả: [1, 0, 1, ...] (danh sách các dự đoán)
```

---

#### Phương thức: `score(songs, preferences)`

Đánh giá hiệu suất của mô hình.

```python
test_songs = [...]
test_preferences = [...]

metrics = model.score(test_songs, test_preferences)

print(f"Accuracy: {metrics['accuracy']:.2%}")    # Độ chính xác
print(f"Precision: {metrics['precision']:.2%}")  # Độ chính xác của dự đoán 'thích'
print(f"Recall: {metrics['recall']:.2%}")        # Tỷ lệ bài thích được phát hiện
```

**Giải thích:**

- **Accuracy** (độ chính xác): Bao nhiêu % dự đoán đúng
- **Precision** (độ chính xác): Trong những bài dự đoán "thích", bao nhiêu % thực sự bị thích
- **Recall** (độ nhạy): Trong những bài thực sự thích, bao nhiêu % được phát hiện

---

### 2. Class `UserPreferenceTracker`

Theo dõi sở thích của người dùng theo thời gian và tự động huấn luyện lại mô hình.

#### Phương thức: `__init__(user_id)`

```python
tracker = UserPreferenceTracker(user_id="user_123")
```

**Thông số:**

- `user_id`: ID duy nhất của người dùng

---

#### Phương thức: `record_preference(song, preference)`

Ghi nhận phản hồi của người dùng về một bài hát.

```python
# Người dùng thích bài hát này
tracker.record_preference(song1, preference=1)

# Người dùng không thích bài hát này
tracker.record_preference(song2, preference=0)

# Người dùng thích bài hát này
tracker.record_preference(song3, preference=1)
```

**Lưu ý:**

- `preference` phải là `0` (không thích) hoặc `1` (thích)
- Dữ liệu được lưu trữ để huấn luyện lại mô hình sau

---

#### Phương thức: `retrain()`

Huấn luyện lại mô hình dựa trên tất cả phản hồi được ghi nhận.

```python
# Ghi nhận ít nhất 3 phản hồi
tracker.record_preference(song1, 1)
tracker.record_preference(song2, 0)
tracker.record_preference(song3, 1)

# Huấn luyện lại mô hình
tracker.retrain()
# → Mô hình cập nhật dựa trên phản hồi mới
```

**Yêu cầu:**

- Ít nhất 3 phản hồi để huấn luyện lại
- Nếu ít hơn 3, phương thức sẽ hiển thị cảnh báo

---

#### Phương thức: `predict_preference(song)`

Dự đoán xác suất người dùng thích bài hát.

```python
prob_like = tracker.predict_preference(new_song)

if prob_like > 0.7:
    print("Gợi ý bài hát này!")
elif prob_like < 0.3:
    print("Không gợi ý bài hát này")
else:
    print("Bài hát trung bình")
```

**Kết quả:**

- Nếu mô hình chưa huấn luyện: trả về `0.5` (trung lập)
- Nếu mô hình đã huấn luyện: trả về xác suất thích (0-1)

---

#### Phương thức: `get_stats()`

Lấy thống kê phản hồi của người dùng.

```python
stats = tracker.get_stats()

print(f"Tổng phản hồi: {stats['total']}")           # 10
print(f"Bài thích: {stats['likes']}")               # 6
print(f"Bài không thích: {stats['dislikes']}")      # 4
print(f"Tỷ lệ thích: {stats['like_ratio']:.1%}")   # 60%
```

---

## Ví dụ Sử dụng Hoàn Chỉnh

### Ví dụ 1: Huấn luyện và Dự đoán Cơ Bản

```python
from backend.src.ranking.preference_model import PreferenceModel

# Dữ liệu huấn luyện (từ feedback của người dùng)
songs = [
    {"energy": 90, "happiness": 85, "tempo": 140, "loudness": -3,
     "danceability": 90, "acousticness": 5, "intensity": 3},     # Bài EDM sôi động

    {"energy": 20, "happiness": 25, "tempo": 60, "loudness": -15,
     "danceability": 10, "acousticness": 95, "intensity": 1},    # Bài guitar buồn

    {"energy": 75, "happiness": 70, "tempo": 120, "loudness": -5,
     "danceability": 80, "acousticness": 20, "intensity": 2},    # Bài pop vui vẻ
]

preferences = [1, 0, 1]  # Thích, Không thích, Thích

# Huấn luyện
model = PreferenceModel()
model.fit(songs, preferences)
print("✓ Mô hình đã huấn luyện thành công!")

# Dự đoán bài hát mới
new_song = {
    "energy": 88, "happiness": 82, "tempo": 135, "loudness": -4,
    "danceability": 88, "acousticness": 8, "intensity": 3
}

prediction = model.predict(new_song)
prob_dislike, prob_like = model.predict_proba(new_song)

print(f"Dự đoán: {'Thích ❤️' if prediction == 1 else 'Không thích 💔'}")
print(f"Xác suất thích: {prob_like:.1%}")
```

---

### Ví dụ 2: Theo dõi Sở thích Người dùng

```python
from backend.src.ranking.preference_model import UserPreferenceTracker

# Tạo tracker cho một người dùng
tracker = UserPreferenceTracker(user_id="user_123")

# Người dùng nghe và phản hồi
songs_data = [
    {"energy": 90, "happiness": 85, ...},  # Bài 1
    {"energy": 20, "happiness": 25, ...},  # Bài 2
    {"energy": 75, "happiness": 70, ...},  # Bài 3
    {"energy": 85, "happiness": 80, ...},  # Bài 4
    {"energy": 30, "happiness": 35, ...},  # Bài 5
]

# Ghi nhận phản hồi
tracker.record_preference(songs_data[0], preference=1)  # Thích
tracker.record_preference(songs_data[1], preference=0)  # Không thích
tracker.record_preference(songs_data[2], preference=1)  # Thích
tracker.record_preference(songs_data[3], preference=1)  # Thích
tracker.record_preference(songs_data[4], preference=0)  # Không thích

# Huấn luyện mô hình từ phản hồi
tracker.retrain()
print("✓ Mô hình đã huấn luyện từ phản hồi!")

# Xem thống kê
stats = tracker.get_stats()
print(f"Tổng phản hồi: {stats['total']}")
print(f"Tỷ lệ thích: {stats['like_ratio']:.1%}")

# Dự đoán bài hát mới
new_song = {"energy": 92, "happiness": 87, ...}
prob = tracker.predict_preference(new_song)

if prob > 0.7:
    print(f"🎵 Gợi ý bài hát này! ({prob:.0%} khả năng thích)")
else:
    print(f"⚠️  Bài hát có thể không phù hợp ({prob:.0%} khả năng thích)")
```

---

## Hợp Tích Hợp Với REST API

### Endpoint: POST `/user/feedback`

Ghi nhận phản hồi của người dùng:

```bash
curl -X POST "http://localhost:8000/user/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "song_id": "song_001",
    "preference": 1
  }'
```

### Endpoint: GET `/user/recommendation`

Lấy gợi ý cho người dùng:

```bash
curl "http://localhost:8000/user/recommendation?user_id=user_123&top_k=5"
```

---

## Kiểm Thử Mô Hình

### Chạy bài test:

```bash
cd d:\MMB
python backend/src/test/test_preference_model.py
```

### Kết quả test:

```
✓ test_initialization (Khởi tạo mô hình)
✓ test_recording_feedback (Ghi nhận phản hồi)
✓ test_training (Huấn luyện mô hình)
✓ test_prediction (Dự đoán)
✓ test_statistics (Thống kê)
✓ test_isolation (Cách ly dữ liệu)
✓ test_edge_cases (Trường hợp cạnh)
✓ test_performance (Hiệu suất)
✓ test_model_properties (Thuộc tính mô hình)
✓ test_integration (Tích hợp)
✓ test_batch_prediction (Dự đoán hàng loạt)

=============== 11 passed ✓ ===============
Performance: 8,850 predictions/second
```

---

## Hiệu Suất

| Thao tác                    | Thời gian | Thông lượng    |
| --------------------------- | --------- | -------------- |
| Dự đoán đơn lẻ              | 0.113 ms  | 8,850 bài/giây |
| Huấn luyện (10 mẫu)         | 3.19 ms   | -              |
| Dự đoán hàng loạt (100 bài) | 11.3 ms   | 8,850 bài/giây |
| Lấy thống kê                | < 0.1 ms  | -              |

---

## Lưu Ý Quan Trọng

1. **Dữ liệu đặc tính:** Nếu một đặc tính bị thiếu hoặc rỗng, mô hình sẽ sử dụng giá trị mặc định là `50`

2. **Số lượng mẫu:** Cần ít nhất 3 mẫu để huấn luyện lại mô hình

3. **Chuẩn hóa dữ liệu:** Mô hình tự động chuẩn hóa dữ liệu đầu vào bằng StandardScaler

4. **Dữ liệu không cân bằng:** Nếu có quá nhiều thích/không thích, mô hình sẽ tự động cân bằng

---

## Tham khảo Thêm

- [test_preference_model.py](../test/test_preference_model.py) - Các test case chi tiết
- [mood_engine.md](../pipelines/readme.md) - Thuật toán Mood Engine
- [database/README.md](../database/README.md) - Cấu trúc cơ sở dữ liệu
