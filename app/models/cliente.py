from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Cliente(Base):
    __tablename__ = "cliente"
    __table_args__ = {"schema": "clientes"}

    id_cliente = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(120), nullable=False, unique=True)
    telefono = Column(String(20), nullable=True)
    fecha_registro = Column(DateTime, server_default=func.now())