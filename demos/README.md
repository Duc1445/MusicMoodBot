# 🎬 Demos - Các Ứng Dụng Demo

Thư mục chứa các ứng dụng demo và kiểm tra tương tác.

## 📋 Danh Sách Demos

### `demo_api.py`
Kiểm tra và khám phá các API endpoints.

```bash
python demos/demo_api.py
```

**Chức năng:**
- Kiểm tra tất cả API dự đoán tâm trạng
- Giới thiệu tìm kiếm
- Hiển thị tạo gợi ý
- Kiểm tra phát hiện tâm trạng từ text

### `demo_server.py`
Server demo độc lập.

```bash
python demos/demo_server.py
```

**Chức năng:**
- Khởi động server FastAPI độc lập
- Cung cấp interface REST API
- Swagger docs tại http://localhost:8000/api/docs

### `demo_with_ui.py` ⭐ **CHỦ YẾU**
Demo tương tác với trực quan hóa cơ sở dữ liệu.

```bash
python demos/demo_with_ui.py
```

**Tính năng:**
- Tải tất cả bài hát từ music.db
- Hiển thị phân bố tâm trạng (😊 Vui, 😢 Buồn, ⚡ Năng lượng, 🧠 Suy tư)
- Thống kê:
  - Tổng bài: 30
  - Độ tự tin trung bình: 67.3%
  - Điểm valence & arousal
- Nhóm theo tâm trạng đẹp mắt
- Hướng dẫn bước tiếp theo

**Ví dụ Output:**
```
⚡ NĂNG LƯỢNG - 7 bài
  1. Khế Ước - The Flob (Rock)
     Valence: 81.0 | Arousal: 69.8 | Confidence: 85.2%
     🔥 Mạnh (Cường độ cao)

😊 VUI - 6 bài
  ...
```

---

Xem [STRUCTURE.md](../STRUCTURE.md) để biết thêm.
