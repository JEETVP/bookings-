"""
Utilidades de autenticación simplificadas para evitar problemas con FastAPI OpenAPI
"""
import os
import re
from datetime import timedelta, datetime, timezone
from typing import Optional, Dict, Any

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

# Configuración JWT
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super-secret')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRES', 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRES_DAYS', 7))

# Configuración de seguridad
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Funciones auxiliares sin dependencias complejas
def verify_access_token(token: str):
    """Verifica y decodifica un access token"""
    payload = decode_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    return int(user_id)

def verify_refresh_token(token: str):
    """Verifica y decodifica un refresh token"""
    payload = decode_token(token)
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere refresh token"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    return int(user_id)

def get_user_by_id(user_id: int):
    """Obtiene un usuario por ID desde la base de datos"""
    from database import get_db
    from models import User
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        return user
    finally:
        db.close()

# Dependencias simplificadas
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependencia para obtener el usuario actual"""
    user_id = verify_access_token(credentials.credentials)
    return get_user_by_id(user_id)

def get_refresh_token_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependencia para obtener usuario desde refresh token"""
    user_id = verify_refresh_token(credentials.credentials)
    return get_user_by_id(user_id)

def get_admin_user(current_user = Depends(get_current_user)):
    """Dependencia para verificar permisos de administrador"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user

# Validaciones y utilidades
def _normalize_email(email: str) -> str:
    from email_validator import validate_email, EmailNotValidError
    try:
        valid = validate_email(email, check_deliverability=False)
        return valid.normalized
    except EmailNotValidError as e:
        raise ValueError(str(e))

def validate_phone(phone: str) -> bool:
    """Valida formato de teléfono (10-15 dígitos, puede tener +)"""
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None