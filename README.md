# Security Service - Accesorios DM

Microservicio de autenticación y gestión de usuarios para la plataforma de comercio electrónico Accesorios DM.

## Requisitos Previos

- Docker Desktop
- Docker Compose
- Python 3.11+ (para ejecución local)
- Base de datos PostgreSQL (accesorios-dm-database)

## Estructura del Proyecto
```
accesorios-dm-security-service/
├── app/
│ ├── init.py
│ ├── main.py # FastAPI app
│ ├── config.py # Configuración
│ ├── database.py # Conexión a BD
│ ├── models/
│ │ ├── rol.py # Modelo Rol
│ │ ├── empleado.py # Modelo Empleado
│ │ └── cliente.py # Modelo Cliente
│ ├── schemas/
│ │ ├── auth.py # Schemas de autenticación
│ │ ├── empleado.py # Schemas de empleados
│ │ ├── cliente.py # Schemas de clientes
│ │ └── rol.py # Schemas de roles
│ ├── routers/
│ │ ├── auth.py # Endpoints de autenticación
│ │ ├── empleados.py # Endpoints de empleados
│ │ ├── clientes.py # Endpoints de clientes
│ │ └── roles.py # Endpoints de roles
│ └── utils/
│ ├── security.py # JWT, hashing
│ └── dependencies.py # Dependencias de autenticación
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Ambientes y Puertos

| Ambiente | Puerto | BD (localhost) | BD (red Docker) |
|----------|--------|----------------|-----------------|
| develop | 8890 | 5434 | 5432 |
| qa | 8889 | 5433 | 5432 |
| main | 8888 | 5432 | 5432 |

## Dependencia: Base de Datos

Este microservicio requiere la base de datos `accesorios-dm-database`. Debes tenerla clonada y corriendo.

### Clonar la base de datos

```bash
git clone https://github.com/SergioLosadaDev/accesorios-dm-database.git
cd accesorios-dm-database
```

## Levantar la base de datos según ambiente

### Develop:

```bash
git checkout develop
docker-compose -f docker-compose.yml up -d
```

### QA:

```bash
git checkout qa
docker-compose -f docker-compose.yml up -d
```
## Configuración del Microservicio

### Variables de entorno

|Variable	|Valor	|Descripción|
|-----------|-------|-----------|
|DATABASE_URL	|postgresql://admin:admin123@host:port/db	|Conexión a BD|
|SECRET_KEY	|tu-secret-key	|Clave para JWT|
|ALGORITHM	|HS256	|Algoritmo JWT|
|ACCESS_TOKEN_EXPIRE_MINUTES	|30	|Expiración del token|
|PORT	|8890/8889/8888	|Puerto del servicio|

### Archivo .env (crear desde .env.example)

```bash
cp .env.example .env
# Editar según el ambiente
```

## Cómo Levantar el Microservicio

### Opción 1: Con Docker (Recomendado)

```bash
# Levantar el contenedor
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

### Opción 2: Ejecución local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python -m uvicorn app.main:app --reload --port 8890
```

## Endpoints Disponibles

### Autenticación

|Método	|Endpoint	|Descripción|
|-------|-----------|-----------|
|POST	|/api/v1/auth/login	|Login de usuario (devuelve JWT)|
|GET	|/api/v1/auth/me	|Obtener perfil actual|

### Empleados (requiere ADMIN)

|Método	|Endpoint	|Descripción|
|-------|-----------|-----------|
|GET	|/api/v1/empleados/	|Listar empleados|
|GET	|/api/v1/empleados/{id}	|Obtener empleado por ID|
|POST	|/api/v1/empleados/	|Crear empleado|
|PUT	|/api/v1/empleados/{id}	|Actualizar empleado|
|DELETE	|/api/v1/empleados/{id}	|Eliminar empleado|
|PATCH	|/api/v1/empleados/{id}/toggle-estado	|Activar/Desactivar|

### Clientes (requiere ADMIN o VENDEDOR)

|Método	|Endpoint	|Descripción|
|-------|-----------|-----------|
|GET	|/api/v1/clientes/	|Listar clientes|
|GET	|/api/v1/clientes/{id}	|Obtener cliente por ID|
|POST	|/api/v1/clientes/	|Crear cliente|
|PUT	|/api/v1/clientes/{id}	|Actualizar cliente|
|DELETE	|/api/v1/clientes/{id}	|Eliminar cliente|

### Roles (requiere ADMIN)

|Método	|Endpoint	|Descripción|
|-------|-----------|-----------|
|GET	|/api/v1/roles/	|Listar roles|
|GET	|/api/v1/roles/{id}	|Obtener rol por ID|
|POST	|/api/v1/roles/	|Crear rol|
|PUT	|/api/v1/roles/{id}	|Actualizar rol|
|DELETE	|/api/v1/roles/{id}	|Eliminar rol|
|PATCH	|/api/v1/roles/{empleado_id}/rol/{rol_id}	|Asignar rol a empleado|

### Health Check

|Método	|Endpoint	|Descripción|
|-------|-----------|-----------|
|GET	|/api/v1/health	|Health check del servicio|

## Ejemplos de uso

### Login

```bash
curl -X POST http://localhost:8890/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"correo":"admin@accesoriosdm.com","password":"admin123"}'
```

### Listar empleados

```bash
curl -X GET http://localhost:8890/api/v1/empleados/ \
  -H "Authorization: Bearer <token>"
