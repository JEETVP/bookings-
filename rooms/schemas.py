"""
Schemas de Pydantic para Rooms
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    """Clase personalizada para manejar ObjectId de MongoDB"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class RoomBase(BaseModel):
    """Schema base para Room"""
    status: str = Field(..., max_length=50, description="Estado de la habitación (disponible, ocupada, mantenimiento)")
    descripcion: str = Field(..., max_length=100, description="Descripción de la habitación")
    characteristics: Optional[str] = Field(None, max_length=200, description="Características adicionales de la habitación")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validar que el status sea válido"""
        valid_statuses = ['disponible', 'ocupada', 'mantenimiento', 'reservada']
        if v.lower() not in valid_statuses:
            raise ValueError(f"Status debe ser uno de: {', '.join(valid_statuses)}")
        return v.lower()

class RoomUpdate(BaseModel):
    """Schema para actualizar una Room"""
    status: Optional[str] = Field(None, max_length=50, description="Estado de la habitación")
    descripcion: Optional[str] = Field(None, max_length=100, description="Descripción de la habitación")
    characteristics: Optional[str] = Field(None, max_length=200, description="Características adicionales de la habitación")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validar que el status sea válido si se proporciona"""
        if v is not None:
            valid_statuses = ['disponible', 'ocupada', 'mantenimiento', 'reservada']
            if v.lower() not in valid_statuses:
                raise ValueError(f"Status debe ser uno de: {', '.join(valid_statuses)}")
            return v.lower()
        return v

class RoomInDB(RoomBase):
    """Schema para Room en la base de datos"""
    id: str = Field(alias="_id", description="ID de MongoDB")
    created_at: datetime = Field(default_factory=datetime.now, description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class RoomResponse(BaseModel):
    """Schema para respuesta de Room"""
    id: str = Field(description="ID de la habitación")
    status: str = Field(description="Estado de la habitación")
    descripcion: str = Field(description="Descripción de la habitación")
    characteristics: Optional[str] = Field(None, description="Características adicionales de la habitación")
    created_at: datetime = Field(description="Fecha de creación")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")

    class Config:
        json_encoders = {ObjectId: str}
