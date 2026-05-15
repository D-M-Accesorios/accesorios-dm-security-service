# ADR-002 — Resolución de Roles en Tiempo Real desde Base de Datos

## Metadatos

| Campo       | Valor                                                          |
|-------------|----------------------------------------------------------------|
| ID          | ADR-002                                                        |
| Título      | Resolución de Roles en Tiempo Real desde Base de Datos         |
| Categoría   | Behavioral                                                     |
| Estado      | Accepted — con deuda técnica en implementación                 |
| Fecha       | 2024 — HU-04 (Gestión de Roles)                               |
| Autores     | Equipo de desarrollo Accesorios DM                             |
| Relacionado | ADR-001, ADR-003                                               |

---

## Justificación de Categoría

**Behavioral** — Define el comportamiento del sistema durante la autorización de cada request HTTP: cómo y desde dónde se resuelve el rol del usuario para determinar si puede acceder a un recurso. Afecta la cantidad de consultas a la base de datos por request, la latencia de endpoints protegidos, y la coherencia de la autorización ante cambios de rol en tiempo real. Es una decisión de comportamiento en ejecución, no de estructura ni de diseño de componentes.

---

## Contexto

El JWT emitido por `POST /api/v1/auth/login` incluye el claim `rol` en su payload:

```json
{
  "sub": "1",
  "email": "admin@accesoriosdm.com",
  "rol": "ADMIN",
  "exp": 1700000000
}
```

Esto significa que la información de rol está disponible en el token decodificado sin necesidad de consultar la base de datos. Sin embargo, el microservicio implementa `require_role` en `utils/dependencies.py` que, en lugar de leer el claim `rol` del payload ya disponible, **realiza una nueva consulta a la tabla `security.rol`** para obtener el nombre del rol actual del empleado.

Esta es una decisión activa e implícita que separa la autenticación (confiar en el token) de la autorización (verificar el estado actual en BD).

El contexto de negocio que motiva esta decisión es la gestión dinámica de roles: un administrador puede reasignar el rol de un empleado en cualquier momento mediante `PATCH /api/v1/roles/{empleado_id}/rol/{rol_id}`. Si la autorización confiara en el claim del token, el empleado reasignado mantendría los permisos del rol anterior hasta que su token expirara (hasta 30 minutos por configuración).

---

## Decisión

Se tomó la decisión de **resolver el rol del empleado consultando en tiempo real la tabla `security.rol` en cada request autorizado**, ignorando el claim `rol` ya embebido en el JWT decodificado.

**Implementación concreta:**

```python
# utils/dependencies.py

def require_role(allowed_roles: list):
    """Dependencia para verificar roles permitidos"""
    def role_checker(current_user: Empleado = Depends(get_current_user)):
        # Abre una nueva sesión de BD — fuera del sistema DI de FastAPI
        db = SessionLocal()
        try:
            # Consulta en tiempo real: ignora el claim "rol" del JWT
            rol = db.query(Rol).filter(Rol.id_rol == current_user.id_rol).first()
            rol_nombre = rol.nombre if rol else None

            if rol_nombre not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Se requiere rol: {', '.join(allowed_roles)}"
                )
            return current_user
        finally:
            db.close()
    return role_checker
```

**Flujo de autorización por request:**

```
HTTP Request
    │
    ▼
get_current_user()
    ├── Decodifica JWT                       → payload con claim "rol" (IGNORADO)
    ├── Consulta BD #1: security.empleado    → carga Empleado + verifica estado
    │
    ▼
require_role(["ADMIN"])
    └── Consulta BD #2: security.rol         → resuelve nombre de rol actual
        └── Verifica: rol_nombre in allowed_roles
```

---

## Consecuencias

Cada request a un endpoint protegido por rol genera **dos consultas independientes a la base de datos**: una en `get_current_user` para cargar el `Empleado` y otra en `require_role` para cargar el `Rol`. El claim `rol` presente en el JWT queda como información decorativa en el token pero no tiene efecto en la autorización.

