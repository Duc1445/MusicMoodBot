# Hướng Dẫn Giải Thích 3 Phần Chính - MMB Music Platform

Tài liệu này giúp bạn hiểu và giải thích 3 phần chính cho thầy cô.

---

## 1️⃣ MOOD PREDICTION ENGINE (Công Cụ Dự Đoán Tâm Trạng)

### Vị Trí: `backend/src/pipelines/mood_engine.py`

### Mục Đích Chính:

Dự đoán tâm trạng của người nghe dựa trên các đặc điểm âm thanh của bài hát.

### Cách Hoạt Động:

**Bước 1: Tính Vui Vẻ (Valence)**

- Công thức: `Vui Vẻ = 0.85 × mức vui vẻ + 0.15 × khả năng nhảy`
- Kết quả: Con số từ 0-100
- Ý nghĩa:
  - 0-30: Buồn bã
  - 30-70: Trung bình
  - 70-100: Vui vẻ cao

**Bước 2: Tính Kích Thích (Arousal)**

- Công thức kết hợp nhiều yếu tố:
  - Năng lượng (45%)
  - Tốc độ (20%)
  - Mức độ lớn tiếng (20%)
  - Khả năng nhảy (10%)
  - Trừ tính acoustic (5%)
- Kết quả: Con số từ 0-100
- Ý nghĩa:
  - 0-30: Yên tĩnh
  - 30-70: Trung bình
  - 70-100: Rất sôi động

**Bước 3: Phân Loại Tâm Trạng**

- Dùng Vui Vẻ + Kích Thích để phân loại thành 5 tâm trạng:

| Tâm Trạng   | Vui Vẻ      | Kích Thích    | Ví Dụ                |
| ----------- | ----------- | ------------- | -------------------- |
| 😄 Vui Vẻ   | Cao (70+)   | Thấp (0-40)   | Bài ballad nhẹ nhàng |
| 🎉 Sôi Động | Cao (70+)   | Cao (60+)     | Bài dance sôi động   |
| 😢 Buồn     | Thấp (0-30) | Thấp (0-40)   | Bài ballad buồn      |
| 😰 Lo Lắng  | Thấp (0-30) | Cao (60+)     | Bài rock gợn sóng    |
| 😠 Tức Giận | Thấp (0-30) | Rất Cao (70+) | Bài metal mạnh       |

**Bước 4: Tính Mức Độ Cường Độ (Intensity)**

- Dựa vào Kích Thích:
  - Mức 1: Yên tĩnh (0-33)
  - Mức 2: Trung bình (33-67)
  - Mức 3: Mạnh mẽ (67-100)

**Bước 5: Tính Độ Tin Cậy (Confidence)**

- Xác suất từ 0-100%
- Cao hơn = mô hình chắc chắn hơn

### Kết Quả Trả Về:

```python
{
    "valence_score": 71.4,        # Điểm vui vẻ
    "arousal_score": 87.8,        # Điểm kích thích
    "mood": "energetic",          # Tâm trạng
    "intensity": 3,               # Mức độ cường độ
    "mood_confidence": 0.95,      # Độ tin cậy 95%
    "mood_score": 79.6            # Trung bình cộng
}
```

### Hiệu Suất:

- ⚡ **70,747 dự đoán/giây** (rất nhanh)
- Xử lý 1 bài hát: 0.014 milliseconds
- Có thể chạy real-time trên điện thoại

---

## 2️⃣ DATABASE & DATA LOADING (Cơ Sở Dữ Liệu & Tải Dữ Liệu)

### Vị Trí: `backend/src/database/music.db`

### Mục Đích Chính:

Lưu trữ thông tin 30 bài hát Việt Nam cùng các đặc điểm âm thanh.

### Cấu Trúc Cơ Sở Dữ Liệu (21 cột):

**Cột Định Danh (5 cột):**

```
1. song_id          - Mã số bài (1-30)
2. song_name        - Tên bài hát
3. artist           - Tên ca sĩ
4. genre            - Thể loại
5. source           - Nguồn
```

**Cột Đặc Điểm Âm Thanh Cơ Bản (6 cột):**

