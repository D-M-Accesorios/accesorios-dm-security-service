from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.cliente import Cliente
from app.schemas.cliente import (
    ClienteCreate, ClienteUpdate, ClienteResponse
)
from app.utils.dependencies import get_current_user, require_role

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("/", response_model=List[ClienteResponse])
def get_clientes(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "VENDEDOR"]))
):
    """Listar todos los clientes"""
    clientes = db.query(Cliente).all()
    return clientes

@router.get("/{cliente_id}", response_model=ClienteResponse)
def get_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "VENDEDOR"]))
):
    """Obtener cliente por ID"""
    cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.get("/correo/{correo}", response_model=ClienteResponse)
def get_cliente_by_correo(
    correo: str,
    db: Session = Depends(get_db)
):
    """Obtener cliente por correo"""
    
    cliente = db.query(Cliente).filter(
        Cliente.correo == correo
    ).first()

    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    return cliente

@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def create_cliente(
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db)
):
    """Crear nuevo cliente"""
    # Verificar si el correo ya existe
    existing = db.query(Cliente).filter(Cliente.correo == cliente_data.correo).first()
    if existing:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    nuevo_cliente = Cliente(
        nombre=cliente_data.nombre,
        correo=cliente_data.correo,
        telefono=cliente_data.telefono
    )
    
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    
    return nuevo_cliente

@router.put("/{cliente_id}", response_model=ClienteResponse)
def update_cliente(
    cliente_id: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN", "VENDEDOR"]))
):
    """Actualizar cliente"""
    cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if cliente_data.nombre is not None:
        cliente.nombre = cliente_data.nombre
    
    if cliente_data.correo is not None:
        # Verificar que el nuevo correo no esté en uso
        existing = db.query(Cliente).filter(
            Cliente.correo == cliente_data.correo,
            Cliente.id_cliente != cliente_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="El correo ya está registrado")
        cliente.correo = cliente_data.correo
    
    if cliente_data.telefono is not None:
        cliente.telefono = cliente_data.telefono
    
    db.commit()
    db.refresh(cliente)
    
    return cliente

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    """Eliminar cliente (solo ADMIN)"""
    cliente = db.query(Cliente).filter(Cliente.id_cliente == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db.delete(cliente)
    db.commit()