# ADR-006 — Hashing de Contraseñas con SHA-256 y Salt Estático

## Metadatos

| Campo       | Valor                                                   |
|-------------|---------------------------------------------------------|
| ID          | ADR-006                                                 |
| Título      | Hashing de Contraseñas con SHA-256 y Salt Estático      |
| Categoría   | Design                                                  |
| Estado      | Accepted — **RIESGO CRÍTICO DE SEGURIDAD ACTIVO**       |
| Fecha       | 2024 — HU-01 (Setup + Autenticación)                   |
| Autores     | Equipo de desarrollo Accesorios DM                      |
| Relacionado | ADR-001                                                 |

---

## Justificación de Categoría

**Design** — Define el diseño interno del componente de seguridad de credenciales: el algoritmo de hashing, la estrategia de salting y la librería utilizada. Afecta la resistencia del sistema ante ataques de fuerza bruta, la seguridad del almacenamiento de contraseñas en base de datos, y la estrategia de migración futura de hashes. Es una decisión de diseño de componente con impacto directo en la postura de seguridad del sistema.

---

## Contexto

El sistema requiere almacenar y verificar contraseñas de empleados en PostgreSQL. Al momento de implementar el módulo de autenticación, el proyecto declaró `passlib[bcrypt]==1.7.4` como dependencia en `requirements.txt`, provisionando la librería estándar de industria para hashing de contraseñas en Python.

Sin embargo, la implementación realizada en `utils/security.py` optó por un mecanismo diferente: un hash personalizado usando `hashlib.sha256` de la librería estándar de Python, con un salt de texto plano hardcodeado en el código fuente. El comentario del código marca explícitamente esta función como "solo para desarrollo", pero es la implementación activa en todos los ambientes incluyendo producción (`main`, puerto 8888).

```python
# utils/security.py — implementación actual
import hashlib
import base64

def get_password_hash(password: str) -> str:
    """Genera un hash simple usando SHA256 (solo para desarrollo)"""
    salt = "accesorios-dm-salt"       # salt estático hardcodeado
    hash_obj = hashlib.sha256(f"{salt}{password}".encode())
    return base64.b64encode(hash_obj.digest()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password
```

La dependencia `passlib[bcrypt]` está instalada en el entorno pero ninguna parte del código la importa o utiliza.

---

## Decisión

Se tomó la decisión de implementar el hashing de contraseñas usando **SHA-256 con un salt estático hardcodeado** (`"accesorios-dm-salt"`) en lugar de utilizar `passlib.bcrypt`. Esta función es invocada en:

- `routers/empleados.py` — al crear y actualizar empleados.
- `init_db.py` — al generar el hash del usuario administrador inicial.

---

## Consecuencias

Todos los hashes de contraseñas almacenados en `security.empleado.password` son determinísticos: dos empleados con la misma contraseña tendrán exactamente el mismo hash. El hash puede ser reproducido por cualquier persona con acceso al repositorio de código, dado que el salt es una constante de texto visible en el código fuente. La función es O(1) en tiempo de cómputo sin iteraciones configurables.

---

## Análisis de Riesgos de Seguridad

### Riesgo 1 — Velocidad de SHA-256 facilita ataques de fuerza bruta

SHA-256 es un algoritmo diseñado para velocidad, no para hashing de contraseñas:

| Algoritmo           | Velocidad en GPU moderna (RTX 4090) | Factor relativo         |
|---------------------|-------------------------------------|-------------------------|
| SHA-256             | ~10,000,000,000 H/s (10 GH/s)       | Baseline                |
| bcrypt (cost=12)    | ~100 H/s                            | 100,000,000x más lento  |
| Argon2id            | ~50 H/s                             | 200,000,000x más lento  |

### Riesgo 2 — Salt estático elimina la protección de salting

Con `salt = "accesorios-dm-salt"` fijo, `admin123` siempre produce el mismo hash. Si dos empleados usan la misma contraseña, tienen el mismo hash en BD; comprometer uno compromete al otro.

