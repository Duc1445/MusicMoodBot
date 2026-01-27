# 🎵 Music Mood Prediction - DEMO GUIDE

## ⚡ Cách chạy demo nhanh nhất

### **Bước 1: Cài đặt Dependencies (Lần đầu)**
```powershell
cd d:\MMB_FRONTBACK
pip install -r requirements.txt
```

### **Bước 2: Khởi tạo Database (Lần đầu)**
```powershell
cd d:\MMB_FRONTBACK\backend
python -m backend.database
```

### **Bước 3: Chạy Backend Server**
**Cách 1 - Nhanh nhất (Dùng batch file):**
```powershell
d:\MMB_FRONTBACK\start_backend.bat
```

**Cách 2 - Manual:**
```powershell
cd d:\MMB_FRONTBACK\backend
python -m uvicorn backend.main:app --reload --port 8000
```

✅ **Backend chạy lúc:** http://localhost:8000

📚 **Xem API Documentation:** http://localhost:8000/api/docs

### **Bước 4: Mở Terminal Mới, Chạy Frontend**
**Cách 1 - Nhanh nhất (Dùng batch file):**
```powershell
d:\MMB_FRONTBACK\start_frontend.bat
```

**Cách 2 - Manual:**
```powershell
cd d:\MMB_FRONTBACK\frontend
python main.py
```

✅ **Frontend sẽ mở cửa sổ Flet UI**

---

## 📱 Các tính năng demo

### **1. Login/Signup Screen**
- Đăng nhập hoặc tạo tài khoản mới
- Lưu trữ thông tin người dùng

### **2. Chat Screen** (Main Feature)
- Chat với AI để yêu cầu gợi ý nhạc
- Nhạc được dự đoán dựa trên mood
- Hiển thị danh sách nhạc được đề xuất

### **3. History Screen**
- Xem lịch sử tất cả nhạc đã nghe
- Xóa lịch sử

### **4. Profile Screen**
- Xem thông tin profile
- Cập nhật thông tin người dùng
- Đăng xuất

---

## 🔧 Kiểm tra API bằng Postman/Browser

### **API Endpoints Available:**

1. **Get All Songs**
```
GET http://localhost:8000/api/songs
```

2. **Predict Mood**
```
POST http://localhost:8000/api/predict_mood
Body: {"text": "I'm feeling happy"}
```

3. **Get Recommendations**
```
GET http://localhost:8000/api/recommendations?mood=happy&limit=10
```

4. **Get Song by ID**
```
GET http://localhost:8000/api/songs/{song_id}
```

### **Interactive API Docs:**
Mở trình duyệt: http://localhost:8000/api/docs

---

## 🐛 Troubleshooting

**Lỗi: "Module not found"**
```powershell
pip install -r requirements.txt --force-reinstall
```

**Lỗi: "Port 8000 already in use"**
```powershell
python -m uvicorn backend.main:app --port 8001
```

**Lỗi: Database không tạo được**
```powershell
cd backend
python -m backend.database
```

**Lỗi: Frontend không chạy được**
- Kiểm tra Flet đã cài: `pip install flet`
- Thử chạy: `python -m flet --version`

---

## 📊 Project Structure

```
d:\MMB_FRONTBACK\
├── backend/
│   ├── main.py (FastAPI server)
│   ├── database.py
│   ├── src/
│   │   ├── api/ (API routes)
│   │   ├── services/ (Business logic)
│   │   └── database/ (DB operations)
│   └── requirements.txt
│
├── frontend/
│   ├── main.py (Flet UI entry)
│   ├── src/
│   │   ├── screens/ (UI screens)
│   │   ├── services/ (API calls)
│   │   └── config/ (Settings)
│   └── requirements.txt
│
├── start_backend.bat (✨ Dễ sử dụng)
├── start_frontend.bat (✨ Dễ sử dụng)
├── requirements.txt
└── README.md
```

---

## 💡 Tips

1. **Chạy cả 2 servers cùng lúc:**
   - Terminal 1: `start_backend.bat`
   - Terminal 2: `start_frontend.bat`

2. **Xem logs chi tiết:**
   - Backend logs: Terminal đang chạy backend
   - Frontend logs: Xem console của Flet UI

3. **Reset Database:**
   ```powershell
   Remove-Item d:\MMB_FRONTBACK\backend\music_mood.db
   python -m backend.database
   ```

4. **Kiểm tra kết nối:**
   - Backend live: http://localhost:8000
   - API docs: http://localhost:8000/api/docs
   - Health check: http://localhost:8000/health

---

## 🎯 Next Steps

- Tùy chỉnh models trong `backend/src/ranking/`
- Thêm songs vào `backend/src/database/seed_data.py`
- Tùy chỉnh UI trong `frontend/src/screens/`
- Thêm features mới vào API

---

**Chúc bạn chạy demo vui vẻ! 🚀**
