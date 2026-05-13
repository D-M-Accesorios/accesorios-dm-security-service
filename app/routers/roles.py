from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.rol import Rol
from app.models.empleado import Empleado
from app.schemas.rol import RolCreate, RolUpdate, RolResponse
from app.utils.dependencies import get_current_user, require_role

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("/", response_model=List[RolResponse])
def get_roles(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    """Listar todos los roles (solo ADMIN)"""
    roles = db.query(Rol).all()
    return roles

@router.get("/{rol_id}", response_model=RolResponse)
def get_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    """Obtener rol por ID (solo ADMIN)"""
    rol = db.query(Rol).filter(Rol.id_rol == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol

@router.post("/", response_model=RolResponse, status_code=status.HTTP_201_CREATED)
def create_rol(
    rol_data: RolCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    """Crear nuevo rol (solo ADMIN)"""
    # Verificar si el nombre ya existe
    existing = db.query(Rol).filter(Rol.nombre == rol_data.nombre).first()
    if existing:
        raise HTTPException(status_code=400, detail="El nombre del rol ya existe")
    
    nuevo_rol = Rol(
        nombre=rol_data.nombre,
        descripcion=rol_data.descripcion
    )
    
    db.add(nuevo_rol)
    db.commit()
    db.refresh(nuevo_rol)
    
    return nuevo_rol

@router.put("/{rol_id}", response_model=RolResponse)
def update_rol(
    rol_id: int,
    rol_data: RolUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    """Actualizar rol (solo ADMIN)"""
    rol = db.query(Rol).filter(Rol.id_rol == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    if rol_data.nombre is not None:
        # Verificar que el nuevo nombre no esté en uso
        existing = db.query(Rol).filter(
            Rol.nombre == rol_data.nombre,
            Rol.id_rol != rol_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="El nombre del rol ya existe")
        rol.nombre = rol_data.nombre
    
    if rol_data.descripcion is not None:
        rol.descripcion = rol_data.descripcion
    
    db.commit()
    db.refresh(rol)
    
    return rol

@router.delete("/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rol(
    rol_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    """Eliminar rol (solo ADMIN)"""
    rol = db.query(Rol).filter(Rol.id_rol == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Verificar si hay empleados con este rol
    empleados = db.query(Empleado).filter(Empleado.id_rol == rol_id).first()
    if empleados:
        raise HTTPException(status_code=400, detail="No se puede eliminar un rol que tiene empleados asignados")
    
    db.delete(rol)
    db.commit()

@router.patch("/{empleado_id}/rol/{rol_id}")
def asignar_rol_empleado(
    empleado_id: int,
    rol_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))
):
    """Asignar rol a un empleado (solo ADMIN)"""
    empleado = db.query(Empleado).filter(Empleado.id_empleado == empleado_id).first()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    rol = db.query(Rol).filter(Rol.id_rol == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    empleado.id_rol = rol_id
    db.commit()
    
    return {"message": f"Rol '{rol.nombre}' asignado al empleado {empleado.nombre}"}