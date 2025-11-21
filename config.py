import os
from dotenv import load_dotenv

# --- TẢI BIẾN MÔI TRƯỜNG ---
load_dotenv()

# --- LẤY CÁC BIẾN ---
# Lấy khóa bí mật cho JWT từ .env
SECRET_KEY = os.getenv("SECRET_KEY")
# Lấy API key cho OpenAQ từ .env
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY")
# Lấy URL của Context Broker từ .env
ORION_BROKER_URL = os.getenv("ORION_BROKER_URL", "http://localhost:1026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

FIRST_SUPERUSER = os.getenv("FIRST_SUPERUSER", "admin@example.com")
FIRST_SUPERUSER_PASSWORD = os.getenv("FIRST_SUPERUSER_PASSWORD", "123456")