#!/usr/bin/env python3
"""
Script rápido para crear el primer administrador del sistema.
Ideal para la configuración inicial.
"""

import sys
import os

# Agregar el directorio padre al path para importar módulos
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Agregar el directorio utils para importar create_admin
utils_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, utils_dir)

from create_admin import create_admin_user, list_existing_admins

def create_first_admin():
    """Crea el primer administrador del sistema con datos predefinidos"""
    
    print("🚀 CONFIGURACIÓN INICIAL - PRIMER ADMINISTRADOR")
    print("=" * 55)
    
    # Verificar si ya existen administradores
    print("🔍 Verificando administradores existentes...")
    
    from database import get_db, init_db
    from models import User
    
    init_db()
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        existing_admins = db.query(User).filter(User.role == "admin").count()
        
        if existing_admins > 0:
            print(f"⚠️  Ya existen {existing_admins} administrador(es) en el sistema.")
            print("📋 Administradores actuales:")
            list_existing_admins()
            
            choice = input("\n¿Crear otro administrador? (s/N): ").strip().lower()
            if choice not in ['s', 'si', 'sí', 'y', 'yes']:
                print("❌ Operación cancelada.")
                return False
    
    except Exception as e:
        print(f"❌ Error verificando administradores: {e}")
        return False
    
    finally:
        db.close()
    
    # Datos del primer administrador
    print("\n📝 Creando administrador principal...")
    
    admin_data = {
        "email": "admin@booking.com",
        "password": "string",  # Cambiar en producción
        "nombre_completo": "Administrador",
        "apellidos": "Principal",
        "direccion": "Oficina Principal",
        "edad": 30,
        "telefono": "1234567890"
    }
    
    print(f"📧 Email: {admin_data['email']}")
    print(f"🔒 Contraseña: {admin_data['password']}")
    print(f"👤 Nombre: {admin_data['nombre_completo']} {admin_data['apellidos']}")
    
    print("\n⚠️  IMPORTANTE: Cambia la contraseña después del primer login!")
    
    confirm = input("\n¿Proceder con la creación? (S/n): ").strip().lower()
    if confirm in ['n', 'no']:
        print("❌ Creación cancelada.")
        return False
    
    # Crear el administrador
    result = create_admin_user(**admin_data)
    
    if result:
        print("\n🎉 ¡PRIMER ADMINISTRADOR CREADO EXITOSAMENTE!")
        print("=" * 50)
        print("📋 CREDENCIALES DE ACCESO:")
        print(f"   Email: {admin_data['email']}")
        print(f"   Contraseña: {admin_data['password']}")
        return True
    
    else:
        print("💥 Error al crear el primer administrador.")
        return False

def main():
    try:
        success = create_first_admin()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()