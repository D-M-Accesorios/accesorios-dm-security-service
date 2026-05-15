# ADR-004 — Arquitectura en 4 Capas: models / schemas / routers / utils

## Metadatos

| Campo       | Valor                                                       |
|-------------|-------------------------------------------------------------|
| ID          | ADR-004                                                     |
| Título      | Arquitectura en 4 Capas: models / schemas / routers / utils |
| Categoría   | Structural                                                  |
| Estado      | Accepted                                                    |
| Fecha       | 2024 — HU-01 (Setup inicial del microservicio)             |
| Autores     | Equipo de desarrollo Accesorios DM                          |
| Relacionado | ADR-003, ADR-005                                            |

---

## Justificación de Categoría

**Structural** — Define la organización física y lógica del código fuente: cómo se dividen los módulos, qué responsabilidades asume cada paquete, y cuáles son las dependencias permitidas entre capas. Afecta directamente la mantenibilidad, la navegabilidad del código y la escalabilidad del equipo de desarrollo. Es una decisión de estructura, no de comportamiento en tiempo de ejecución ni de diseño interno de componentes individuales.

---

## Contexto

FastAPI es un framework que no impone una estructura de proyecto. El microservicio gestiona cuatro recursos de negocio (autenticación, empleados, clientes, roles) con lógica compartida de seguridad (JWT, verificación de roles) y acceso a base de datos. Sin una estructura definida, la base de código tendería al crecimiento desordenado: lógica de validación mezclada con acceso a BD, endpoints con dependencias circulares, y dificultad para localizar código relacionado.

La decisión debía balancear navegabilidad, separación de responsabilidades y complejidad apropiada para el alcance del microservicio.

---

## Decisión

Se adoptó una **arquitectura en 4 capas con separación por responsabilidad técnica** (layer-based architecture), implementada mediante cuatro paquetes Python dentro de `app/`:

```
app/
├── models/       → Capa de datos: entidades SQLAlchemy (mapeo ORM ↔ PostgreSQL)
├── schemas/      → Capa de contrato: validación de entrada y serialización de salida (Pydantic)
├── routers/      → Capa de aplicación: endpoints HTTP, orquestación y lógica de negocio
└── utils/        → Capa transversal: JWT, hashing, dependencias de autenticación/autorización
```

**Flujo de datos unidireccional:**

```
HTTP Request
    │
    ▼
routers/           ← recibe el request HTTP, valida con schemas, coordina la lógica
    ├── schemas/   ← valida y deserializa el body de entrada (Pydantic)
    ├── models/    ← persiste y recupera datos (SQLAlchemy ORM)
    └── utils/     ← verifica identidad y permisos (JWT, require_role)
    │
    ▼
HTTP Response      ← serializado por el schema Response correspondiente
```

**Dependencias entre capas:**

| Capa        | Depende de                                    |
|-------------|-----------------------------------------------|
| `routers/`  | `schemas/`, `models/`, `utils/`, `database`   |
| `schemas/`  | Sin dependencias internas (solo Pydantic)     |
| `models/`   | `database` (Base, engine)                     |
| `utils/`    | `models/`, `config`, `database`               |

**Ejemplo de implementación del patrón en un router:**

```python
# routers/empleados.py
from app.models.empleado import Empleado
from app.schemas.empleado import EmpleadoCreate, EmpleadoResponse
from app.utils.dependencies import require_role
from app.database import get_db

router = APIRouter(prefix="/empleados", tags=["Empleados"])

@router.post("/", response_model=EmpleadoResponse, status_code=201)
def create_empleado(
    empleado_data: EmpleadoCreate,               # schema valida entrada
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["ADMIN"]))  # utils verifica permisos
):
    nuevo_empleado = Empleado(**empleado_data.dict())
    db.add(nuevo_empleado)
    db.commit()
    return nuevo_empleado                         # schema serializa salida
```

---

## Consecuencias

La lógica de negocio reside directamente en los routers, sin una capa de servicios/use-cases intermedios. Cada capa tiene una responsabilidad única y predecible. El directorio `utils/` agrupa funcionalidades transversales consumidas por múltiples routers.

---

## Ventajas

- **Navegabilidad predecible:** La localización de cualquier pieza de código sigue una convención constante para todos los recursos del sistema.
- **Bajo costo de onboarding:** La estructura mapea directamente a conceptos nativos de FastAPI (Router, Schema Pydantic, Model SQLAlchemy).
- **Separación de contrato de API del modelo de datos:** Un cambio en el esquema de BD no necesariamente impacta la interfaz pública y viceversa.
- **Reutilización de lógica transversal:** `utils/dependencies.py` con `get_current_user` y `require_role` es un único punto de implementación consumido por todos los routers.
- **Testabilidad por capas:** Los schemas pueden testearse de forma unitaria sin el ORM. Los routers pueden testearse con TestClient mockeando las dependencias de `utils/`.

---

## Desventajas

- **Ausencia de Service Layer:** Toda la lógica de negocio vive directamente en los routers. Al escalar la complejidad del dominio, esto producirá routers que mezclan lógica HTTP con lógica de negocio, violando el Principio de Responsabilidad Única.
- **Escalabilidad de feature limitada:** No existe una capa natural donde colocar lógica compartida entre dos routers sin duplicar código o crear acoplamiento entre ellos.
- **Layer-based vs Feature-based:** A medida que el sistema incorpora más recursos, el número de archivos en cada capa crece linealmente, dificultando la navegación.
- **`utils/` como capa mixta:** Agrupa lógica de seguridad transversal con potenciales futuras utilidades sin una categorización clara.

---

## Alternativas Consideradas

| Alternativa                                   | Trade-off                                                                                                               |
|-----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| **Organización por feature (vertical slices)**| Mejor escalabilidad para equipos grandes; cada feature es autocontenida; mayor overhead inicial de configuración.       |
| **5 capas con Service Layer explícito**        | Recomendado como evolución natural; añadir `services/` entre `routers/` y `models/` encapsula la lógica de negocio.    |
| **Arquitectura hexagonal (ports & adapters)** | Máximo desacoplamiento; excesivamente compleja para el alcance actual del microservicio.                                |
| **Capa plana (todo en `app/`)**               | Configuración mínima; impracticable con más de 3-4 recursos.                                                            |

---

## Evolución Recomendada

Cuando la lógica de negocio en los routers supere las 50 líneas por endpoint, se recomienda extraer una capa `services/`:

```
app/
├── models/
├── schemas/
├── services/     ← nueva capa: lógica de negocio pura, sin dependencias HTTP
├── routers/      ← delgados: solo reciben request, delegan a services, retornan response
└── utils/
```

---

## Relación con la Arquitectura Actual

Esta decisión define la anatomía completa del microservicio. Se relaciona con ADR-003 (los modelos en `models/` reflejan la segregación de schemas de BD) y con ADR-005 (los schemas Pydantic en `schemas/` implementan el patrón jerárquico de contratos de API). El archivo `app/main.py` es el punto de ensamblaje donde los routers son registrados con el prefijo `/api/v1`.

**Véase también:** ADR-005 — Patrón de Jerarquía de Schemas Pydantic, que define el diseño interno de la capa `schemas/`.
