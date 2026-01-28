# 📂 Scripts - Các Scripts Chạy Nhanh

Thư mục chứa các script launcher để khởi động dịch vụ.

## 📋 Danh Sách Scripts

### `run_backend.py`
Khởi động backend server đơn giản.

```bash
python scripts/run_backend.py
```

**Tính năng:**
- Khởi động FastAPI server tại http://localhost:8000
- Tự động tải database music.db
- API docs có sẵn tại http://localhost:8000/api/docs

### `launch_backend.py`
Khởi động backend với ghi log vào file.

```bash
python scripts/launch_backend.py
```

**Tính năng:**
- Giống run_backend.py
- Ghi log ra backend_log.txt
- Tốt hơn cho production/debugging

---

Xem [STRUCTURE.md](../STRUCTURE.md) để biết thêm.
