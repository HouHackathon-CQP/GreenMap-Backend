import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# --- TẢI BIẾN MÔI TRƯỜNG ---
# Tải biến môi trường (ví dụ: POSTGRES_HOST) từ file .env
load_dotenv()

# --- CẤU HÌNH DATABASE_URL ---
# 1. Lấy host CSDL từ .env, nếu không có thì mặc định là 'localhost'
#    (Khi chạy trong Docker, .env sẽ cung cấp POSTGRES_HOST=postgres-db)
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")

# 2. CHUỖI KẾT NỐI (Connection String)
#    Sử dụng biến POSTGRES_HOST thay vì "localhost" cứng
DATABASE_URL = "postgresql+asyncpg://greenmap:12345678@160.250.5.180:5432/greenmap"


# 3. TẠO "CỖ MÁY" KẾT NỐI (Engine)
#    Đây là "cửa ngõ" chính mà SQLAlchemy dùng để nói chuyện với PostGIS.
engine = create_async_engine(DATABASE_URL, echo=True) # echo=True để xem log SQL (tốt khi debug)


# 4. TẠO "PHIÊN LÀM VIỆC" (Session)
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False, 
    autoflush=False,
    autocommit=False
)

# 5. LỚP "CHA" CHO CÁC MODELS
#    Sau này, khi bạn tạo Bảng (ví dụ: bảng User, Bảng Sensor),
#    chúng sẽ kế thừa từ lớp 'Base' này.
Base = declarative_base()


# -----------------------------------------------------------
# PHẦN QUAN TRỌNG: Hàm "Dependency" cho FastAPI
# -----------------------------------------------------------
async def get_db():
    """
    Hàm này tạo ra một phiên (session) CSDL mới cho mỗi request,
    làm việc của nó, rồi đóng lại.
    """
    async with SessionLocal() as session:
        try:
            yield session # Giao "chìa khóa" CSDL cho API
        finally:
            await session.close()