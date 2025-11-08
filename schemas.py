from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import enum

# Esto lo dejamos aquí, para mongo este no cambia
class BookingStatus(str, enum.Enum):
    CONFIRMADA = "Confirmada"
    CANCELADA  = "Cancelada"
    COMPLETADA = "Completada"


# Es la base para crear y para responder, o sea, co común para una reserva, sin id ni la hora de creación
class BookingBase(BaseModel):
    room_id: str = Field(..., description="Id del room en la colección rooms") #Todavia no "relacionamos" con rooms
    user_id: str = Field(..., description="Id del user en la colección users") #Todavia no "relacionamos" con users
    estado: BookingStatus = Field(default=BookingStatus.CONFIRMADA,description="Estado de la reserva")
    booking_in: Optional[datetime] = None
    booking_on: Optional[datetime] = None
    num_guests: int = Field(..., ge=1, description="Mínimo 1 huésped")
    total_price: float = Field(..., ge=0, description="No negativo")

# Esto es lo que el cliente envia al crear (post), no manda id ni la hora de creacion
class BookingCreate(BookingBase):
    #Todavia aqui no tengo nada pero ya le pondre algo
    pass


# Esto es lo que mi api responde, incluyendo el id y la hora de creaicon
class BookingOut(BookingBase):
    id: str = Field(..., alias="_id") #Mongo usa _id
    created_at: datetime

    class Config:
        populate_by_name = True
