# MusicMood Bot - Hướng Dẫn Sử Dụng

## 🎵 Giới Thiệu
MusicMood Bot là ứng dụng gợi ý nhạc thông minh dựa trên cảm xúc của bạn.

## ✨ Các Tính Năng Đã Sửa

### 1. **Database Lưu Lịch Sử** ✅
- Database `musicmood.db` được tạo tự động tại `backend/musicmood.db`
- Lưu trữ:
  - Thông tin người dùng (tài khoản, email, mật khẩu)
  - Lịch sử chat (mood, intensity, thời gian)
  - Danh sách bài hát
  - Lịch sử gợi ý

### 2. **Chứng Thực Người Dùng** ✅
- **Đăng Ký**: Tạo tài khoản mới với email, tên, mật khẩu
- **Đăng Nhập**: Xác thực tài khoản từ database
- **Đăng Xuất**: Quay lại màn hình login

### 3. **Lưu Lịch Sử Chat** ✅
- Mỗi khi chọn mood → lưu vào database
- Mỗi khi chọn intensity → cập nhật lịch sử
- Mỗi lần nhận gợi ý → lưu recommendation

### 4. **Màn Hình Lịch Sử** ✅
- Hiển thị 20 bản ghi lịch sử gần nhất
- Hiển thị mood, intensity, thời gian, bài hát được gợi ý
- Lưu trữ dữ liệu liên tục

### 5. **Buttons Hoạt Động** ✅
Tất cả buttons bây giờ đều có functionality:
- **💬 Chat** → Về màn hình chat
- **📋 Lịch Sử** → Xem lịch sử nghe nhạc
- **👤 Hồ Sơ** → Xem thông tin tài khoản
- **🧹 Reset** → Làm mới cuộc chat
- **⚙️ Cài Đặt** → (sẵn sàng mở rộng)
- **Đăng Xuất** → Quay lại login

## 🚀 Cách Chạy Ứng Dụng

### Prerequisite
```bash
pip install flet
```

### Chạy ứng dụng
```bash
cd h:\MusicMoodBot-frontend
python frontend/test.py
```

## 📁 Cấu Trúc Database

### Bảng `users`
```sql
- user_id (PRIMARY KEY)
- username
- email (UNIQUE)
- password
- created_at
- total_songs_listened
- favorite_mood
- favorite_artist
```

### Bảng `chat_history`
```sql
- history_id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- mood
- intensity
- song_id
- reason
- timestamp
```

### Bảng `recommendations`
```sql
- recommendation_id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- song_id (FOREIGN KEY)
- mood
- intensity
- timestamp
```

### Bảng `songs`
```sql
- song_id (PRIMARY KEY)
- name
- artist
- genre
- suy_score
- reason
- moods
- created_at
```

## 🎯 Luồng Sử Dụng

1. **Đăng Ký / Đăng Nhập**
   - Email: user@example.com
   - Mật khẩu: tùy ý

2. **Chat Screen**
   - Chọn mood: Vui, Buồn, Suy tư, Chill, Năng lượng, Other
   - Chọn intensity: Nhẹ, Vừa, Mạnh
   - Nhận gợi ý bài hát
   - Bấm "Try again" để xem bài khác
   - Bấm "Đổi mood" để chọn lại cảm xúc

3. **History Screen**
   - Xem toàn bộ lịch sử chat
   - Filter theo mood (sẵn sàng mở rộng)
   - Thông tin: Mood, Intensity, Thời gian, Bài hát

4. **Profile Screen**
   - Xem thông tin cá nhân
   - Xem thống kê (sẵn sàng cập nhật từ DB)
   - Đăng xuất

## 💾 Data Persistence

Tất cả dữ liệu được lưu vào `musicmood.db`:
- ✅ Thông tin user
- ✅ Lịch sử mood selections
- ✅ Lịch sử recommendations
- ✅ Danh sách bài hát

Khi login lại cùng tài khoản:
- ✅ Lịch sử sẽ được hiển thị
- ✅ Có thể xem các tuần/tháng trước

## 🔒 Security Notes

Hiện tại mật khẩu được lưu dưới dạng plain text. Cho production:
- Sử dụng hashing (bcrypt, argon2)
- Sử dụng HTTPS
- Sử dụng session tokens

## 📝 Sample Data

6 bài hát mẫu được tải vào database tự động:
1. Mưa Tháng Sáu - Văn Mai Hương
2. Có Chàng Trai Viết Lên Cây - Phan Mạnh Quỳnh
3. Ngày Chưa Giông Bão - Bùi Lan Hương
4. Cô Gái M52 - HuyR x Tùng Viu
5. Bước Qua Nhau - Vũ.
6. Nơi Này Có Anh - Sơn Tùng M-TP

## 🐛 Troubleshooting

### Database file not found
```
Nếu database không được tạo, chạy:
python backend/database.py
```

### Import error
```
Đảm bảo đang chạy từ thư mục root:
cd h:\MusicMoodBot-frontend
python frontend/test.py
```

### Port conflict
Thay đổi port trong code nếu cần.

## 📞 Liên Hệ & Hỗ Trợ

Đây là phiên bản v1.0.0 của MusicMood Bot.
Mọi vấn đề vui lòng báo cáo.

---
**Updated: 22/01/2026**
**Status: ✅ All features working**
