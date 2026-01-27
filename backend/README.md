# Backend - Công Cụ Phân Loại Tâm Trạng Nhạc

## Tổng Quan

Backend là hệ thống dự đoán và phân tích tâm trạng bài hát sử dụng học máy. Nó đọc metadata từ SQLite, áp dụng mô hình Valence-Arousal để phân loại bài hát vào 5 loại tâm trạng khác nhau với 3 mức độ cường độ.

## Cấu Trúc Code

backend gồm các mô-đun chính:

- main.py: Điểm vào ứng dụng
- requirements.txt: Danh sách thư viện
- src/api/: Các endpoint REST API (13 routes)
- src/database/: Quản lý cơ sở dữ liệu SQLite
- src/pipelines/: Các mô hình học máy (Valence-Arousal)
- src/repo/: Tầng truy cập dữ liệu (Repository pattern)
- src/services/: Xử lý nghiệp vụ chính
- src/search/: Tìm kiếm TF-IDF (200 lines)
- src/ranking/: Dự đoán sở thích Logistic Regression (300 lines)

## Các Thành Phần Chính

**Tầng Services (Xử lý nghiệp vụ)**

- constants.py: Định nghĩa kiểu dữ liệu và hằng số
- helpers.py: Các hàm tiện ích để chuẩn hóa dữ liệu
- mood_services.py: Lớp DBMoodEngine dùng để dự đoán tâm trạng với cache
- history_service.py: Theo dõi lịch sử tâm trạng bài hát
- ranking_service.py: Xếp hạng bài hát theo tâm trạng

**Tầng Pipelines (Các mô hình ML)**

- mood_engine.py: Mô hình chính sử dụng Valence-Arousal + xác suất Gaussian
- EngineConfig: Các tham số cấu hình mô hình
- Prototype2D: Đại diện toán học của từng tâm trạng

**Tầng Repository (Truy cập dữ liệu)**

- song_repo.py: Các thao tác cơ sở dữ liệu
- history_repo.py: Theo dõi lịch sử bài hát

**Tầng Database**

- Tự động tạo và quản lý schema SQLite
- Hỗ trợ cột debug để giải thích mô hình

## Tính Năng

**Dự đoán tâm trạng:** Phân loại bài hát vào 5 loại tâm trạng

- Sôi động: Năng lượng cao, kích thích cao
- Vui vẻ: Năng lượng cao, kích thích thấp
- Buồn: Năng lượng thấp, kích thích thấp
- Lo lắng: Năng lượng thấp, kích thích cao
- Tức giận: Dựa vào công suất âm thanh và tốc độ

**Mức độ cường độ:** Chia làm 3 mức từ 1 đến 3

**Phương pháp xác suất:** Sử dụng Gaussian prototypes cho mỗi tâm trạng

**Thích ứng thể loại:** Hỗ trợ các prototype riêng cho từng thể loại nhạc

**Tự động huấn luyện lại:** Khi số lượng bài hát thay đổi

**Tìm kiếm TF-IDF:** Tìm bài hát theo từ khóa với xếp hạng relevance

**Gợi ý cá nhân hóa:** Dự đoán sở thích người dùng dựa trên feedback

## Bắt Đầu Nhanh

Cài đặt thư viện:

```bash
pip install -r requirements.txt
```

Khởi tạo cơ sở dữ liệu:

```bash
python -m backend.src.database.init_db
python -m backend.src.database.seed_data
```

Dự đoán tâm trạng cho bài hát chưa có:

```python
from backend.src.services.mood_services import DBMoodEngine
engine = DBMoodEngine("music.db", add_debug_cols=True)
engine.update_missing()
```

Cập nhật một bài hát:

```python
engine.update_one(song_id=12)
```

Tính toán lại tất cả bài hát:

```python
engine.update_all()
```

Chạy REST API:

```bash
python -m uvicorn backend.main:app --reload
```

Truy cập Swagger UI tại: http://127.0.0.1:8000/api/docs

## Cấu Hình

Chỉnh sửa EngineConfig trong mood_engine.py để điều chỉnh:

- Trọng số các đặc điểm âm thanh
- Ngưỡng mức độ cường độ
- Tham số huấn luyện
- Cấu hình thích ứng thể loại

## Kiểm Tra

Sử dụng CLI:

```bash
python main.py --db music.db update-missing --debug-cols
python main.py --db music.db update-all
python main.py --db music.db update-one --id 42
```

Hoặc test qua API:

```bash
curl http://127.0.0.1:8000/api/moods/predict?energy=0.8&valence=0.6
curl http://127.0.0.1:8000/api/moods/search?query=happy
curl -X POST http://127.0.0.1:8000/api/moods/user/user1/preference?song_id=1&preference=1
```

## Nguyên Tắc Thiết Kế

- Mỗi mô-đun có một trách nhiệm duy nhất
- Tránh lặp lại code, dùng helper functions
- Type hints đầy đủ
- Pure functions để dễ kiểm tra
- Config classes để dễ tùy chỉnh
