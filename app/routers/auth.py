from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.models.empleado import Empleado
from app.models.rol import Rol
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.security import verify_password, create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    from app.models.rol import Rol
    
    # Buscar en empleados
    user = db.query(Empleado).filter(Empleado.correo == request.correo).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    if not user.estado:
        raise HTTPException(status_code=401, detail="Usuario inactivo")
    
    # Obtener rol
    rol = db.query(Rol).filter(Rol.id_rol == user.id_rol).first()
    rol_nombre = rol.nombre if rol else "CLIENTE"
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id_empleado), "email": user.correo, "rol": rol_nombre},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id_empleado,
        nombre=user.nombre,
        correo=user.correo,
        rol=rol_nombre
    )