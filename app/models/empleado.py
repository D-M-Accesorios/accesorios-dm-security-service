from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Empleado(Base):
    __tablename__ = "empleado"
    __table_args__ = {"schema": "security"}

    id_empleado = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(120), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())
    estado = Column(Boolean, default=True)
    id_rol = Column(Integer, ForeignKey("security.rol.id_rol"), nullable=False)