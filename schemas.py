from pydantic import BaseModel, Field, validator
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

    #Validador para asegurar que booking_on es despues de booking_in
    @validator("booking_on")
    def booking_on_after_booking_in(cls, v, values):
        booking_in = values.get("booking_in")
        if booking_in and v and v <= booking_in:
            raise ValueError("booking_on debe ser posterior a booking_in")
        return v

# Esto es lo que el cliente envia al crear (post), no manda id ni la hora de creacion
class BookingCreate(BookingBase):
    #Datos que el cliente envia al crear una reserva
    user_id: str
    room_id: str
    booking_in: datetime
    booking_on: datetime
    num_guests: int
    total_price: float
    estado: BookingStatus


# Esto es lo que mi api responde, incluyendo el id y la hora de creaicon
class BookingOut(BookingBase):
    id: str = Field(..., alias="_id") #Mongo usa _id
    created_at: datetime = Field(..., description="Fecha y hora de creación de la reserva")

    class Config:
        populate_by_name = True
