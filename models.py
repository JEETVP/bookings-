# Clases de modelos para la aplicación de reservas de habitaciones
# Clases base: User, Booking, Room, Notification 
from pydantic import BaseModel, Field
from typing import  Optional, List
from datetime import datetime

#User
class User(BaseModel):
    Id: int = Field(..., description="Primary Key")
    Nombre: str = Field(..., description="Nombre del usuario")
    Correo: str = Field(..., description="Correo electrónico del usuario")
    Password: str = Field(..., description="Contraseña del usuario")

#Booking
class Booking(BaseModel):
    Id: int = Field(..., description="Primary Key")
    Room_Id: int = Field(..., description="Foreign Key to Room")
    User_Id: int = Field(..., description="Foreign Key to User")
    Estado: str = Field(..., description="Estado de la reserva", default="Pendiente")
    BookingIn: Optional[datetime] = Field(None, description="Fecha y hora de entrada")
    BookingOn: Optional[datetime] = Field(None, description="Fecha y hora de salida")

#Room
class Room(BaseModel):
    Id: int = Field(..., description="Primary Key")
    Estado: str = Field(..., description="Estado de la habitación", default="Disponible")
    Capacidad: int = Field(..., description="Capacidad de la habitación",minimum=1)
    Características: List = Field(..., description="Características de la habitación")
    Ubicación: str = Field(..., description="Ubicación de la habitación")

#Notification
class Notification(BaseModel):
    Id: int = Field(..., description="Primary Key")
    Estado: bool = Field(..., description="Estado de la notificación", default=False) #Entregado o no
    User_id: int = Field(..., description="Foreign Key to User")
    Mensaje: str = Field(..., description="Contenido del mensaje de la notificación")