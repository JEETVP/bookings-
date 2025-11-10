# Clases de modelos para la aplicación de reservas de habitaciones
# Modelos limpios en Pydantic - MongoDB será implementado próximamente
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Modelos base con Pydantic (temporalmente sin BD)

#User
class User(BaseModel):
    email: str = Field(..., description="Email del usuario")
    password_hash: str = Field(..., description="Hash de la contraseña")
    nombre_completo: str = Field(..., description="Nombre completo del usuario")
    apellidos: str = Field(..., description="Apellidos del usuario")
    direccion: str = Field(..., description="Dirección del usuario")
    edad: int = Field(..., ge=1, description="Edad del usuario")
    telefono: str = Field(..., description="Teléfono del usuario")
    role: str = Field(default="clientes", description="Rol del usuario")
    is_authorized: bool = Field(default=False, description="Usuario autorizado")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="Fecha de creación")

#Booking
class Booking(BaseModel):
    room_id: str = Field(..., description="ID de la habitación")
    user_id: str = Field(..., description="ID del usuario")
    estado: str = Field(default="Pendiente", description="Estado de la reserva")
    booking_in: Optional[datetime] = Field(None, description="Fecha y hora de entrada")
    booking_out: Optional[datetime] = Field(None, description="Fecha y hora de salida")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="Fecha de creación")

#Room
class Room(BaseModel):
    estado: str = Field(default="Disponible", description="Estado de la habitación")
    capacidad: int = Field(..., ge=1, description="Capacidad de la habitación")
    caracteristicas: List[str] = Field(..., description="Características de la habitación")
    ubicacion: str = Field(..., description="Ubicación de la habitación")
    precio_por_noche: float = Field(..., ge=0, description="Precio por noche")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="Fecha de creación")

#Notification
class Notification(BaseModel):
    estado: bool = Field(default=False, description="Estado de la notificación (entregada o no)")
    user_id: str = Field(..., description="ID del usuario")
    mensaje: str = Field(..., description="Contenido del mensaje de la notificación")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="Fecha de creación")

# Modelos de Pydantic para autenticación
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class UserLogin(BaseModel):
    email: str
    password: str