### Riesgo 3 — Salt expuesto en repositorio de código

El valor `"accesorios-dm-salt"` está en texto plano en el código fuente, visible para cualquier persona con acceso al repositorio. Esto permite precomputar rainbow tables para el sistema específico antes de obtener acceso a la BD.

### Riesgo 4 — `passlib` instalada pero no utilizada

La dependencia correcta (`passlib[bcrypt]==1.7.4`) está declarada en `requirements.txt` y disponible en el entorno, pero no se utiliza.

---

## Ventajas

- **Simplicidad de implementación:** Solo requiere la librería estándar de Python, sin configuración de parámetros de costo.
- **Verificación de latencia mínima:** SHA-256 ejecuta en microsegundos.

> **Nota arquitectónica:** La velocidad de SHA-256 que reduce la latencia de login es la misma característica que lo hace vulnerable a ataques offline. En el contexto de hashing de contraseñas, la velocidad es una desventaja de seguridad, no una ventaja operacional.

---

## Desventajas

- **Vulnerabilidad crítica a ataques de fuerza bruta offline:** Con el hash y el salt conocidos, un atacante puede realizar 10 GH/s de intentos. Las contraseñas débiles son recuperables en fracciones de segundo.
- **Salt estático invalida la seguridad de per-user salting:** Los beneficios fundamentales del salting son anulados por un salt fijo y conocido.
- **Hashes idénticos para contraseñas iguales:** Compromete múltiples cuentas con un único ataque exitoso.
- **Deuda técnica de migración costosa:** Cambiar el algoritmo de hashing requiere re-hashear todas las contraseñas existentes.
- **Inconsistencia entre comentario y realidad:** El comentario "solo para desarrollo" contradice el uso en producción, generando confianza falsa.

---

## Alternativas Consideradas

| Alternativa                         | Evaluación                                                                                                               |
|-------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| **`passlib.bcrypt` (ya instalado)** | **Recomendado:** Salt aleatorio por usuario, factor de costo configurable, estándar de industria, costo de migración mínimo. |
| **`passlib.argon2`**                | Ganador del Password Hashing Competition 2015; superior a bcrypt en resistencia a ataques de GPU y ASIC.                 |
| **PBKDF2-HMAC-SHA256 (stdlib)**     | Disponible en `hashlib` sin dependencias externas; permite iteraciones configurables; mejor que SHA-256 puro.            |
| **Argon2id via `argon2-cffi`**      | Mejor opción actual para nuevos proyectos; recomendado por OWASP 2024.                                                   |

---

## Migración Recomendada

La corrección tiene costo mínimo: `passlib` ya está instalada. El cambio es de 5 líneas en un único archivo:

```python
# utils/security.py — implementación recomendada
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)   # salt aleatorio generado automáticamente

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Estrategia de migración transparente de hashes existentes:**

```python
# Migración durante el login — re-hash automático sin disrupciones
def login(request: LoginRequest, db: Session):
    user = db.query(Empleado).filter(Empleado.correo == request.correo).first()

    if is_legacy_hash(user.password):
        if not verify_legacy_password(request.password, user.password):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        # Re-hashear con bcrypt de forma transparente en el próximo login
        user.password = get_password_hash(request.password)
        db.commit()
    else:
        if not verify_password(request.password, user.password):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
```

---

## Relación con la Arquitectura Actual

Esta función es el único punto de hashing de contraseñas en el sistema. Es invocada por `routers/empleados.py` en creación y actualización, y por `init_db.py` en el seed inicial. Un cambio en este componente requiere una estrategia de migración para los hashes existentes en `security.empleado`.

El endpoint de login en `routers/auth.py` depende de `verify_password` para validar credenciales antes de emitir el JWT. La integridad de toda la cadena de autenticación descansa sobre la seguridad de esta función.

**Véase también:** ADR-001 — Autenticación Stateless con JWT y HTTPBearer, cuyo endpoint de login es el principal consumidor de `verify_password`.
