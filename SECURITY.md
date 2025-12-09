# Chính Sách Bảo Mật (Security Policy)

## Các Phiên Bản Được Hỗ Trợ

Chúng tôi cam kết hỗ trợ bảo mật cho các phiên bản sau của GreenMap Backend:

| Phiên Bản | Được Hỗ Trợ          |
| --------- | -------------------- |
| 1.0.x     | :white_check_mark:   |
| < 1.0     | :x:                  |

## Báo Cáo Lỗ Hổng Bảo Mật

Chúng tôi rất coi trọng vấn đề bảo mật. Nếu bạn phát hiện lỗ hổng bảo mật trong dự án này, vui lòng báo cáo **một cách có trách nhiệm**.

### ⚠️ QUAN TRỌNG: KHÔNG tạo public issue cho lỗ hổng bảo mật

### Cách Báo Cáo

Vui lòng báo cáo lỗ hổng bảo mật thông qua một trong các cách sau:

1. **GitHub Security Advisory (Khuyến nghị)**
   - Truy cập: https://github.com/HouHackathon-CQP/GreenMap-Backend/security/advisories
   - Click "Report a vulnerability"
   - Điền đầy đủ thông tin về lỗ hổng

2. **Email riêng tư**
   - Gửi email đến: trantrongchien05@gmail.com
   - Tiêu đề: `[SECURITY] GreenMap Backend - [Mô tả ngắn]`

### Thông Tin Cần Cung Cấp

Để giúp chúng tôi hiểu và xử lý vấn đề nhanh chóng, vui lòng bao gồm:

1. **Mô tả chi tiết** về lỗ hổng
2. **Các bước tái hiện** (step-by-step)
3. **Tác động tiềm ẩn** (ví dụ: rò rỉ dữ liệu, truy cập trái phép)
4. **Phiên bản bị ảnh hưởng**
5. **Proof of Concept** (nếu có)
6. **Đề xuất giải pháp** (nếu có)

### Ví Dụ Báo Cáo

```
**Tiêu đề**: SQL Injection trong endpoint /api/users

**Mô tả**: 
Endpoint /api/users/{user_id} dễ bị tấn công SQL injection do không 
sanitize input đúng cách.

**Các bước tái hiện**:
1. Gửi request: GET /api/users/1' OR '1'='1
2. Quan sát response trả về tất cả users
3. ...

**Tác động**:
- Attacker có thể truy cập thông tin của tất cả users
- Có thể thực hiện các thao tác CRUD trên database

**Phiên bản**: v1.0.0

**Đề xuất**: Sử dụng parameterized queries hoặc ORM properly
```

## Quy Trình Xử Lý

1. **Xác nhận** - Chúng tôi sẽ xác nhận đã nhận được báo cáo trong vòng **48 giờ**
2. **Đánh giá** - Phân tích mức độ nghiêm trọng và tác động
3. **Phát triển Fix** - Xây dựng bản vá lỗi
4. **Testing** - Kiểm tra kỹ lưỡng
5. **Release** - Phát hành bản cập nhật bảo mật
6. **Công bố** - Thông báo công khai sau khi đã patch (nếu phù hợp)

### Thời Gian Xử Lý Dự Kiến

| Mức Độ Nghiêm Trọng | Thời Gian Xử Lý |
| -------------------- | --------------- |
| Critical             | 1-7 ngày        |
| High                 | 7-30 ngày       |
| Medium               | 30-90 ngày      |
| Low                  | 90+ ngày        |

## Chính Sách Công Bố

- Chúng tôi tuân theo nguyên tắc **Responsible Disclosure**
- Thông tin lỗ hổng sẽ được giữ bí mật cho đến khi có bản vá
- Người báo cáo sẽ được **credit** (nếu muốn) trong security advisory
- Thời gian embargo mặc định: **90 ngày** hoặc cho đến khi patch được release

## Best Practices Bảo Mật

### Cho Contributors

- **KHÔNG** commit sensitive data (API keys, passwords, tokens)
- Sử dụng `.env` cho configuration, không hardcode
- Tuân thủ OWASP Top 10
- Review code kỹ lưỡng trước khi PR
- Cập nhật dependencies thường xuyên

### Cho Users

- Luôn sử dụng **phiên bản mới nhất**
- Đổi các **default credentials** ngay lập tức
- Sử dụng **HTTPS** trong production
- Giới hạn quyền truy cập database
- Backup dữ liệu thường xuyên
- Theo dõi [CHANGELOG.md](CHANGELOG.md) và [GitHub Security Advisories](https://github.com/HouHackathon-CQP/GreenMap-Backend/security/advisories)

## Các Vấn Đề Bảo Mật Đã Biết

Hiện tại không có lỗ hổng bảo mật đã biết nào đang ảnh hưởng đến phiên bản được hỗ trợ.

Lịch sử các security advisories: https://github.com/HouHackathon-CQP/GreenMap-Backend/security/advisories

## Dependencies và CVE

Chúng tôi sử dụng các công cụ sau để theo dõi lỗ hổng trong dependencies:

- GitHub Dependabot
- `pip-audit` cho Python packages
- Định kỳ review `requirements.txt`

## Liên Hệ

- **GitHub Issues** (cho các vấn đề không phải bảo mật): https://github.com/HouHackathon-CQP/GreenMap-Backend/issues
- **Security Advisory**: https://github.com/HouHackathon-CQP/GreenMap-Backend/security/advisories

---

**Cảm ơn bạn đã giúp giữ cho GreenMap Backend an toàn!** 🔒
