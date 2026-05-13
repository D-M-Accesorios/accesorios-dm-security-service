from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Rol(Base):
    __tablename__ = "rol"
    __table_args__ = {"schema": "security"}

    id_rol = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now())