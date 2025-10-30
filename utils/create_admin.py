#!/usr/bin/env python3
"""
Script para crear usuarios administradores directamente en la base de datos.
Útil para crear el primer admin o agregar admins adicionales.

Uso:
    python create_admin.py
    python create_admin.py --email admin@example.com --password mypass123
"""

import argparse
import sys
import os
from getpass import getpass

# Agregar el directorio padre al path para importar módulos
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from database import get_db, init_db
from models import User

# Importar funciones de validación directamente
import re
from email_validator import validate_email, EmailNotValidError

def _normalize_email(email: str) -> str:
    """Normalizar email"""
    try:
        valid = validate_email(email, check_deliverability=False)
        return valid.normalized
    except EmailNotValidError as e:
        raise ValueError(str(e))

def validate_phone(phone: str) -> bool:
    """Validar formato de teléfono (10-15 dígitos, puede tener +)"""
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None

def create_admin_user(email, password, nombre_completo, apellidos, direccion, edad, telefono):
    """
    Crea un usuario administrador directamente en la base de datos.
    
    Args:
        email: Email del administrador
        password: Contraseña del administrador
        nombre_completo: Nombre completo
        apellidos: Apellidos
        direccion: Dirección
        edad: Edad
        telefono: Teléfono
        
    Returns:
        dict: Información del usuario creado o None si hubo error
    """
    
    # Inicializar la base de datos
    init_db()
    
    # Obtener sesión de base de datos
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Validar email
        try:
            normalized_email = _normalize_email(email)
        except ValueError as e:
            print(f"❌ Email inválido: {e}")
            return None
        
        # Validar contraseña
        if len(password) < 6:
            print("❌ La contraseña debe tener al menos 6 caracteres.")
            return None
        
        # Validar edad
        if edad < 18 or edad > 120:
            print("❌ La edad debe estar entre 18 y 120 años.")
            return None
        
        # Validar teléfono
        if not validate_phone(telefono):
            print("❌ Formato de teléfono inválido (debe tener 10-15 dígitos).")
            return None
        
        # Verificar si el email ya existe
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            print(f"❌ El email {normalized_email} ya está registrado.")
            print(f"   Usuario existente: {existing_user.nombre_completo} {existing_user.apellidos} (Rol: {existing_user.role})")
            return None
        
        # Crear el usuario administrador
        admin_user = User(
            email=normalized_email,
            nombre_completo=nombre_completo.strip(),
            apellidos=apellidos.strip(),
            direccion=direccion.strip(),
            edad=edad,
            telefono=telefono.strip(),
            role="admin",
            is_authorized=True,  # Los admins se autorizan automáticamente
        )
        
        # Establecer la contraseña
        admin_user.set_password(password)
        
        # Guardar en la base de datos
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        user_info = {
            "id": admin_user.id,
            "email": admin_user.email,
            "nombre_completo": admin_user.nombre_completo,
            "apellidos": admin_user.apellidos,
            "role": admin_user.role,
            "is_authorized": admin_user.is_authorized,
            "created_at": admin_user.created_at.isoformat()
        }
        
        print("✅ Administrador creado exitosamente!")
        print(f"   ID: {user_info['id']}")
        print(f"   Email: {user_info['email']}")
        print(f"   Nombre: {user_info['nombre_completo']} {user_info['apellidos']}")
        print(f"   Rol: {user_info['role']}")
        print(f"   Autorizado: {user_info['is_authorized']}")
        print(f"   Creado: {user_info['created_at']}")
        
        return user_info
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear administrador: {e}")
        return None
    
    finally:
        db.close()

def interactive_mode():
    """Modo interactivo para crear un administrador"""
    
    print("🛡️  CREADOR DE ADMINISTRADORES")
    print("=" * 50)
    print("Creando un nuevo usuario administrador...")
    print()
    
    # Recopilar información del usuario
    email = input("📧 Email: ").strip()
    
    # Solicitar contraseña de forma segura
    password = getpass("🔒 Contraseña (mín 6 caracteres): ")
    confirm_password = getpass("🔒 Confirmar contraseña: ")
    
    if password != confirm_password:
        print("❌ Las contraseñas no coinciden.")
        return False
    
    nombre_completo = input("👤 Nombre completo: ").strip()
    apellidos = input("👥 Apellidos: ").strip()
    direccion = input("🏠 Dirección: ").strip()
    
    try:
        edad = int(input("🎂 Edad: ").strip())
    except ValueError:
        print("❌ La edad debe ser un número.")
        return False
    
    telefono = input("📱 Teléfono: ").strip()
    
    print()
    print("📋 RESUMEN:")
    print(f"   Email: {email}")
    print(f"   Nombre: {nombre_completo} {apellidos}")
    print(f"   Edad: {edad}")
    print(f"   Teléfono: {telefono}")
    print(f"   Dirección: {direccion}")
    print(f"   Rol: admin")
    print()
    
    confirm = input("¿Crear este administrador? (s/N): ").strip().lower()
    if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Creación cancelada.")
        return False
    
    # Crear el administrador
    result = create_admin_user(
        email=email,
        password=password,
        nombre_completo=nombre_completo,
        apellidos=apellidos,
        direccion=direccion,
        edad=edad,
        telefono=telefono
    )
    
    return result is not None

def list_existing_admins():
    """Lista los administradores existentes en la base de datos"""
    
    # Inicializar la base de datos
    init_db()
    
    # Obtener sesión de base de datos
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Buscar todos los administradores
        admins = db.query(User).filter(User.role == "admin").all()
        
        if not admins:
            print("📋 No hay administradores en la base de datos.")
            return
        
        print("📋 ADMINISTRADORES EXISTENTES:")
        print("=" * 50)
        
        for i, admin in enumerate(admins, 1):
            status = "✅ Autorizado" if admin.is_authorized else "❌ No autorizado"
            print(f"{i}. ID: {admin.id}")
            print(f"   Email: {admin.email}")
            print(f"   Nombre: {admin.nombre_completo} {admin.apellidos}")
            print(f"   Estado: {status}")
            print(f"   Creado: {admin.created_at}")
            print()
    
    except Exception as e:
        print(f"❌ Error al listar administradores: {e}")
    
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Crear usuarios administradores en la base de datos")
    parser.add_argument("--email", help="Email del administrador")
    parser.add_argument("--password", help="Contraseña del administrador")
    parser.add_argument("--nombre", help="Nombre completo del administrador")
    parser.add_argument("--apellidos", help="Apellidos del administrador")
    parser.add_argument("--direccion", help="Dirección del administrador")
    parser.add_argument("--edad", type=int, help="Edad del administrador")
    parser.add_argument("--telefono", help="Teléfono del administrador")
    parser.add_argument("--list", action="store_true", help="Listar administradores existentes")
    
    args = parser.parse_args()
    
    # Si se solicita listar administradores
    if args.list:
        list_existing_admins()
        return
    
    # Si se proporcionan todos los argumentos necesarios
    if all([args.email, args.password, args.nombre, args.apellidos, 
            args.direccion, args.edad, args.telefono]):
        
        print("🚀 Creando administrador con argumentos proporcionados...")
        result = create_admin_user(
            email=args.email,
            password=args.password,
            nombre_completo=args.nombre,
            apellidos=args.apellidos,
            direccion=args.direccion,
            edad=args.edad,
            telefono=args.telefono
        )
        
        if result:
            print("\n🎉 ¡Administrador creado exitosamente!")
        else:
            print("\n💥 Error al crear administrador.")
            sys.exit(1)
    
    else:
        # Modo interactivo
        success = interactive_mode()
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)