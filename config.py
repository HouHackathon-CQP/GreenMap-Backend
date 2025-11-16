import os
from dotenv import load_dotenv

# --- TẢI BIẾN MÔI TRƯỜNG ---
load_dotenv()

# --- LẤY CÁC BIẾN ---
# Lấy khóa bí mật cho JWT từ .env
SECRET_KEY = os.getenv("SECRET_KEY")
# Lấy API key cho OpenAQ từ .env
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# --- Kiểm tra an toàn ---
if not SECRET_KEY:
    print("LỖI: Biến 'SECRET_KEY' không được tìm thấy trong file .env")
    # (Trong sản phẩm thật, bạn nên raise Exception ở đây)
if not OPENAQ_API_KEY:
    print("CẢNH BÁO: Biến 'OPENAQ_API_KEY' không được tìm thấy trong .env. Các cuộc gọi API OpenAQ có thể bị lỗi.")