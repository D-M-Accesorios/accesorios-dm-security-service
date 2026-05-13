from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.empleado import Empleado
from app.models.rol import Rol
from app.schemas.empleado import (
    EmpleadoCreate, EmpleadoUpdate, EmpleadoResponse, ChangePasswordRequest
)
from app.utils.security import get_password_hash, verify_password
from app.utils.dependencies import get_current_user, require_role

router = APIRouter(prefix="/empleados", tags=["Empleados"])

@router.get("/", response_model=List[EmpleadoResponse])
def get_empleados(
    db: Session = Depends(get_db),
    current_user: Empleado = Depends(require_role(["ADMIN"]))
):
    """Listar todos los empleados"""
    empleados = db.query(Empleado).all()
    
    result = []
    for emp in empleados:
        rol = db.query(Rol).filter(Rol.id_rol == emp.id_rol).first()
        result.append(EmpleadoResponse(
            id_empleado=emp.id_empleado,
            nombre=emp.nombre,
            correo=emp.correo,
            id_rol=emp.id_rol,
            estado=emp.estado,
            fecha_creacion=emp.fecha_creacion,
            rol_nombre=rol.nombre if rol else None
        ))
    return result

@router.get("/{empleado_id}", response_model=EmpleadoResponse)
def get_empleado(
    empleado_id: int,
    db: Session = Depends(get_db),
    current_user: Empleado = Depends(require_role(["ADMIN"]))
):
    """Obtener empleado por ID"""
    empleado = db.query(Empleado).filter(Empleado.id_empleado == empleado_id).first()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    rol = db.query(Rol).filter(Rol.id_rol == empleado.id_rol).first()
    return EmpleadoResponse(
        id_empleado=empleado.id_empleado,
        nombre=empleado.nombre,
        correo=empleado.correo,
        id_rol=empleado.id_rol,
        estado=empleado.estado,
        fecha_creacion=empleado.fecha_creacion,
        rol_nombre=rol.nombre if rol else None
    )

@router.post("/", response_model=EmpleadoResponse, status_code=status.HTTP_201_CREATED)
def create_empleado(
    empleado_data: EmpleadoCreate,
    db: Session = Depends(get_db),
    current_user: Empleado = Depends(require_role(["ADMIN"]))
):
    """Crear nuevo empleado"""
    # Verificar si el correo ya existe
    existing = db.query(Empleado).filter(Empleado.correo == empleado_data.correo).first()
    if existing:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    # Verificar que el rol existe
    rol = db.query(Rol).filter(Rol.id_rol == empleado_data.id_rol).first()
    if not rol:
        raise HTTPException(status_code=400, detail="Rol no válido")
    
    nuevo_empleado = Empleado(
        nombre=empleado_data.nombre,
        correo=empleado_data.correo,
        password=get_password_hash(empleado_data.password),
        id_rol=empleado_data.id_rol,
        estado=empleado_data.estado
    )
    
    db.add(nuevo_empleado)
    db.commit()
    db.refresh(nuevo_empleado)
    
    return EmpleadoResponse(
        id_empleado=nuevo_empleado.id_empleado,
        nombre=nuevo_empleado.nombre,
        correo=nuevo_empleado.correo,
        id_rol=nuevo_empleado.id_rol,
        estado=nuevo_empleado.estado,
        fecha_creacion=nuevo_empleado.fecha_creacion,
        rol_nombre=rol.nombre
    )

@router.put("/{empleado_id}", response_model=EmpleadoResponse)
def update_empleado(
    empleado_id: int,
    empleado_data: EmpleadoUpdate,
    db: Session = Depends(get_db),
    current_user: Empleado = Depends(require_role(["ADMIN"]))
):
    """Actualizar empleado"""
    empleado = db.query(Empleado).filter(Empleado.id_empleado == empleado_id).first()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    if empleado_data.nombre is not None:
        empleado.nombre = empleado_data.nombre
    
    if empleado_data.correo is not None:
        # Verificar que el nuevo correo no esté en uso
        existing = db.query(Empleado).filter(
            Empleado.correo == empleado_data.correo,
            Empleado.id_empleado != empleado_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="El correo ya está registrado")
        empleado.correo = empleado_data.correo
    
    if empleado_data.password is not None:
        empleado.password = get_password_hash(empleado_data.password)
    
    if empleado_data.id_rol is not None:
        rol = db.query(Rol).filter(Rol.id_rol == empleado_data.id_rol).first()
        if not rol:
            raise HTTPException(status_code=400, detail="Rol no válido")
        empleado.id_rol = empleado_data.id_rol
    
    if empleado_data.estado is not None:
        empleado.estado = empleado_data.estado
    
    db.commit()
    db.refresh(empleado)
    
    rol = db.query(Rol).filter(Rol.id_rol == empleado.id_rol).first()
    return EmpleadoResponse(
        id_empleado=empleado.id_empleado,
        nombre=empleado.nombre,
        correo=empleado.correo,
        id_rol=empleado.id_rol,
        estado=empleado.estado,
        fecha_creacion=empleado.fecha_creacion,
        rol_nombre=rol.nombre if rol else None
    )

@router.delete("/{empleado_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_empleado(
    empleado_id: int,
    db: Session = Depends(get_db),
    current_user: Empleado = Depends(require_role(["ADMIN"]))
):
    """Eliminar empleado (no se puede eliminar a sí mismo)"""
    if current_user.id_empleado == empleado_id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    
    empleado = db.query(Empleado).filter(Empleado.id_empleado == empleado_id).first()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    db.delete(empleado)
    db.commit()

@router.patch("/{empleado_id}/toggle-estado")
def toggle_empleado_estado(
    empleado_id: int,
    db: Session = Depends(get_db),
    current_user: Empleado = Depends(require_role(["ADMIN"]))
):
    """Activar/Desactivar empleado"""
    if current_user.id_empleado == empleado_id:
        raise HTTPException(status_code=400, detail="No puedes cambiar el estado de tu propio usuario")
    
    empleado = db.query(Empleado).filter(Empleado.id_empleado == empleado_id).first()
    if not empleado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    empleado.estado = not empleado.estado
    db.commit()
    
    return {"message": f"Empleado {'activado' if empleado.estado else 'desactivado'}"}