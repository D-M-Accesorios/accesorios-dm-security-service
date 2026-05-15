# ADR-003 — Segregación de Datos por PostgreSQL Schemas

## Metadatos

| Campo       | Valor                                              |
|-------------|----------------------------------------------------|
| ID          | ADR-003                                            |
| Título      | Segregación de Datos por PostgreSQL Schemas        |
| Categoría   | Structural                                         |
| Estado      | Accepted                                           |
| Fecha       | 2024 — HU-01 / HU-03                              |
| Autores     | Equipo de desarrollo Accesorios DM                 |
| Relacionado | ADR-004                                            |

---

## Justificación de Categoría

**Structural** — Define cómo se organiza y estructura el almacenamiento de datos a nivel de base de datos. Afecta la disposición física y lógica de las tablas, el control de acceso granular sobre conjuntos de datos, y la preparación para una eventual extracción de dominios a servicios independientes. No define comportamiento en tiempo de ejecución ni el diseño interno de componentes de código, sino la arquitectura de datos del sistema.

---

## Contexto

El microservicio gestiona dos dominios de negocio conceptualmente distintos dentro de una misma instancia de base de datos PostgreSQL:

1. **Dominio de Seguridad / Identidad:** Empleados internos del sistema que se autentican y tienen roles asignados. Tablas: `rol`, `empleado`.
2. **Dominio de Clientes:** Consumidores finales de la plataforma e-commerce. Tabla: `cliente`. Los clientes no tienen credenciales de autenticación en este servicio.

Ambos dominios comparten la misma instancia PostgreSQL gestionada por el repositorio `accesorios-dm-database`. Sin una estrategia de organización, todas las tablas coexistirían en el schema `public` por defecto de PostgreSQL, sin separación lógica ni posibilidad de control de acceso granular.

---

## Decisión

Se adoptó la estrategia de **segregar las tablas en schemas de PostgreSQL separados** según su dominio funcional:

- Schema `security`: contiene las tablas `rol` y `empleado`.
- Schema `clientes`: contiene la tabla `cliente`.

Esta separación se declara explícitamente en cada modelo SQLAlchemy:

```python
# models/rol.py
class Rol(Base):
    __tablename__ = "rol"
    __table_args__ = {"schema": "security"}

# models/empleado.py
class Empleado(Base):
    __tablename__ = "empleado"
    __table_args__ = {"schema": "security"}

# models/cliente.py
class Cliente(Base):
    __tablename__ = "cliente"
    __table_args__ = {"schema": "clientes"}
```

SQLAlchemy traduce esta configuración a referencias completamente calificadas en todas las queries generadas: `security.rol`, `security.empleado`, `clientes.cliente`.

---

## Consecuencias

El diseño de la base de datos refleja explícitamente los límites de dominio del negocio. Las queries que impliquen datos de ambos dominios requieren referencias cross-schema. El servicio asume que los schemas existen previamente en la base de datos; SQLAlchemy no los crea automáticamente al arrancar el servicio. Los schemas deben estar creados en la base de datos gestionada por `accesorios-dm-database` antes de levantar el microservicio.

---

## Ventajas

- **Separación lógica de dominio:** El schema actúa como namespace explícito, haciendo visible la pertenencia de cada tabla tanto en el código como en herramientas de administración (pgAdmin, psql).
- **Control de acceso granular a nivel de schema:** PostgreSQL permite asignar permisos `GRANT` a nivel de schema, habilitando el principio de mínimo privilegio (ej: usuario de BD con acceso solo a `clientes.*`).
- **Preparación para extracción de microservicios:** Si el dominio de clientes se extrae a un microservicio independiente, la migración implicaría mover el schema `clientes` a otra instancia, no restructurar tablas.
- **Alineación con Domain-Driven Design:** Los schemas funcionan como representación de los Bounded Contexts del dominio.
- **Prevención de colisiones de nombres:** Tablas con el mismo nombre en dominios distintos coexistirían sin conflicto bajo schemas separados.

---

## Desventajas

- **Configuración explícita obligatoria en cada modelo:** Un olvido de `__table_args__` resulta en tablas creadas en el schema `public` por defecto, generando inconsistencias silenciosas.
- **Sin migrations automáticas:** El proyecto no utiliza Alembic. Los schemas `security` y `clientes` deben existir en PostgreSQL antes del arranque del servicio.
- **Acoplamiento a PostgreSQL:** Los schemas de PostgreSQL no tienen equivalente directo en MySQL ni SQLite, reduciendo la portabilidad a otros motores.
- **Complejidad en queries cross-schema:** Consultas que cruzan dominios requieren referencias explícitas a ambos schemas.

---

## Alternativas Consideradas

| Alternativa                              | Trade-off                                                                                                               |
|------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| **Schema `public` único con prefijos**   | Más simple de configurar; sin separación real de dominio; no permite control de permisos granular.                      |
| **Base de datos separada por dominio**   | Separación total; requiere múltiples cadenas de conexión; elimina la posibilidad de joins cross-domain.                 |
| **Sin schemas (PostgreSQL `public`)**    | Configuración mínima; produce base de datos sin organización a medida que crece el número de tablas.                    |

---

## Relación con la Arquitectura Actual

Esta decisión impacta directamente todos los modelos SQLAlchemy del servicio (`models/`). La separación de schemas en la base de datos es un espejo de la separación de paquetes de modelos en el código, complementando la arquitectura en capas definida en ADR-004.

La consulta de autorización en ADR-002 accede a `security.rol`, siendo dependiente de esta decisión de organización.

**Véase también:** ADR-004 — Arquitectura en 4 Capas, cuya separación de paquetes refleja en el código la misma separación de dominios que este ADR establece en la base de datos.
