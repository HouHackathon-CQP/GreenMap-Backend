from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Khởi tạo "máy băm" bcrypt
# Nó sẽ biết rằng mật khẩu đang được băm bằng bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra mật khẩu "chay" (từ login) với mật khẩu "băm" (trong CSDL).
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    "Băm" một mật khẩu "chay" thành dạng không thể dịch ngược.
    """
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Tạo ra một "vé thông hành" (JWT) mới.
    """
    to_encode = data.copy()
    
    # Tính thời gian hết hạn
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # "Ký tên" vào vé
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Hàm "kiểm tra vé"
def verify_token(token: str, credentials_exception):
    """Kiểm tra xem "vé" có hợp lệ không."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email # Trả về email (payload)
    except JWTError:
        raise credentials_exception