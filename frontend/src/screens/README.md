# 🎨 screens/ - UI Pages

Chứa **toàn bộ trang** của ứng dụng - login, chat, history, profile, v.v.

## 📄 Files

- **login_screen.py** - Trang đăng nhập
- **signup_screen.py** - Trang đăng ký
- **chat_screen.py** - Trang chính (chat với bot)
- **history_screen.py** - Trang xem lịch sử chat
- **profile_screen.py** - Trang hồ sơ người dùng

## 📱 Mỗi screen hiển thị gì?

### login_screen.py

- Form đăng nhập (email, mật khẩu)
- Nút đăng nhập
- Link đến trang đăng ký

### signup_screen.py

- Form đăng ký (tên, email, mật khẩu)
- Kiểm tra mật khẩu trùng khớp
- Link quay lại đăng nhập

### chat_screen.py (trang chính)

- Danh sách tin nhắn
- Nút chọn tâm trạng (Vui, Buồn, v.v.)
- Nút chọn cường độ (Nhẹ, Vừa, Mạnh)
- Gợi ý bài hát
- Nút thử lại
- Menu điều hướng

### history_screen.py

- Danh sách lịch sử chat
- Thống kê (tổng số, tâm trạng nhiều nhất)
- Nút quay lại chat

### profile_screen.py

- Thông tin người dùng (tên, email)
- Nút đăng xuất
- Nút quay lại chat

## 🎨 Khi nào edit?

- Thay đổi bố cục trang
- Thêm element UI mới
- Sửa lỗi giao diện
- Thay đổi điều hướng

## ⚠️ Lưu ý

- Mỗi screen là **một trang riêng biệt**
- Không đặt **logic** vào screen, dùng services
- Gọi services để xử lý data
- Sử dụng components để tái sử dụng UI
