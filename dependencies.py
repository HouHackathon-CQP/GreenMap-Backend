from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
import config, crud, models, database
from models import User, UserRole

# Định nghĩa nơi lấy token (chính là đường dẫn API login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(database.get_db)
):
    """
    Hàm này sẽ tự động chạy mỗi khi có request vào API được bảo vệ.
    Nó kiểm tra Token -> Giải mã -> Lấy User từ CSDL.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 1. Giải mã Token bằng chìa khóa bí mật
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception # Token giả hoặc hết hạn
        
    # 2. Tìm user trong CSDL PostgreSQL
    user = await crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
        
    return user # Trả về object User cho API dùng

async def get_current_admin(
    current_user: User = Depends(get_current_user) # Gọi hàm trên để lấy user trước
):
    """
    Chỉ cho phép nếu user có role là ADMIN.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Bạn không có quyền Admin để thực hiện thao tác này."
        )
    return current_user

async def get_current_manager(
    current_user: User = Depends(get_current_user)
):
    """
    Cho phép nếu là MANAGER hoặc ADMIN.
    """
    if current_user.role not in [UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yêu cầu quyền Quản lý."
        )
    return current_user