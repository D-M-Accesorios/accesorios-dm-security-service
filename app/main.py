from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth_router, empleados_router, clientes_router, roles_router
from app.config import settings

app = FastAPI(
    title="Security Service - Accesorios DM",
    description="Microservicio de autenticación y usuarios",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(empleados_router, prefix="/api/v1")
app.include_router(clientes_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Security Service - Accesorios DM"}

@app.get("/api/v1/health")
def health():
    return {"status": "UP", "service": "security-service", "version": "1.0.0"}