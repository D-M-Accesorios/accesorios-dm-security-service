from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    correo: EmailStr
    password: str

class RegisterRequest(BaseModel):
    nombre: str
    correo: EmailStr
    password: str
    telefono: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    nombre: str
    correo: str
    rol: str

class UserResponse(BaseModel):
    id: int
    nombre: str
    correo: str
    rol: str
    estado: bool

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str