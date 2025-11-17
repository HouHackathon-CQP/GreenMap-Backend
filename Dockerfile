# 1. Sử dụng image Python 3.11 mỏng nhẹ
FROM python:3.11-slim

# 2. Đặt thư mục làm việc bên trong container
WORKDIR /app

# 3. Sao chép file requirements và cài đặt thư viện
# Tách ra để tận dụng Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Sao chép toàn bộ mã nguồn (.py) vào container
COPY . .

# 5. Mở cổng 8000 (cổng FastAPI chạy)
EXPOSE 8000

# 6. Lệnh để chạy ứng dụng khi container khởi động
# Sử dụng uvicorn và bật --reload để code tự cập nhật khi bạn sửa file
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]