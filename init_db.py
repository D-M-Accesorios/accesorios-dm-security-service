# init_db.py
from app.database import SessionLocal
from app.models.rol import Rol
from app.models.empleado import Empleado
from app.utils.security import get_password_hash

def init_database():
    db = SessionLocal()
    try:
        # Verificar rol ADMIN
        rol = db.query(Rol).filter(Rol.nombre == 'ADMIN').first()
        if not rol:
            rol = Rol(nombre='ADMIN', descripcion='Administrador del sistema')
            db.add(rol)
            db.commit()
            print('✅ Rol ADMIN creado')
        else:
            print('⚠️ Rol ADMIN ya existe (ID: {})'.format(rol.id_rol))
        
        # Verificar usuario admin
        admin_user = db.query(Empleado).filter(Empleado.correo == 'admin@test.com').first()
        if not admin_user:
            rol_admin = db.query(Rol).filter(Rol.nombre == 'ADMIN').first()
            admin_user = Empleado(
                nombre='Administrador Test',
                correo='admin@test.com',
                password=get_password_hash('admin123'),
                estado=True,
                id_rol=rol_admin.id_rol
            )
            db.add(admin_user)
            db.commit()
            print('✅ Usuario admin creado (admin@test.com / admin123)')
        else:
            print('⚠️ Usuario admin ya existe')
            
        print('\n✅ Inicialización completada')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    init_database()