```
6. energy           - Năng lượng (0-100)
7. happiness        - Tính vui vẻ (0-100)
8. danceability     - Khả năng nhảy (0-100)
9. acousticness     - Tính acoustic (0-100)
10. tempo           - Tốc độ (BPM)
11. loudness        - Mức lớn tiếng (dB)
```

**Cột Đặc Điểm Tùy Chọn (4 cột):**

```
12. speechiness      - Tính nói chuyện
13. instrumentalness - Tính nhạc không lời
14. liveness         - Tính trực tiếp
15. popularity       - Độ nổi tiếng
```

**Cột Được Tính Toán Tự Động (6 cột):**

```
16. valence_score    - Điểm vui vẻ (từ Mood Engine)
17. arousal_score    - Điểm kích thích (từ Mood Engine)
18. mood             - Tâm trạng (energetic, happy, sad, stress, angry)
19. intensity        - Mức độ (1-3)
20. mood_score       - Trung bình V+A
21. mood_confidence  - Độ tin cậy dự đoán
```

### Dữ Liệu Mẫu:

**Bài 1: Lạc Trôi - Sơn Tùng MTP**

```
- Energy: 87 (rất cao)
- Happiness: 17 (rất thấp)
- Danceability: 64 (cao)
- Mood: STRESS (tâm trạng lo lắng)
- Intensity: 3 (rất mạnh)
```

**Bài 2: Phép Màu - MAYDAYS**

```
- Energy: 95 (cực cao)
- Happiness: 72 (cao)
- Danceability: 68 (cao)
- Mood: ENERGETIC (tâm trạng sôi động)
- Intensity: 3 (rất mạnh)
```

### Hiệu Suất:

- 📊 **30 bài hát** trong database
- 📈 **Tải tất cả: 0.44ms** (dưới 1 mili-giây)
- 🔍 **Truy vấn 1 bài: 0.25ms**
- 💾 **Kích thước: 16 KB** (rất nhỏ)
- ✅ **Toàn vẹn dữ liệu: 100%**

### Cách Sử Dụng:

```python
from backend.src.repo.song_repo import connect, fetch_songs

# Kết nối
con = connect("d:\\MMB\\backend\\src\\database\\music.db")

# Lấy tất cả bài hát
songs = fetch_songs(con)
print(f"Tổng bài hát: {len(songs)}")  # 30

# Lấy 1 bài
song = next(s for s in songs if s['song_id'] == 5)
print(song['song_name'])  # "Không Phải Dạng Vừa Đâu"
```

---

## 3️⃣ PREFERENCE MODEL (Mô Hình Sở Thích)

### Vị Trí: `backend/src/ranking/preference_model.py`

### Mục Đích Chính:

Theo dõi phản hồi người dùng (thích/không thích) và dự đoán sở thích cho bài hát mới.

### Cách Hoạt Động:

**Bước 1: Ghi Lại Phản Hồi**

- Khi người dùng thích một bài: ghi lại `1`
- Khi người dùng không thích: ghi lại `0`
- Lưu vào lịch sử của người dùng

Ví dụ:

```python
tracker = UserPreferenceTracker("user_001")

# Người dùng thích bài 1, 3, 5
tracker.record_preference(song1, preference=1)
tracker.record_preference(song3, preference=1)
tracker.record_preference(song5, preference=1)

# Người dùng không thích bài 2, 4
tracker.record_preference(song2, preference=0)
tracker.record_preference(song4, preference=0)
```

**Bước 2: Trích Xuất Đặc Điểm (7 đặc điểm)**

```
1. Energy - Năng lượng
2. Happiness - Tính vui vẻ
3. Tempo - Tốc độ
4. Loudness - Mức lớn tiếng
5. Danceability - Khả năng nhảy
6. Acousticness - Tính acoustic
7. Intensity - Mức độ cường độ
```

**Bước 3: Chuẩn Hóa Dữ Liệu**

- Đưa tất cả 7 đặc điểm về cùng thang đo
- Sử dụng StandardScaler (giống như "tái cân bằng" các số)
- Để mô hình học tập hiệu quả hơn

**Bước 4: Huấn Luyện Mô Hình**

- Sử dụng Logistic Regression
- Học từ phản hồi được ghi lại
- Tìm ra quy luật: "Khi nào người dùng thích bài?"

Ví dụ:

```python
# Sau khi thêm phản hồi từ 5+ bài
tracker.retrain()  # Huấn luyện mô hình
```

