# Functional Test Cases

> Tài liệu kiểm thử chức năng MusicMoodBot v1.0

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [TC-AUTH: Authentication](#2-tc-auth-authentication)
3. [TC-MOOD: Mood Detection](#3-tc-mood-mood-detection)
4. [TC-REC: Recommendations](#4-tc-rec-recommendations)
5. [TC-SEARCH: Search](#5-tc-search-search)
6. [TC-HIST: History](#6-tc-hist-history)
7. [TC-PLAY: Playlist](#7-tc-play-playlist)
8. [TC-UI: User Interface](#8-tc-ui-user-interface)

---

## 1. Giới thiệu

### 1.1 Mục đích

Tài liệu này mô tả các test case chức năng để kiểm thử hệ thống MusicMoodBot.

### 1.2 Phạm vi

| Module | Component | Priority |
|--------|-----------|----------|
| Authentication | Login, Signup, JWT | High |
| Mood Detection | Text Analysis, NLP | High |
| Recommendations | Smart Rec, By Mood | High |
| Search | TF-IDF, Vietnamese | Medium |
| History | Tracking, Analytics | Medium |
| Playlist | Curator, Harmonic | Medium |
| UI | All Screens | High |

### 1.3 Test Environment

- OS: Windows 10/11
- Python: 3.12
- Database: SQLite (fresh copy)
- Network: localhost

---

## 2. TC-AUTH: Authentication

### TC-AUTH-001: Đăng ký thành công

| Field | Value |
|-------|-------|
| **ID** | TC-AUTH-001 |
| **Title** | Đăng ký tài khoản mới thành công |
| **Priority** | High |
| **Preconditions** | Server đang chạy, username chưa tồn tại |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Mở ứng dụng | Màn hình Login hiển thị |
| 2 | Click "Đăng ký" | Chuyển sang form đăng ký |
| 3 | Nhập username: `testuser001` | Field hiển thị đúng |
| 4 | Nhập password: `Test@123` | Password masked |
| 5 | Click "Đăng ký" | Loading indicator hiển thị |
| 6 | Chờ response | Thông báo thành công |

**Expected Result:**
- Status: `success`
- User được tạo trong database
- Chuyển về màn hình Login

**Test Data:**
```json
{
  "username": "testuser001",
  "password": "Test@123"
}
```

---

### TC-AUTH-002: Đăng ký thất bại - Username đã tồn tại

| Field | Value |
|-------|-------|
| **ID** | TC-AUTH-002 |
| **Title** | Đăng ký với username đã tồn tại |
| **Priority** | High |
| **Preconditions** | Username `testuser001` đã tồn tại |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Mở form đăng ký | Form hiển thị |
| 2 | Nhập username: `testuser001` | Field hiển thị |
| 3 | Nhập password: `Test@456` | Password masked |
| 4 | Click "Đăng ký" | Loading indicator |
| 5 | Chờ response | Error message |

**Expected Result:**
- Status: `error`
- Message: "Username already exists"
- Không tạo user mới

---

### TC-AUTH-003: Đăng nhập thành công

| Field | Value |
|-------|-------|
| **ID** | TC-AUTH-003 |
| **Title** | Đăng nhập với credentials hợp lệ |
| **Priority** | High |
| **Preconditions** | User `testuser001` đã tồn tại |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Mở ứng dụng | Màn hình Login |
| 2 | Nhập username: `testuser001` | Field hiển thị |
| 3 | Nhập password: `Test@123` | Password masked |
| 4 | Click "Đăng nhập" | Loading indicator |
| 5 | Chờ response | JWT token received |
| 6 | Verify redirect | Chat screen hiển thị |

**Expected Result:**
- Status: `success`
- JWT token lưu local
- Redirect đến Chat screen
- Header hiển thị username

---

### TC-AUTH-004: Đăng nhập thất bại - Sai password

| Field | Value |
|-------|-------|
| **ID** | TC-AUTH-004 |
| **Title** | Đăng nhập với password sai |
| **Priority** | High |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Nhập username: `testuser001` | Field hiển thị |
| 2 | Nhập password: `wrongpassword` | Password masked |
| 3 | Click "Đăng nhập" | Loading indicator |
| 4 | Chờ response | Error message |

**Expected Result:**
- Status: `error`
- Message: "Invalid credentials"
- Không lưu token
- Không redirect

---

### TC-AUTH-005: JWT Token Expiration

| Field | Value |
|-------|-------|
| **ID** | TC-AUTH-005 |
| **Title** | Token hết hạn được xử lý đúng |
| **Priority** | Medium |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Đăng nhập thành công | Token received |
| 2 | Thay đổi token thành expired | Token modified |
| 3 | Gọi API cần auth | 401 Unauthorized |
| 4 | Verify redirect | Về màn hình Login |

---

## 3. TC-MOOD: Mood Detection

### TC-MOOD-001: Phát hiện mood Happy

| Field | Value |
|-------|-------|
| **ID** | TC-MOOD-001 |
| **Title** | Phát hiện mood vui vẻ từ text tiếng Việt |
| **Priority** | High |

**Test Data:**

| Input Text | Expected Mood | Expected Intensity |
|------------|---------------|-------------------|
| "Hôm nay tôi rất vui" | happy | medium |
| "Quá phấn khích luôn!!" | happy | high |
| "Thấy cũng vui vui" | happy | low |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Đăng nhập | Chat screen |
| 2 | Nhập: "Hôm nay tôi rất vui" | Message sent |
| 3 | Chờ response | Mood detected |
| 4 | Verify mood | mood = "happy" |
| 5 | Verify songs | Songs có valence cao |

---

### TC-MOOD-002: Phát hiện mood Sad

| Field | Value |
|-------|-------|
| **ID** | TC-MOOD-002 |
| **Title** | Phát hiện mood buồn từ text tiếng Việt |
| **Priority** | High |

**Test Data:**

| Input Text | Expected Mood | Expected Intensity |
|------------|---------------|-------------------|
| "Tôi buồn quá" | sad | medium |
| "Cảm thấy chán nản" | sad | medium |
| "Đau khổ vô cùng" | sad | high |
| "Hơi buồn một chút" | sad | low |

---

### TC-MOOD-003: Phát hiện mood Energetic

| Field | Value |
|-------|-------|
| **ID** | TC-MOOD-003 |
| **Title** | Phát hiện mood năng động |
| **Priority** | High |

**Test Data:**

| Input Text | Expected Mood |
|------------|---------------|
| "Muốn quẩy lên nào!" | energetic |
| "Đang tập gym, cần nhạc sôi động" | energetic |
| "Phê pha lên đê" | energetic |

---

### TC-MOOD-004: Phát hiện mood Calm

| Field | Value |
|-------|-------|
| **ID** | TC-MOOD-004 |
| **Title** | Phát hiện mood bình tĩnh |
| **Priority** | High |

**Test Data:**

| Input Text | Expected Mood |
|------------|---------------|
| "Muốn thư giãn" | calm |
| "Đang cần tĩnh lặng" | calm |
| "Nhạc nhẹ nhàng thôi" | calm |

---

### TC-MOOD-005: Phát hiện mood Romantic

| Field | Value |
|-------|-------|
| **ID** | TC-MOOD-005 |
| **Title** | Phát hiện mood lãng mạn |
| **Priority** | High |

**Test Data:**

| Input Text | Expected Mood |
|------------|---------------|
| "Đang yêu" | romantic |
| "Nhớ người yêu quá" | romantic |
| "Tình yêu thật đẹp" | romantic |

---

### TC-MOOD-006: Mood không xác định

| Field | Value |
|-------|-------|
| **ID** | TC-MOOD-006 |
| **Title** | Xử lý text không rõ mood |
| **Priority** | Medium |

**Test Data:**

| Input Text | Expected Mood |
|------------|---------------|
| "abc xyz" | neutral |
| "12345" | neutral |
| "" | neutral |

---

## 4. TC-REC: Recommendations

### TC-REC-001: Smart Recommendation

| Field | Value |
|-------|-------|
| **ID** | TC-REC-001 |
| **Title** | Gợi ý thông minh dựa trên text |
| **Priority** | High |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Nhập: "Cho tôi nhạc vui" | Request sent |
| 2 | Chờ response | Songs returned |
| 3 | Verify mood | All songs have mood=happy |
| 4 | Verify count | Có ít nhất 5 songs |
| 5 | Click play một bài | Song plays |

**Verification Criteria:**
- Tất cả songs phải có mood matching
- Valence trong range 0.6-1.0
- Energy trong range 0.4-0.8

---

### TC-REC-002: Recommendation by Mood & Intensity

| Field | Value |
|-------|-------|
| **ID** | TC-REC-002 |
| **Title** | Gợi ý theo mood và intensity cụ thể |
| **Priority** | High |

**Test Matrix:**

| Mood | Intensity | Min Valence | Max Valence | Min Energy | Max Energy |
|------|-----------|-------------|-------------|------------|------------|
| happy | high | 0.7 | 1.0 | 0.6 | 1.0 |
| happy | low | 0.5 | 0.7 | 0.3 | 0.5 |
| sad | high | 0.0 | 0.3 | 0.1 | 0.4 |
| energetic | high | 0.4 | 0.8 | 0.8 | 1.0 |

---

### TC-REC-003: User Preference Learning

| Field | Value |
|-------|-------|
| **ID** | TC-REC-003 |
| **Title** | Hệ thống học preference từ history |
| **Priority** | Medium |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Like 5 bài nhạc V-Pop | Actions recorded |
| 2 | Request recommendation | Get songs |
| 3 | Verify results | V-Pop được ưu tiên |

---

## 5. TC-SEARCH: Search

### TC-SEARCH-001: Tìm kiếm tiếng Việt

| Field | Value |
|-------|-------|
| **ID** | TC-SEARCH-001 |
| **Title** | Tìm kiếm bài hát tiếng Việt |
| **Priority** | High |

**Test Data:**

| Query | Expected Results |
|-------|-----------------|
| "Em của ngày hôm qua" | Bài của Sơn Tùng |
| "sơn tùng" | Các bài của Sơn Tùng |
| "buon" | Bài có "buồn" trong tên |

---

### TC-SEARCH-002: Fuzzy Search

| Field | Value |
|-------|-------|
| **ID** | TC-SEARCH-002 |
| **Title** | Tìm kiếm với lỗi chính tả nhỏ |
| **Priority** | Medium |

**Test Data:**

| Query (Typo) | Expected to Find |
|--------------|-----------------|
| "son tung" (không dấu) | Sơn Tùng M-TP |
| "em cua ngay" | Em Của Ngày Hôm Qua |

---

### TC-SEARCH-003: Search Empty Results

| Field | Value |
|-------|-------|
| **ID** | TC-SEARCH-003 |
| **Title** | Xử lý khi không có kết quả |
| **Priority** | Medium |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Search: "xyz123abc" | No results |
| 2 | Verify UI | "Không tìm thấy" message |
| 3 | Verify no error | App stable |

---

## 6. TC-HIST: History

### TC-HIST-001: Record Play History

| Field | Value |
|-------|-------|
| **ID** | TC-HIST-001 |
| **Title** | Ghi lại lịch sử nghe nhạc |
| **Priority** | High |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Play một bài hát | Song plays |
| 2 | Nghe 30+ giây | Duration recorded |
| 3 | Mở History screen | Entry hiển thị |
| 4 | Verify data | Title, artist, time correct |

---

### TC-HIST-002: Like/Dislike Actions

| Field | Value |
|-------|-------|
| **ID** | TC-HIST-002 |
| **Title** | Ghi nhận actions Like/Dislike |
| **Priority** | Medium |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Click Like trên bài hát | Like recorded |
| 2 | Verify in DB | action = "like" |
| 3 | Click Like lần nữa | Unlike (toggle) |
| 4 | Click Dislike | Dislike recorded |

---

## 7. TC-PLAY: Playlist

### TC-PLAY-001: Generate Playlist

| Field | Value |
|-------|-------|
| **ID** | TC-PLAY-001 |
| **Title** | Tạo playlist từ seed song |
| **Priority** | High |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Chọn một bài hát | Song selected |
| 2 | Click "Tạo Playlist" | Processing |
| 3 | Chờ response | Playlist generated |
| 4 | Verify length | 10 songs default |
| 5 | Verify transitions | Camelot compatible |

---

### TC-PLAY-002: Harmonic Mixing Validation

| Field | Value |
|-------|-------|
| **ID** | TC-PLAY-002 |
| **Title** | Kiểm tra Camelot wheel transitions |
| **Priority** | Medium |

**Camelot Compatibility Matrix:**

| From | Valid To |
|------|----------|
| 8A | 8A, 8B, 7A, 9A |
| 8B | 8B, 8A, 7B, 9B |

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Generate playlist | Playlist created |
| 2 | Check consecutive pairs | All Camelot compatible |
| 3 | Calculate transition score | Score > 0.8 |

---

## 8. TC-UI: User Interface

### TC-UI-001: Login Screen Layout

| Field | Value |
|-------|-------|
| **ID** | TC-UI-001 |
| **Title** | Kiểm tra layout màn hình Login |
| **Priority** | High |

**Checklist:**

| Element | Check | Status |
|---------|-------|--------|
| Logo/Title | Hiển thị đúng | ☐ |
| Username field | Có placeholder | ☐ |
| Password field | Masked input | ☐ |
| Login button | Enabled | ☐ |
| Signup link | Clickable | ☐ |
| Error area | Initially hidden | ☐ |

---

### TC-UI-002: Chat Screen Layout

| Field | Value |
|-------|-------|
| **ID** | TC-UI-002 |
| **Title** | Kiểm tra layout màn hình Chat |
| **Priority** | High |

**Checklist:**

| Element | Check | Status |
|---------|-------|--------|
| Header | Username hiển thị | ☐ |
| Message area | Scrollable | ☐ |
| Input field | Focused on load | ☐ |
| Send button | Disabled khi empty | ☐ |
| Song cards | Clickable | ☐ |
| Mood indicator | Shows detected mood | ☐ |

---

### TC-UI-003: Responsive Behavior

| Field | Value |
|-------|-------|
| **ID** | TC-UI-003 |
| **Title** | Kiểm tra responsive layout |
| **Priority** | Medium |

**Test Matrix:**

| Window Size | Expected Behavior |
|-------------|-------------------|
| 1920x1080 | Full layout |
| 1280x720 | Compact layout |
| 800x600 | Mobile-like layout |

---

### TC-UI-004: Loading States

| Field | Value |
|-------|-------|
| **ID** | TC-UI-004 |
| **Title** | Kiểm tra loading indicators |
| **Priority** | Medium |

**Scenarios:**

| Action | Loading Indicator |
|--------|-------------------|
| Login | Button spinner |
| Send message | Typing indicator |
| Load history | Skeleton cards |
| Generate playlist | Progress bar |

---

### TC-UI-005: Error States

| Field | Value |
|-------|-------|
| **ID** | TC-UI-005 |
| **Title** | Kiểm tra hiển thị lỗi |
| **Priority** | High |

**Scenarios:**

| Error Type | Expected Display |
|------------|------------------|
| Network error | "Không thể kết nối" dialog |
| Server error (500) | "Đã xảy ra lỗi" message |
| Validation error | Field-level error |
| Auth error | Redirect to login |

---

## Test Execution Summary

### Test Priority Matrix

| Priority | Count | Critical Path |
|----------|-------|---------------|
| High | 18 | ✓ |
| Medium | 12 | |
| Low | 0 | |

### Test Coverage

| Module | Test Cases | Coverage |
|--------|------------|----------|
| Authentication | 5 | 100% |
| Mood Detection | 6 | 100% |
| Recommendations | 3 | 90% |
| Search | 3 | 85% |
| History | 2 | 80% |
| Playlist | 2 | 80% |
| UI | 5 | 90% |

---

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| QA Lead | | | |
| Dev Lead | | | |
| Product Owner | | | |

---

*Document Version: 1.0.0*
*Created: February 2025*
*Last Updated: February 2025*
