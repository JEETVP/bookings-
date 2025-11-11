# Clases de modelos para la aplicación de reservas de habitaciones
# Modelos con Beanie Document para MongoDB
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from beanie import Document, Indexed, PydanticObjectId
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums para estados
class RoomStatus(str, Enum):
    DISPONIBLE = "Disponible"
    OCUPADA = "Ocupada"
    MANTENIMIENTO = "Mantenimiento"
    RESERVADA = "Reservada"


class BookingStatus(str, Enum):
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    COMPLETADA = "Completada"


class UserRole(str, Enum):
    CLIENTE = "clientes"
    ADMIN = "admin"
    STAFF = "staff"


# Document Models para MongoDB
class User(Document):
    """Modelo de Usuario para MongoDB"""
    email: Indexed(EmailStr, unique=True)  # type: ignore
    password_hash: str = Field(..., description="Hash de la contraseña")
    nombre_completo: str = Field(..., min_length=1, max_length=100, description="Nombre completo del usuario")
    apellidos: str = Field(..., min_length=1, max_length=100, description="Apellidos del usuario")
    direccion: str = Field(..., min_length=1, max_length=255, description="Dirección del usuario")
    edad: int = Field(..., ge=18, le=120, description="Edad del usuario")
    telefono: str = Field(..., min_length=10, max_length=20, description="Teléfono del usuario")
    role: UserRole = Field(default=UserRole.CLIENTE, description="Rol del usuario")
    is_authorized: bool = Field(default=False, description="Usuario autorizado")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(default=None, description="Fecha de última actualización")
    
    class Settings:
        name = "users"  # Nombre de la colección en MongoDB
        indexes = [
            "email",
            "role",
        ]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "usuario@example.com",
                "nombre_completo": "Juan",
                "apellidos": "Pérez García",
                "direccion": "Calle Principal 123",
                "edad": 30,
                "telefono": "+34123456789",
                "role": "clientes"
            }
        }
    )


class Room(Document):
    """Modelo de Habitación para MongoDB"""
    numero: str = Field(..., description="Número de habitación", min_length=1)
    estado: RoomStatus = Field(default=RoomStatus.DISPONIBLE, description="Estado de la habitación")
    capacidad: int = Field(..., ge=1, le=10, description="Capacidad de la habitación")
    caracteristicas: List[str] = Field(default_factory=list, description="Características de la habitación")
    ubicacion: str = Field(..., description="Ubicación de la habitación")
    precio_por_noche: float = Field(..., ge=0, description="Precio por noche")
    imagen_url: Optional[str] = Field(default=None, description="URL de la imagen de la habitación")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(default=None, description="Fecha de última actualización")
    
    class Settings:
        name = "rooms"
        indexes = [
            "numero",
            "estado",
            "precio_por_noche",
        ]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "numero": "101",
                "estado": "Disponible",
                "capacidad": 2,
                "caracteristicas": ["WiFi", "TV", "Aire acondicionado", "Baño privado"],
                "ubicacion": "Piso 1",
                "precio_por_noche": 75.00
            }
        }
    )


class Booking(Document):
    """Modelo de Reserva para MongoDB"""
    room_id: PydanticObjectId = Field(..., description="ID de la habitación")
    user_id: PydanticObjectId = Field(..., description="ID del usuario")
    estado: BookingStatus = Field(default=BookingStatus.PENDIENTE, description="Estado de la reserva")
    booking_in: datetime = Field(..., description="Fecha y hora de entrada")
    booking_out: datetime = Field(..., description="Fecha y hora de salida")
    numero_huespedes: int = Field(default=1, ge=1, description="Número de huéspedes")
    precio_total: float = Field(..., ge=0, description="Precio total de la reserva")
    notas: Optional[str] = Field(default=None, max_length=500, description="Notas adicionales")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(default=None, description="Fecha de última actualización")
    
    class Settings:
        name = "bookings"
        indexes = [
            "room_id",
            "user_id",
            "estado",
            "booking_in",
            "booking_out",
        ]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "room_id": "507f1f77bcf86cd799439011",
                "user_id": "507f1f77bcf86cd799439012",
                "estado": "Pendiente",
                "booking_in": "2025-11-15T14:00:00",
                "booking_out": "2025-11-18T12:00:00",
                "numero_huespedes": 2,
                "precio_total": 225.00,
                "notas": "Llegada tarde"
            }
        }
    )


class Notification(Document):
    """Modelo de Notificación para MongoDB"""
    user_id: PydanticObjectId = Field(..., description="ID del usuario")
    mensaje: str = Field(..., min_length=1, max_length=500, description="Contenido del mensaje")
    titulo: str = Field(..., min_length=1, max_length=100, description="Título de la notificación")
    tipo: str = Field(default="info", description="Tipo de notificación: info, warning, error, success")
    leida: bool = Field(default=False, description="Estado de lectura de la notificación")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    
    class Settings:
        name = "notifications"
        indexes = [
            "user_id",
            "leida",
            "created_at",
        ]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "507f1f77bcf86cd799439012",
                "titulo": "Reserva confirmada",
                "mensaje": "Tu reserva para la habitación 101 ha sido confirmada",
                "tipo": "success",
                "leida": False
            }
        }
    )


# Schemas Pydantic para requests/responses (sin ID de MongoDB)
class UserCreate(BaseModel):
    """Schema para crear un usuario"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Contraseña (mínimo 8 caracteres)")
    nombre_completo: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=100)
    direccion: str = Field(..., min_length=1, max_length=255)
    edad: int = Field(..., ge=18, le=120)
    telefono: str = Field(..., min_length=10, max_length=20)


class UserResponse(BaseModel):
    """Schema para respuesta de usuario (sin password_hash)"""
    id: str
    email: EmailStr
    nombre_completo: str
    apellidos: str
    direccion: str
    edad: int
    telefono: str
    role: str
    is_authorized: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema para login de usuario"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema para token JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema para datos dentro del token"""
    email: Optional[str] = None
    user_id: Optional[str] = None