Cualquier cambio de rol aplicado mediante `PATCH /api/v1/roles/{empleado_id}/rol/{rol_id}` es efectivo en el **siguiente request** del empleado, sin necesidad de revocar ni regenerar el token existente.

---

## Ventajas

- **Consistencia inmediata de autorización:** Los cambios de rol son efectivos en tiempo real. Un empleado reasignado de `ADMIN` a `VENDEDOR` pierde acceso a los endpoints de administración en su próximo request.
- **Separación semántica correcta entre autenticación y autorización:** El token JWT demuestra *quién eres* (identidad verificada). La base de datos determina *qué puedes hacer* (permisos actuales). Esta separación está alineada con los principios de RBAC dinámico.
- **Resistencia a tokens con claims desactualizados:** Un token emitido antes de un cambio de rol no puede utilizarse para acceder a recursos del rol anterior.
- **Simplicidad operacional:** No requiere mecanismos adicionales de invalidación de tokens, listas de revocación ni notificaciones push a clientes para forzar re-autenticación tras cambios de rol.

---

## Desventajas

- **Overhead de consultas por request:** Todo endpoint protegido por `require_role` genera 2 consultas BD en lugar de 1.
- **Sesión de BD fuera del ciclo de inyección de dependencias:** `require_role` crea `db = SessionLocal()` manualmente en lugar de recibir la sesión mediante `Depends(get_db)`. La sesión no participa en la misma unidad de trabajo transaccional del request, e impide mockear la dependencia en tests unitarios.
- **Claim `rol` en el JWT es decorativo:** El token incluye el claim `rol` en su payload pero nunca se usa para autorización. Esto puede confundir a consumidores del token o a nuevos desarrolladores.
- **Acoplamiento a `security.rol`:** La función `require_role` tiene conocimiento directo del modelo `Rol` y del schema `security`.

---

## Alternativas Consideradas

| Alternativa                                          | Trade-off                                                                                                                |
|------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| **Leer el claim `rol` del JWT directamente**         | Elimina la consulta extra; el rol puede estar desactualizado hasta la expiración del token (hasta 30 min).               |
| **Cache de roles con TTL corto (ej: 60 segundos)**   | Reduce carga a BD; introduce estado en el servicio e inconsistencia temporal tolerable; requiere Redis o cache en memoria. |
| **Refresh token con re-emisión al cambiar rol**      | Semánticamente correcto; requiere implementar flujo completo de refresh tokens; añade complejidad al cliente.             |
| **Event-driven invalidation (mensaje en cola)**      | Solución óptima en producción; requiere infraestructura de mensajería (Kafka, RabbitMQ) fuera del alcance actual.        |

---

## Deuda Técnica Identificada

La implementación actual crea la sesión fuera del sistema DI de FastAPI. La corrección mantiene la decisión arquitectónica pero corrige la implementación:

```python
# Implementación mejorada — sesión gestionada por el DI de FastAPI
def require_role(allowed_roles: list):
    def role_checker(
        current_user: Empleado = Depends(get_current_user),
        db: Session = Depends(get_db)       # ← sesión inyectada correctamente
    ):
        rol = db.query(Rol).filter(Rol.id_rol == current_user.id_rol).first()
        rol_nombre = rol.nombre if rol else None
        if rol_nombre not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Se requiere rol: {', '.join(allowed_roles)}")
        return current_user
    return role_checker
```

---

## Relación con la Arquitectura Actual

Esta decisión es complementaria a ADR-001: mientras ADR-001 define cómo se verifica la identidad (autenticación), ADR-002 define cómo se verifican los permisos (autorización). Juntos conforman el pipeline completo de seguridad del microservicio.

La consulta de autorización accede a la tabla `security.rol` dependiendo de la segregación de datos definida en ADR-003.

**Véase también:** ADR-001 — Autenticación Stateless con JWT y HTTPBearer.
