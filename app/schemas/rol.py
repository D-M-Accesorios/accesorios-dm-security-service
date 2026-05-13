from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RolBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class RolCreate(RolBase):
    pass

class RolUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class RolResponse(RolBase):
    id_rol: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True