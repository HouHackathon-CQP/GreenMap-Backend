# Đóng góp cho dự án

Cảm ơn bạn đã quan tâm đến việc đóng góp! 🎉  
Chúng tôi hoan nghênh mọi ý kiến, từ báo lỗi, đề xuất tính năng đến gửi pull request.

## Báo lỗi / Đề xuất tính năng

- Kiểm tra xem issue của bạn đã có ai tạo trước chưa.  
- Dùng tiêu đề rõ ràng, dễ hiểu.  
- Mô tả chi tiết: môi trường, bước tái hiện lỗi, mong đợi, kết quả thực tế.  

## Pull Request

1. Fork repository này.  
2. Tạo branch mới từ `main` (ví dụ: `fix/ten-bug` hoặc `feature/them-chuc-nang`).  
3. Commit thay đổi theo [Conventional Commits](#conventional-commits).  
4. Push lên fork của bạn và mở Pull Request.  
5. Mô tả chi tiết những gì bạn thay đổi.

## Conventional Commits

Dự án sử dụng [Conventional Commits](https://www.conventionalcommits.org/) để tự động tạo changelog.

### Format
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- **feat**: Tính năng mới (🚀 Features)
- **fix**: Sửa lỗi (🐛 Bug Fixes)
- **docs**: Cập nhật tài liệu (📚 Documentation)
- **style**: Thay đổi formatting, không ảnh hưởng code
- **refactor**: Tái cấu trúc code (🚜 Refactor)
- **perf**: Cải thiện hiệu suất (⚡ Performance)
- **test**: Thêm/sửa tests (🧪 Testing)
- **chore**: Maintenance tasks (⚙️ Miscellaneous)
- **ci**: CI/CD changes

### Ví dụ
```bash
feat(auth): add OAuth2 authentication
fix(api): resolve null pointer in weather endpoint
docs: update API documentation
refactor(database): optimize query performance
test(users): add unit tests for user service
chore(deps): update dependencies
```

### Breaking Changes
Nếu có thay đổi breaking, thêm `!` sau type hoặc thêm `BREAKING CHANGE:` trong footer:
```bash
feat(api)!: change response format for locations endpoint

BREAKING CHANGE: Response now returns array instead of object
```  

## Quy tắc code

- Tuân thủ chuẩn code của dự án.  
- Viết comment nếu code phức tạp.  
- Viết test cho tính năng mới nếu có thể.  

## Quy tắc cộng đồng

- Tôn trọng mọi người.  
- Giao tiếp lịch sự, không công kích cá nhân.  
- Hãy nhớ rằng chúng ta cùng nhau xây dựng cộng đồng này.

## Hỗ trợ

Nếu bạn có câu hỏi, vui lòng tạo issue hoặc liên hệ với nhóm quản trị dự án.