**Bước 5: Dự Đoán Sở Thích**

- Cho bài hát mới, dự đoán người dùng có thích không
- Trả về xác suất (0-100%)

Ví dụ:

```python
new_song = {...}
prediction = tracker.model.predict(new_song)  # 0 hoặc 1

if prediction == 1:
    print("Người dùng sẽ thích bài này")
else:
    print("Người dùng có thể không thích bài này")
```

### Kết Quả Dự Đoán Thực Tế:

**Test Trên 5 Bài Hát Mới:**

```
1. "Buông Đôi Tay Nhau Ra" → THÍCH (69.6% tin cậy)
2. "Phép Màu - Đàn Cá Gỗ" → THÍCH (72.3% tin cậy)
3. "Hơn Bất Cứ Ai" → THÍCH (58.1% tin cậy)
4. "Thiệp Hồng Sai Tên" → THÍCH (96.2% tin cậy) ⭐
5. "Ngày Này Năm Ấy" → KHÔNG THÍCH (53.8% tin cậy)
```

### Hỗ Trợ Đa Người Dùng:

- Mỗi người dùng có tracker **độc lập**
- Phản hồi của user 1 **không ảnh hưởng** user 2
- Mô hình của user 1 **hoàn toàn khác** user 2

```python
user1 = UserPreferenceTracker("user_001")
user2 = UserPreferenceTracker("user_002")

# Các tracker này tách biệt hoàn toàn
```

### Hiệu Suất:

- ⚡ **8,850 dự đoán/giây**
- Dự đoán 1 bài: **0.113 milliseconds**
- Huấn luyện: **3.19ms** (có thể thực hiện real-time)
- Có thể chạy trên web server

---

## 📊 Tóm Tắt So Sánh

| Phần            | Mục Đích            | Đầu Vào               | Đầu Ra                 | Hiệu Suất   |
| --------------- | ------------------- | --------------------- | ---------------------- | ----------- |
| **Mood Engine** | Dự đoán tâm trạng   | Đặc điểm âm thanh (6) | Tâm trăng + độ tin cậy | 70K pred/s  |
| **Database**    | Lưu dữ liệu bài hát | -                     | 30 bài với đặc điểm    | 0.44ms tải  |
| **Preference**  | Dự đoán sở thích    | Phản hồi người dùng   | Thích/không thích      | 8.8K pred/s |

---

## 🔄 Luồng Dữ Liệu Hoàn Chỉnh

```
Database (30 bài hát)
        ↓
        └→ Mood Engine: Tính tâm trăng
        │  (Valence + Arousal)
        │
        └→ REST API: Cung cấp endpoints
        │  /moods, /predict, etc.
        │
        └→ Preference Model: Theo dõi phản hồi
           (User thích/không thích)
           │
           └→ Huấn luyện mô hình
           │
           └→ Dự đoán sở thích mới
```

---

## 💡 Những Điểm Chính Để Giải Thích Cho Thầy:

1. **Mood Engine:**
   - "Công cụ dự đoán tâm trạng bằng cách phân tích 6 đặc điểm âm thanh"
   - "Kết hợp 2 yếu tố: Vui Vẻ (75%) và Kích Thích (kiến thức từ âm thanh)"
   - "Phân loại thành 5 tâm trăng: vui, sôi động, buồn, lo lắng, tức giận"

2. **Database:**
   - "Lưu 30 bài hát Việt Nam với các đặc điểm âm thanh (21 cột)"
   - "Tối ưu hóa để truy vấn cực nhanh (0.25ms)"
   - "Dữ liệu được tính toán tự động từ Mood Engine"

3. **Preference Model:**
   - "Mô hình học máy để dự đoán sở thích người dùng"
   - "Dùng Logistic Regression để học từ phản hồi"
   - "Mỗi người dùng có mô hình riêng (không can thiệp lẫn nhau)"
   - "Huấn luyện nhanh (3ms), dự đoán cực nhanh (0.11ms)"

---

## 📚 Tệp Để Tham Khảo

- `backend/src/pipelines/readme.md` - Chi tiết Mood Engine
- `backend/src/database/README.md` - Chi tiết Database
- `backend/src/ranking/README.md` - Chi tiết Preference Model
