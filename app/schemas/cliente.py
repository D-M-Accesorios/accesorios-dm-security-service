from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ClienteBase(BaseModel):
    nombre: str
    correo: EmailStr
    telefono: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None

class ClienteResponse(ClienteBase):
    id_cliente: int
    fecha_registro: datetime

    class Config:
        from_attributes = True