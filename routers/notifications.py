from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from models import Notification  

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationCreate(BaseModel):
    user_id: int = Field(..., description="ID del usuario relacionado")
    mensaje: str = Field(..., min_length=1, description="Mensaje de la notificación")

class NotificationUpdate(BaseModel):
    mensaje: Optional[str] = Field(None, description="Actualizacion de Notificacion")
    estado: Optional[bool] = Field(None, description="Entregada (True) o pendiente (False)")

class NotificationOut(Notification):
    created_at: datetime = Field(default_factory=datetime.utcnow)