"""
Schemas de Pydantic para Bookings (Reservas)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from bson import ObjectId

class BookingBase(BaseModel):
    """Schema base para Booking"""
    room_id: str = Field(..., description="ID de la habitacion (MongoDB ObjectId)")
    user_id: int = Field(..., description="ID del usuario")
    check_in: datetime = Field(..., description="Fecha y hora de entrada")
    check_out: datetime = Field(..., description="Fecha y hora de salida")
    guest_name: str = Field(..., min_length=1, max_length=200, description="Nombre del huesped")
    guest_email: str = Field(..., description="Email del huesped")
    guest_phone: str = Field(..., description="Telefono del huesped")
    number_of_guests: int = Field(default=1, ge=1, le=10, description="Numero de huespedes")
    special_requests: Optional[str] = Field(None, max_length=500, description="Solicitudes especiales")

    @field_validator('check_out')
    @classmethod
    def validate_checkout_after_checkin(cls, v, info):
        """Validar que el check_out sea posterior al check_in"""
        if 'check_in' in info.data and v <= info.data['check_in']:
            raise ValueError("La fecha de salida debe ser posterior a la fecha de entrada")
        return v
    
    @field_validator('check_in')
    @classmethod
    def validate_checkin_future(cls, v):
        """Validar que el check_in no sea en el pasado"""
        if v < datetime.now():
            raise ValueError("La fecha de entrada no puede ser en el pasado")
        return v

class BookingCreate(BookingBase):
    """Schema para crear una nueva Reserva"""
    pass

class BookingUpdate(BaseModel):
    """Schema para actualizar una Reserva"""
    check_in: Optional[datetime] = Field(None, description="Nueva fecha de entrada")
    check_out: Optional[datetime] = Field(None, description="Nueva fecha de salida")
    guest_name: Optional[str] = Field(None, max_length=200, description="Nombre del huesped")
    guest_email: Optional[str] = Field(None, description="Email del huesped")
    guest_phone: Optional[str] = Field(None, description="Telefono del huesped")
    number_of_guests: Optional[int] = Field(None, ge=1, le=10, description="Numero de huespedes")
    special_requests: Optional[str] = Field(None, max_length=500, description="Solicitudes especiales")
    status: Optional[str] = Field(None, description="Estado de la reserva")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validar que el status sea valido"""
        if v is not None:
            valid_statuses = ['pendiente', 'confirmada', 'en_progreso', 'completada', 'cancelada']
            if v.lower() not in valid_statuses:
                raise ValueError(f"Status debe ser uno de: {', '.join(valid_statuses)}")
            return v.lower()
        return v

class BookingResponse(BaseModel):
    """Schema para respuesta de Booking"""
    id: str = Field(description="ID de la reserva")
    room_id: str = Field(description="ID de la habitacion")
    user_id: int = Field(description="ID del usuario")
    check_in: datetime = Field(description="Fecha y hora de entrada")
    check_out: datetime = Field(description="Fecha y hora de salida")
    guest_name: str = Field(description="Nombre del huesped")
    guest_email: str = Field(description="Email del huesped")
    guest_phone: str = Field(description="Telefono del huesped")
    number_of_guests: int = Field(description="Numero de huespedes")
    special_requests: Optional[str] = Field(None, description="Solicitudes especiales")
    status: str = Field(description="Estado de la reserva")
    room_status: str = Field(description="Estado actual de la habitacion")
    created_at: datetime = Field(description="Fecha de creacion")
    updated_at: Optional[datetime] = Field(None, description="Fecha de ultima actualizacion")

    class Config:
        json_encoders = {ObjectId: str}

class BookingStatusResponse(BaseModel):
    """Schema para respuesta de cambio de estado"""
    booking_id: str
    previous_status: str
    new_status: str
    room_previous_status: str
    room_new_status: str
    message: str
