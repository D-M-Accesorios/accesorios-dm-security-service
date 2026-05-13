from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.empleado import Empleado
from app.utils.security import decode_access_token

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Empleado:
    """Obtener el usuario actual a partir del token JWT"""
    token = credentials.credentials
    print(f"DEBUG: Token recibido: {token[:50]}...")  # Debug
    
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = int(payload.get("sub"))
    print(f"DEBUG: user_id: {user_id}")  # Debug
    
    user = db.query(Empleado).filter(Empleado.id_empleado == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def require_role(allowed_roles: list):
    """Dependencia para verificar roles permitidos"""
    def role_checker(current_user: Empleado = Depends(get_current_user)):
        from app.models.rol import Rol
        from app.database import SessionLocal
        
        db = SessionLocal()
        try:
            rol = db.query(Rol).filter(Rol.id_rol == current_user.id_rol).first()
            rol_nombre = rol.nombre if rol else None
            
            if rol_nombre not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Se requiere rol: {', '.join(allowed_roles)}"
                )
            return current_user
        finally:
            db.close()
    
    return role_checker