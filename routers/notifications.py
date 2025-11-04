from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict, Any
from models import User
from utils.auth import get_current_user, get_admin_user
from notifications.schemas import NotificationCreate, NotificationUpdate, NotificationResponse
from notifications import service as svc

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(payload: NotificationCreate, admin: User = Depends(get_admin_user)):
    return svc.create_notification(payload)

@router.get("/", response_model=List[NotificationResponse])
async def list_all_notifications(
    estado: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    admin: User = Depends(get_admin_user)
):
    return svc.list_notifications(user_id=user_id, estado=estado, skip=skip, limit=limit)

@router.get("/mine", response_model=List[NotificationResponse])
async def list_my_notifications(
    estado: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    return svc.list_notifications(user_id=current_user.id, estado=estado, skip=skip, limit=limit)

@router.post("/{notif_id}/mark-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(notif_id: str, current_user: User = Depends(get_current_user)):
    notif = svc.get_notification_by_id(notif_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    # Solo dueño o admin
    if notif["user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    ok = svc.mark_as_read(notif_id)
    if not ok:
        raise HTTPException(status_code=400, detail="No se pudo marcar como leída")

@router.patch("/{notif_id}", response_model=NotificationResponse)
async def update_notification(notif_id: str, data: NotificationUpdate, admin: User = Depends(get_admin_user)):
    notif = svc.update_notification(notif_id, data)
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return notif

@router.delete("/{notif_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notif_id: str, admin: User = Depends(get_admin_user)):
    ok = svc.delete_notification(notif_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
