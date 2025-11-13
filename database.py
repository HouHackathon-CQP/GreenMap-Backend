from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 1. CHUỖI KẾT NỐI (Connection String)
#    Định dạng: "postgresql+driver://user:password@host:port/dbname"
#    Host là 'localhost' vì Docker đang 'map' cổng 5432 ra máy thật
DATABASE_URL = "postgresql+asyncpg://admin:mysecretpassword@localhost:5432/greenmap_db"


# 2. TẠO "CỖ MÁY" KẾT NỐI (Engine)
#    Đây là "cửa ngõ" chính mà SQLAlchemy dùng để nói chuyện với PostGIS.
engine = create_async_engine(DATABASE_URL, echo=True) # echo=True để xem log SQL (tốt khi debug)


# 3. TẠO "PHIÊN LÀM VIỆC" (Session)
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False, 
    autoflush=False,
    autocommit=False
)

# 4. LỚP "CHA" CHO CÁC MODELS
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