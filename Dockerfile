# Sử dụng Python 3.11
FROM python:3.11-slim

# Không tạo .pyc + log trực tiếp ra stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cài các gói hệ thống cần thiết (nếu lib của bạn cần build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Thư mục làm việc trong container
WORKDIR /app

# Copy requirements trước để tận dụng cache
COPY requirements.txt .

# Cài thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code vào container (trừ những thứ nằm trong .dockerignore)
COPY . .

# FastAPI/Uvicorn sẽ chạy port 8000
EXPOSE 8000

# ---- QUAN TRỌNG ----
# Nếu biến app = FastAPI() nằm trong main.py -> dùng "main:app"
# Nếu nằm trong app/main.py với biến app -> dùng "app.main:app"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
