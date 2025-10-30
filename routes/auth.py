from datetime import timedelta, datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Form, status, Depends
from sqlalchemy.orm import Session

from models import User, Token, UserLogin
from utils.auth import (
    create_access_token, create_refresh_token, get_current_user, 
    get_refresh_token_user, _normalize_email, validate_phone,
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
)

# Importar la dependencia de la base de datos
from database import get_db

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post('/register', response_model=Dict[str, Any])
async def register(
    email: str = Form(...),
    password: str = Form(...),
    nombre_completo: str = Form(...),
    apellidos: str = Form(...),
    direccion: str = Form(...),
    edad: int = Form(...),
    telefono: str = Form(...),
    db: Session = Depends(get_db)
):

    
    # Validar datos del formulario
    try:
        normalized_email = _normalize_email(email)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email inválido: {str(e)}"
        )
    
    # Validar contraseña
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 6 caracteres."
        )
    
    # Validar edad
    if edad < 18 or edad > 120:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe ser mayor de edad (18 años o más)."
        )
    
    # Validar teléfono
    if not validate_phone(telefono):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de teléfono inválido (debe tener 10-15 dígitos)."
        )
    
    # Verificar si el email ya existe
    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado."
        )
    
    # Crear usuario con rol automático de cliente
    try:
        user = User(
            email=normalized_email,
            nombre_completo=nombre_completo.strip(),
            apellidos=apellidos.strip(),
            direccion=direccion.strip(),
            edad=edad,
            telefono=telefono.strip(),
            role="clientes",  # Rol automático para todos los nuevos usuarios
            is_authorized=True,  # Los clientes se autorizan automáticamente
        )
        
        # Establecer la contraseña usando el método del modelo
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)

        # Preparar información de respuesta
        user_info = {
            "id": user.id,
            "email": user.email,
            "nombre_completo": user.nombre_completo,
            "apellidos": user.apellidos,
            "role": user.role,
            "is_authorized": user.is_authorized,
            "created_at": user.created_at.isoformat()
        }
        return {
            "message": "Usuario registrado exitosamente como cliente.",
            "user": user_info
        }
    except HTTPException:
        # Re-lanzar HTTPException tal como están
        raise
    except Exception as e:
        # Limpiar usuario si hay error
        try:
            if 'user' in locals() and user.id:
                db.delete(user)
                db.commit()
        except:
            pass
        
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )
@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    try:
        email = _normalize_email(user_credentials.email)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email inválido: {ve}"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas."
        )
    
    try:
        password_valid = user.check_password(user_credentials.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor. Por favor contacta al administrador."
        )
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas."
        )

    # Verificar si el usuario está autorizado
    if not user.is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no autorizado. Contacte al administrador."
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={
            "sub": str(user.id), 
            "email": user.email, 
            "role": user.role
        },
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Obtener información del usuario actual"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "nombre_completo": current_user.nombre_completo,
        "apellidos": current_user.apellidos,
        "direccion": current_user.direccion,
        "edad": current_user.edad,
        "telefono": current_user.telefono,
        "role": current_user.role,
        "is_authorized": current_user.is_authorized,
        "created_at": current_user.created_at.isoformat()
    }

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    current_user: User = Depends(get_refresh_token_user)
):
    """Generar un nuevo access token usando el refresh token"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        data={
            "sub": str(current_user.id), 
            "email": current_user.email, 
            "role": current_user.role
        },
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(current_user.id)},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post('/admin/create-user', response_model=Dict[str, Any])
async def create_user_as_admin(
    email: str = Form(...),
    password: str = Form(...),
    nombre_completo: str = Form(...),
    apellidos: str = Form(...),
    direccion: str = Form(...),
    edad: int = Form(...),
    telefono: str = Form(...),
    role: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint para que los administradores puedan crear usuarios con cualquier rol.
    Solo accesible por usuarios con rol 'admin'.
    """
    
    # Verificar que el usuario actual es administrador
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear usuarios con roles específicos."
        )
    
    # Validar datos del formulario
    try:
        normalized_email = _normalize_email(email)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email inválido: {str(e)}"
        )
    
    # Validar contraseña
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 6 caracteres."
        )
    
    # Validar edad
    if edad < 18 or edad > 120:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe ser mayor de edad (18 años o más)."
        )
    
    # Validar teléfono
    if not validate_phone(telefono):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de teléfono inválido (debe tener 10-15 dígitos)."
        )
    
    # Validar rol
    valid_roles = ['admin', 'clientes']
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido. Roles válidos: {', '.join(valid_roles)}"
        )
    
    # Verificar si el email ya existe
    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado."
        )
    
    # Crear usuario con el rol especificado
    try:
        user = User(
            email=normalized_email,
            nombre_completo=nombre_completo.strip(),
            apellidos=apellidos.strip(),
            direccion=direccion.strip(),
            edad=edad,
            telefono=telefono.strip(),
            role=role,
            is_authorized=True,  # Los usuarios creados por admin se autorizan automáticamente
        )
        
        # Establecer la contraseña usando el método del modelo
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.refresh(user)

        # Preparar información de respuesta
        user_info = {
            "id": user.id,
            "email": user.email,
            "nombre_completo": user.nombre_completo,
            "apellidos": user.apellidos,
            "role": user.role,
            "is_authorized": user.is_authorized,
            "created_at": user.created_at.isoformat()
        }
        return {
            "message": f"Usuario registrado exitosamente con rol '{role}' por el administrador.",
            "user": user_info,
            "created_by": {
                "admin_id": current_user.id,
                "admin_email": current_user.email
            }
        }
    except HTTPException:
        # Re-lanzar HTTPException tal como están
        raise
    except Exception as e:
        # Limpiar usuario si hay error
        try:
            if 'user' in locals() and user.id:
                db.delete(user)
                db.commit()
        except:
            pass
        
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor."
        )