# Modelos de Pydantic para la aplicación de reservas de habitaciones
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Modelo simple de Usuario (sin SQLAlchemy)
class User(BaseModel):
    id: int
    email: str
    nombre_completo: str
    apellidos: str
    direccion: str
    edad: int
    telefono: str
    role: str = "clientes"
    is_authorized: bool = False
    created_at: Optional[datetime] = None

# Modelos de Pydantic para Booking
class Booking(BaseModel):
    Id: int = Field(..., description="Primary Key")
    Room_Id: int = Field(..., description="Foreign Key to Room")
    User_Id: int = Field(..., description="Foreign Key to User")
    Estado: str = Field(default="Pendiente", description="Estado de la reserva")
    BookingIn: Optional[datetime] = Field(None, description="Fecha y hora de entrada")
    BookingOn: Optional[datetime] = Field(None, description="Fecha y hora de salida")

# Modelos de Pydantic para Notification
class Notification(BaseModel):
    Id: int = Field(..., description="Primary Key")
    Estado: bool = Field(default=False, description="Estado de la notificación")
    User_id: int = Field(..., description="Foreign Key to User")
    Mensaje: str = Field(..., description="Contenido del mensaje de la notificación")
