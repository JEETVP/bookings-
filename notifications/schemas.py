from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

Estado = Literal["pendiente", "enviado", "fallido", "leido"]
Canal = Literal["inapp", "email", "push"]
#AQUI ESTA EL MODELO DE LO QUE VA A RECIBIR LA API AL CREAR Y EDITAR LAS MODIFICACIONES
class NotificationCreate(BaseModel):
    user_id: int = Field(..., ge=1)
    titulo: Optional[str] = Field(None, max_length=120)
    mensaje: str = Field(..., min_length=1, max_length=1000)
    canal: Canal = "inapp"
    scheduled_at: Optional[datetime] = None

class NotificationUpdate(BaseModel):
    titulo: Optional[str] = None
    mensaje: Optional[str] = None
    canal: Optional[Canal] = None
#LO QUE DEVUELVE LA API AL CLIENTE
class NotificationResponse(BaseModel):
    id: str
    user_id: int
    titulo: Optional[str]
    mensaje: str
    canal: Canal
    estado: Estado
    intentos: int
    created_at: datetime
    updated_at: Optional[datetime]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
