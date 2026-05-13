from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.config import settings
import hashlib
import base64

# Función simple de hash para desarrollo
def get_password_hash(password: str) -> str:
    """Genera un hash simple usando SHA256 (solo para desarrollo)"""
    salt = "accesorios-dm-salt"
    hash_obj = hashlib.sha256(f"{salt}{password}".encode())
    return base64.b64encode(hash_obj.digest()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica la contraseña usando SHA256"""
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"DEBUG: Token decodificado: {payload}")  # Debug
        return payload
    except JWTError as e:
        print(f"DEBUG: Error decodificando token: {e}")  # Debug
        return None