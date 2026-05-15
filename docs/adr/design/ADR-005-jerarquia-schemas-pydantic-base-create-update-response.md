# ADR-005 — Patrón de Jerarquía de Schemas Pydantic (Base / Create / Update / Response)

## Metadatos

| Campo       | Valor                                                                        |
|-------------|------------------------------------------------------------------------------|
| ID          | ADR-005                                                                      |
| Título      | Patrón de Jerarquía de Schemas Pydantic (Base / Create / Update / Response) |
| Categoría   | Design                                                                       |
| Estado      | Accepted                                                                     |
| Fecha       | 2024 — HU-01 a HU-04                                                        |
| Autores     | Equipo de desarrollo Accesorios DM                                           |
| Relacionado | ADR-001, ADR-004                                                             |

---

## Justificación de Categoría

**Design** — Define el diseño interno de los componentes de contrato de la API: cómo se estructuran y organizan los schemas Pydantic, qué relaciones de herencia existen entre ellos, y cómo se dividen las responsabilidades de validación de entrada, actualización parcial y serialización de salida. Afecta el diseño de la interfaz pública del servicio y la seguridad por diseño del sistema de contratos. No define comportamiento en tiempo de ejecución ni la organización estructural de paquetes.

---

## Contexto

FastAPI utiliza modelos Pydantic para validar el cuerpo de los requests de entrada y para serializar las respuestas de salida. Cada recurso de negocio (Empleado, Cliente, Rol) requiere múltiples contratos con características distintas:

- **Creación:** Requiere todos los campos obligatorios, incluyendo `password` para Empleado.
- **Actualización parcial:** Todos los campos deben ser opcionales para permitir modificar solo los campos necesarios.
- **Respuesta:** Incluye campos generados por el servidor (`id`, `fecha_creacion`) y excluye campos sensibles (`password`).

Sin un patrón establecido, cada desarrollador podría definir sus schemas de forma ad-hoc, produciendo inconsistencias entre recursos, duplicación de campos, y potenciales filtraciones de datos sensibles en las respuestas.

---

## Decisión

Se adoptó un **patrón de jerarquía de herencia** en los schemas Pydantic con cuatro variantes por recurso:

1. **`Base`:** Campos comunes a creación y respuesta. Sirve como clase padre.
2. **`Create`:** Hereda de `Base` y añade campos requeridos solo en creación (ej: `password`).
3. **`Update`:** No hereda de `Base`. Define todos los campos como `Optional` para actualizaciones parciales.
4. **`Response`:** Hereda de `Base` y añade campos generados por el servidor. Habilita `from_attributes = True` para serializar desde instancias ORM.

**Implementación completa del patrón — Recurso Empleado:**

```python
# schemas/empleado.py

class EmpleadoBase(BaseModel):
    nombre: str
    correo: EmailStr          # validación automática de formato de email
    id_rol: int
    estado: Optional[bool] = True

class EmpleadoCreate(EmpleadoBase):
    password: str             # solo presente en creación, nunca en respuesta

class EmpleadoUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[EmailStr] = None
    password: Optional[str] = None
    id_rol: Optional[int] = None
    estado: Optional[bool] = None

class EmpleadoResponse(EmpleadoBase):
    id_empleado: int          # generado por el servidor
    fecha_creacion: datetime  # generado por el servidor
    rol_nombre: Optional[str] = None

    class Config:
        from_attributes = True  # Pydantic v2: serializa desde instancias SQLAlchemy
```

**Implementación del patrón — Recurso Cliente:**

```python
# schemas/cliente.py

class ClienteBase(BaseModel):
    nombre: str
    correo: EmailStr
    telefono: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass                      # sin campos adicionales: herencia directa

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = None

class ClienteResponse(ClienteBase):
    id_cliente: int
    fecha_registro: datetime

    class Config:
        from_attributes = True
```

**Uso en routers:**

```python
# El schema Create valida la entrada; el schema Response serializa la salida
@router.post("/", response_model=EmpleadoResponse, status_code=201)
def create_empleado(
    empleado_data: EmpleadoCreate,    # ← valida entrada, incluye password
    ...
):
    ...
    return nuevo_empleado             # ← EmpleadoResponse excluye password automáticamente
```

---

## Consecuencias

El API tiene contratos de entrada y salida explícitamente separados en cada recurso. El modelo ORM nunca se expone directamente al cliente. Los campos sensibles como `password` son estructuralmente imposibles de aparecer en ninguna respuesta del servicio. FastAPI genera documentación OpenAPI automáticamente basada en estos schemas.

---

## Ventajas

- **Seguridad por diseño:** `password` está en `EmpleadoCreate` y `EmpleadoUpdate` para recibir contraseñas, pero ausente en `EmpleadoResponse`. Es estructuralmente imposible filtrar el hash en cualquier respuesta de la API.
- **DRY mediante herencia:** Los campos comunes se definen una vez en `Base`. Una corrección en la validación de `correo: EmailStr` se propaga automáticamente a `Create` y `Response`.
- **Semántica de actualización parcial correcta:** `EmpleadoUpdate` con todos los campos `Optional` implementa la semántica PATCH correcta.
- **Documentación automática de calidad:** FastAPI usa estos schemas para generar el contrato OpenAPI en `/docs`.
- **Validación automática en frontera del sistema:** `EmailStr` garantiza que correos malformados son rechazados con error 422 antes de ejecutar lógica de negocio.
- **`from_attributes = True` en Response:** Permite que FastAPI serialice directamente instancias del ORM SQLAlchemy sin conversión manual.

---

## Desventajas

- **`EmpleadoUpdate` no hereda `EmpleadoBase`:** Ruptura necesaria de la jerarquía que introduce un punto de divergencia silencioso: nuevos campos en `Base` deben añadirse manualmente a `Update`.
- **Proliferación de clases:** Con 4 recursos y 4 schemas por recurso, el proyecto gestiona 16+ clases de schema.
- **`ChangePasswordRequest` duplicado:** Este schema está definido en `schemas/auth.py` y también en `schemas/empleado.py`, violando DRY.
- **`RegisterRequest` es schema huérfano:** Definido en `schemas/auth.py` pero sin endpoint de registro público que lo utilice.

---

## Alternativas Consideradas

| Alternativa                                        | Trade-off                                                                                                             |
|----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| **Schema único con todos los campos `Optional`**   | Elimina la jerarquía; pierde type safety, validación de campos obligatorios en creación, y exclusión de campos sensibles. |
| **Marshmallow**                                    | Más verbosa; Pydantic v2 es superior en performance, ergonomía e integración nativa con FastAPI.                      |
| **Dataclasses de Python con validación manual**    | Sin validación automática de tipos ni de formato; no genera documentación OpenAPI; mayor código boilerplate.          |
| **Schema único con `model_validator`**             | Un único modelo con lógica condicional según la operación; añade complejidad interna al schema.                       |

---

## Relación con la Arquitectura Actual

Esta decisión define el diseño de la capa `schemas/` establecida en ADR-004. Los schemas son el contrato público del microservicio. El `TokenResponse` de `schemas/auth.py` define el contrato de la respuesta de autenticación establecida en ADR-001.

La configuración `from_attributes = True` en los schemas Response crea el puente entre la capa `models/` (SQLAlchemy ORM) y la capa `schemas/` (contratos Pydantic), completando el flujo de datos de la arquitectura en capas.

**Véase también:** ADR-004 — Arquitectura en 4 Capas, que establece `schemas/` como la capa de contrato del servicio.
