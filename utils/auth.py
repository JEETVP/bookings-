"""
Utilidades de autenticación (FastAPI + JWT) versión MongoDB
- JWT 'sub' = str(ObjectId)
- Sin SQLAlchemy; usa utils.mongodb.get_users_collection
- Tiempos en UTC tz-aware
"""
import os
import re
from datetime import timedelta, datetime, timezone
from typing import Optional, Dict, Any

from bson import ObjectId
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from utils.mongodb import get_users_collection

# ===================== Configuración JWT =====================
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRES_DAYS", 7))

# ===================== Seguridad (Bearer) ====================
security = HTTPBearer()

# ===================== Helpers JWT ===========================
def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = _utc_now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = _utc_now() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def _ensure_objectid_str(user_id: Any) -> str:
    """
    Valida que user_id sea un ObjectId válido (string o ObjectId) y devuelve str(ObjectId).
    """
    if isinstance(user_id, ObjectId):
        return str(user_id)
    if isinstance(user_id, str) and ObjectId.is_valid(user_id):
        return user_id
    # Si llegaran a usar enteros como IDs, aquí podrías mapearlos;
    # por ahora solo aceptamos ObjectId.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido (sub no es ObjectId válido)",
    )

# ===================== Verificadores =========================
def verify_access_token(token: str) -> str:
    """
    Verifica y decodifica un access token. Devuelve user_id (str(ObjectId)).
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tipo de token inválido")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return _ensure_objectid_str(user_id)

def verify_refresh_token(token: str) -> str:
    """
    Verifica y decodifica un refresh token. Devuelve user_id (str(ObjectId)).
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere refresh token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    return _ensure_objectid_str(user_id)

# ===================== Acceso a usuarios (Mongo) =============
def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """
    Obtiene un usuario por _id desde MongoDB.
    Retorna el documento completo (dict). Debe incluir 'role'.
    """
    col = get_users_collection()
    doc = col.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return doc

# ===================== Dependencias FastAPI ==================
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependencia para obtener el usuario actual desde un Access Token Bearer.
    """
    user_id = verify_access_token(credentials.credentials)
    return get_user_by_id(user_id)

def get_refresh_token_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependencia para obtener el usuario desde un Refresh Token Bearer.
    (Útil si haces rotación vía endpoint protegido)
    """
    user_id = verify_refresh_token(credentials.credentials)
    return get_user_by_id(user_id)

def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Verifica permisos de administrador. Asume que el doc de usuario tiene 'role'.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return current_user

# ===================== Utilidades varias =====================
def _normalize_email(email: str) -> str:
    from email_validator import validate_email, EmailNotValidError
    try:
        valid = validate_email(email, check_deliverability=False)
        return valid.normalized
    except EmailNotValidError as e:
        raise ValueError(str(e))

def validate_phone(phone: str) -> bool:
    """Valida formato de teléfono (10-15 dígitos, puede tener +)"""
    pattern = r"^\+?[0-9]{10,15}$"
    return re.match(pattern, phone) is not None