```

### Crear cliente

```bash
curl -X POST http://localhost:8890/api/v1/clientes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"nombre":"Juan Perez","correo":"juan@test.com","telefono":"3001234567"}'
```

### Crear rol

```bash
curl -X POST http://localhost:8890/api/v1/roles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"nombre":"SUPERVISOR","descripcion":"Supervisor de ventas"}'
```

## Comandos Útiles

```bash
# Ver logs del contenedor
docker-compose logs -f

# Reconstruir imagen
docker-compose build --no-cache

# Detener y eliminar contenedor
docker-compose down

# Conectar a la base de datos (desde el host)
docker exec -it accesorios-dm-postgres-dev psql -U admin -d accesorios_dm_db
```

## Solución de Problemas
### Error: Connection refused

**Causa:** Base de datos no corriendo.

**Solución:**

```bash
cd ../accesorios-dm-database
docker-compose -f docker-compose.yml up -d
```

### Error: Credenciales incorrectas

**Causa:** Contraseña en texto plano en lugar de hash.

**Solución:**

```bash
docker exec -it accesorios-dm-postgres-dev psql -U admin -d accesorios_dm_db -c "UPDATE security.empleado SET password = 'UC5g9HK3oclQfjko7ZDoYYY79CDV2KqxB5H7hnbOOAU=' WHERE correo = 'admin@accesoriosdm.com';"
```

### Error: Not authenticated

**Causa:** Token inválido o expirado.

**Solución:** Obtener nuevo token con login.

### Error: Se requiere rol: ADMIN

**Causa:** El usuario actual no tiene permisos de administrador.

**Solución:** Usar un usuario con rol ADMIN o asignar el rol ADMIN a un usuario existente.

## Tecnologías Utilizadas

|Tecnología	|Versión	|Propósito|
|-----------|-----------|---------|
|Python	|3.11	|Lenguaje principal|
|FastAPI	|0.115.0	|Framework web|
|SQLAlchemy	|2.0.35	|ORM|
|PostgreSQL	|16	|Base de datos|
|JWT	|-	|Autenticación|
|Docker	|-	|Contenerización|

## Flujo de Trabajo con Git

```bash
# Crear rama para nueva funcionalidad
git checkout develop
git pull origin develop
git checkout -b HU-DEV-DYC-XX-ss-nombre

# Hacer cambios...
git add .
git commit -m "feat: HU-DEV-DYC-XX-ss-nombre descripcion"
git push origin HU-DEV-DYC-XX-ss-nombre

# Crear Pull Request a develop
```

## HUs Completadas

|HU	|Descripción|
|---|-----------|
|HU-01	|Setup + Autenticación|
|HU-02	|CRUD Empleados|
|HU-03	|CRUD Clientes|
|HU-04	|Gestión de Roles|
|HU-05	|Documentación + Docker|
|HU-RLS-01	|Release para Main|

## Endpoints Disponibles

|Endpoint	|Método	|Rol requerido|
|-----------|-------|-------------|
|/api/v1/health	|GET	|Público|
|/api/v1/auth/login	|POST	|Público|
|/api/v1/auth/me	|GET	|Autenticado|
|/api/v1/empleados/	|GET/POST/PUT/DELETE	|ADMIN|
|/api/v1/clientes/	|GET/POST/PUT/DELETE	|ADMIN/VENDEDOR|
|/api/v1/roles/	|GET/POST/PUT/DELETE	|ADMIN|
|/api/v1/roles/{id}/rol/{id}	|PATCH	|ADMIN|

## Licencia

Proyecto interno de Accesorios DM.

## Contacto

- Repositorio: https://github.com/SergioLosadaDev/accesorios-dm-security-service

