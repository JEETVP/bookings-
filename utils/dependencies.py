"""
Dependencias comunes para los routers de FastAPI
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.models import User, TokenData
from utils.security import decode_token

# Esquema de seguridad Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Obtener el usuario actual desde el token JWT
    
    Args:
        credentials: Credenciales del token Bearer
        
    Returns:
        User: Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar el token
        payload = decode_token(credentials.credentials)
        
        if payload is None:
            raise credentials_exception
        
        email: Optional[str] = payload.get("sub")
        user_id: Optional[str] = payload.get("user_id")
        
        if email is None:
            raise credentials_exception
        
        token_data = TokenData(email=email, user_id=user_id)
        
    except Exception:
        raise credentials_exception
    
    # Buscar usuario en la base de datos
    user = await User.find_one(User.email == token_data.email)
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Obtener el usuario actual y verificar que esté autorizado
    
    Args:
        current_user: Usuario actual
        
    Returns:
        User: Usuario autorizado
        
    Raises:
        HTTPException: Si el usuario no está autorizado
    """
    if not current_user.is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario no autorizado"
        )
    
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Verificar que el usuario actual sea administrador
    
    Args:
        current_user: Usuario actual
        
    Returns:
        User: Usuario administrador
        
    Raises:
        HTTPException: Si el usuario no es administrador
    """
    if current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    
    return current_user
