# ADR-001 — Autenticación Stateless con JWT y HTTPBearer

## Metadatos

| Campo       | Valor                                              |
|-------------|----------------------------------------------------|
| ID          | ADR-001                                            |
| Título      | Autenticación Stateless con JWT y HTTPBearer       |
| Categoría   | Behavioral                                         |
| Estado      | Accepted                                           |
| Fecha       | 2024 — HU-01 (Setup + Autenticación)              |
| Autores     | Equipo de desarrollo Accesorios DM                 |
| Relacionado | ADR-002                                            |

---

## Justificación de Categoría

**Behavioral** — Define el comportamiento del sistema en tiempo de ejecución: cómo el servicio verifica la identidad del caller en cada request HTTP, cómo genera y valida tokens, y cómo responde ante credenciales inválidas o tokens expirados. No afecta la estructura de paquetes ni el diseño interno de componentes, sino el flujo de ejecución observable desde el exterior.

---

## Contexto

El microservicio `accesorios-dm-security-service` opera dentro de una arquitectura distribuida donde múltiples servicios necesitan verificar la identidad del caller. El sistema gestiona empleados internos de la plataforma e-commerce, no usuarios externos con flujos OAuth. Se requería un mecanismo de autenticación que cumpliera los siguientes criterios:

- **Stateless:** Sin necesidad de almacén de sesiones centralizado.
- **Portable:** Un token emitido por este servicio puede ser validado por otros microservicios del ecosistema que compartan el `SECRET_KEY`.
- **Compatible con clientes HTTP estándar:** Frontend web y otros microservicios deben consumir la API sin dependencias especiales.
- **Expiración configurable:** El TTL del token debe ser ajustable por ambiente sin cambios en el código.

FastAPI ofrece `OAuth2PasswordBearer` (recibe credenciales en `application/x-www-form-urlencoded`) y `HTTPBearer` (recibe el token en `Authorization: Bearer <token>` con body JSON). Dado que el sistema usa JSON como formato de intercambio en todos sus endpoints, `OAuth2PasswordBearer` requeriría un formato inconsistente con el resto de la API.

---

## Decisión

Se adoptó **JWT firmado con HS256** como mecanismo de autenticación stateless, transmitido mediante el esquema **HTTP Bearer Token** en el header `Authorization`.

**Implementación concreta:**

```python
# utils/security.py
from jose import jwt

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
```

```python
# utils/dependencies.py
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Empleado:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    user_id = int(payload.get("sub"))
    user = db.query(Empleado).filter(Empleado.id_empleado == user_id).first()
    if not user or not user.estado:
        raise HTTPException(status_code=401, ...)
    return user
```

**Payload del token:**
```json
{
  "sub": "1",
  "email": "admin@accesoriosdm.com",
  "rol": "ADMIN",
  "exp": 1700000000
}
```

El token es emitido por `POST /api/v1/auth/login` y validado en cada request protegido mediante la dependencia `get_current_user`, que actúa como middleware de autenticación declarativo en todos los routers.

---

## Consecuencias

El servicio nunca almacena estado de sesión. Cualquier instancia puede verificar cualquier token de forma autónoma sin coordinación entre réplicas. Los tokens son auto-contenidos: incluyen identidad (`sub`), email y rol del usuario autenticado, junto con su fecha de expiración (`exp`).

La verificación de `user.estado` en `get_current_user` añade una consulta a la base de datos por request, pero garantiza que empleados desactivados sean rechazados incluso con tokens válidos antes de su expiración.

---

## Ventajas

- **Escalabilidad horizontal real:** Múltiples instancias verifican tokens de forma independiente sin sticky sessions ni coordinación de estado.
- **Interoperabilidad entre microservicios:** Cualquier servicio del ecosistema que comparta el `SECRET_KEY` puede verificar el token, habilitando propagación de identidad sin llamadas adicionales al security service.
- **Sin infraestructura adicional:** Elimina la necesidad de Redis o tabla de sesiones para gestión de autenticación.
- **Estándar de industria:** JWT (RFC 7519) es compatible con API gateways, herramientas de monitoreo, proxies y clientes de cualquier plataforma.
- **Expiración configurable por ambiente:** `ACCESS_TOKEN_EXPIRE_MINUTES` como variable de entorno permite TTL diferente en develop, QA y producción sin modificar código.

---

## Desventajas

- **Revocación compleja:** No existe mecanismo nativo para invalidar un token antes de su expiración. Un empleado cuyo token fue comprometido mantiene acceso hasta que el token expire.
- **Rotación de SECRET_KEY es disruptiva:** Cambiar la clave invalida todos los tokens activos simultáneamente, forzando re-login de todos los usuarios.
- **HS256 es simétrico:** La misma clave firma y verifica tokens. No es posible delegar la verificación a un tercero sin también darle capacidad de emitir tokens.
- **Tamaño del token en cada request:** Las claims completas viajan en cada header HTTP, incrementando el tamaño de la petición.

---

## Alternativas Consideradas

| Alternativa                               | Razón de descarte                                                                                                     |
|-------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| **OAuth2 Password Flow**                  | Requiere `application/x-www-form-urlencoded`; inconsistente con el formato JSON del resto de la API.                 |
| **Sesiones con cookies + Redis**          | Introduce estado centralizado que contradice la naturaleza distribuida del microservicio; requiere infraestructura adicional. |
| **API Keys estáticas**                    | No soportan expiración ni claims dinámicos; inadecuado para usuarios con roles que pueden cambiar en tiempo real.     |
| **JWT con RS256 (asimétrico)**            | Correcto para federación entre dominios; agrega complejidad operacional injustificada para un ecosistema de microservicios propios. |
| **Session tokens opacos + BD**            | Requiere consulta a BD en cada request para resolver la sesión; no escala horizontalmente sin coordinación.           |

---

## Relación con la Arquitectura Actual

Esta decisión es el fundamento de toda la capa de seguridad del microservicio. `get_current_user` en `utils/dependencies.py` es la implementación concreta y actúa como la puerta de entrada declarativa para todos los endpoints protegidos. La función se inyecta en todos los routers (`auth`, `empleados`, `clientes`, `roles`) usando `Depends(get_current_user)` o `Depends(require_role([...]))`.

**Véase también:** ADR-002 — que define cómo se resuelve la autorización (roles) una vez que la autenticación (identidad) fue establecida por este mecanismo.
