from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class EmpleadoBase(BaseModel):
    nombre: str
    correo: EmailStr
    id_rol: int
    estado: Optional[bool] = True

class EmpleadoCreate(EmpleadoBase):
    password: str

class EmpleadoUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[EmailStr] = None
    password: Optional[str] = None
    id_rol: Optional[int] = None
    estado: Optional[bool] = None

class EmpleadoResponse(EmpleadoBase):
    id_empleado: int
    fecha_creacion: datetime
    rol_nombre: Optional[str] = None

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str