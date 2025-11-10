from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from rooms.schemas import RoomUpdate, RoomResponse, RoomBase
from utils.mongodb import (
    get_rooms_collection,
    get_bookings_collection,
    get_users_collection,
)
from utils.auth import get_current_user
from models import User
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "no-reply@example.com")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Reservas")
router = APIRouter(prefix="/rooms", tags=["Rooms"])

def _utc_now():
    return datetime.now(timezone.utc)

def room_helper(room) -> dict:
    return {
        "id": str(room["_id"]),
        "status": room["status"],
        "descripcion": room["descripcion"],
        "characteristics": room.get("characteristics"),
        "created_at": room["created_at"],
        "updated_at": room.get("updated_at")
    }

def _send_email(to_email: str, subject: str, plain_text: str):
    """
    Envío simple con SendGrid. Si no hay API key, no truena: solo hace no-op.
    """
    if not SENDGRID_API_KEY:
        # Puedes cambiar a logging si prefieres
        print(f"[SendGrid disabled] To={to_email} | {subject} | {plain_text[:120]}...")
        return

    message = Mail(
        from_email=(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
        to_emails=to_email,
        subject=subject,
        plain_text_content=plain_text,
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        # Evita tirar 500 por correo; loguea y sigue
        print(f"[SendGrid] Error sending to {to_email}: {e}")

def _broadcast_room_back_online(room_id: str, room_desc: str):
    """
    Evento: room.back_online → correo a todos los usuarios registrados.
    (Si la base de usuarios es grande, considera paginar/cola.)
    """
    users_col = get_users_collection()
    cursor = users_col.find({}, {"email": 1})
    subject = "Habitación disponible de nuevo"
    for u in cursor:
        email = u.get("email")
        if not email:
            continue
        _send_email(
            email,
            subject,
            f"Buenas noticias: la habitación {room_desc} (ID {room_id}) volvió a estar disponible. ¡Reserva ahora!",
        )

def _notify_affected_bookings_on_status_change(room_id: str, old_status: str, new_status: str, room_desc: str):
    """
    Evento: room.updated.status_changed → correo a bookings futuras afectadas.
    Mensaje: “El cuarto ha pasado de old_status a new_status para tu booking X.”
    """
    bookings_col = get_bookings_collection()
    now = _utc_now()
    # Asumimos campos estándar: room_id, check_in (datetime UTC), user_id, (opcional user_email)
    cursor = bookings_col.find(
        {
            "room_id": room_id,
            "check_in": {"$gte": now},
        },
        {"_id": 1, "user_id": 1, "user_email": 1, "check_in": 1, "check_out": 1},
    )

    users_col = get_users_collection()
    subject = "Actualización de estado de tu habitación"
    for b in cursor:
        # Resuelve email del usuario
        email = b.get("user_email")
        if not email:
            uid = b.get("user_id")
            # uid puede ser str(ObjectId) o numérico; intentamos ambos
            user_doc = None
            if isinstance(uid, str) and ObjectId.is_valid(uid):
                user_doc = users_col.find_one({"_id": ObjectId(uid)}, {"email": 1})
            elif isinstance(uid, (int, float)):
                user_doc = users_col.find_one({"id": int(uid)}, {"email": 1})
            if user_doc:
                email = user_doc.get("email")

        if not email:
            # Sin email, omite el envío (o envía in-app si lo conectas)
            continue

        booking_id = str(b["_id"])
        plain = (
            f"Hola,\n\n"
            f"La habitación '{room_desc}' (ID {room_id}) ha cambiado de estado: "
            f"de '{old_status}' a '{new_status}' para tu reserva {booking_id}.\n"
            f"Check-in: {b.get('check_in')}\n"
            f"Check-out: {b.get('check_out')}\n\n"
            f"Si necesitas reprogramar o recibir apoyo, contáctanos.\n"
        )
        _send_email(email, subject, plain)

@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room: RoomBase,
    current_user: User = Depends(get_current_user)
):
    if str(current_user.get("role")) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear habitaciones"
        )

    collection = get_rooms_collection()
    room_dict = {
        "status": room.status,
        "descripcion": room.descripcion,
        "characteristics": room.characteristics,
        "created_at": _utc_now(),
        "updated_at": None
    }
    result = collection.insert_one(room_dict)
    created_room = collection.find_one({"_id": result.inserted_id})
    return room_helper(created_room)

@router.get("/", response_model=List[RoomResponse])
async def get_rooms(
    status_filter: Optional[str] = Query(None, description="Filtrar por estado"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a devolver"),
    current_user: User = Depends(get_current_user)
):
    collection = get_rooms_collection()
    filter_query: Dict[str, Any] = {}
    if status_filter:
        filter_query["status"] = status_filter.lower()
    rooms = list(collection.find(filter_query).skip(skip).limit(limit))
    return [room_helper(room) for room in rooms]

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    collection = get_rooms_collection()
    if not ObjectId.is_valid(room_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de habitación inválido"
        )
    obj_id = ObjectId(room_id)
    room = collection.find_one({"_id": obj_id})
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )
    return room_helper(room)

@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: str,
    room_update: RoomUpdate,
    current_user: User = Depends(get_current_user)
):
    if str(current_user.get("role")) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden actualizar habitaciones"
        )

    collection = get_rooms_collection()
    if not ObjectId.is_valid(room_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de habitación inválido"
        )
    obj_id = ObjectId(room_id)

    existing_room = collection.find_one({"_id": obj_id})
    if not existing_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )

    update_data = room_update.model_dump(exclude_unset=True)
    if update_data:
        # Detectar cambio de status
        old_status = existing_room.get("status")
        new_status = update_data.get("status", old_status)

        update_data["updated_at"] = _utc_now()
        collection.update_one({"_id": obj_id}, {"$set": update_data})
        updated_room = collection.find_one({"_id": obj_id})

        # --- EVENTOS ---
        if new_status != old_status:
            # Evento: room.updated.status_changed
            _notify_affected_bookings_on_status_change(
                room_id=str(obj_id),
                old_status=str(old_status),
                new_status=str(new_status),
                room_desc=existing_room.get("descripcion", ""),
            )

            # Evento: room.back_online (si pasa a 'available')
            if str(new_status).lower() == "available" and str(old_status).lower() in {"maintenance", "unavailable"}:
                _broadcast_room_back_online(
                    room_id=str(obj_id),
                    room_desc=existing_room.get("descripcion", ""),
                )

        return room_helper(updated_room)

    # Si no hubo cambios en payload, regresamos el original
    return room_helper(existing_room)

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    if str(current_user.get("role")) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden eliminar habitaciones"
        )
    collection = get_rooms_collection()
    if not ObjectId.is_valid(room_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de habitación inválido"
        )
    obj_id = ObjectId(room_id)
    result = collection.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )
    return None

@router.get("/stats/summary", response_model=dict)
async def get_rooms_stats(current_user: User = Depends(get_current_user)):
    collection = get_rooms_collection()
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    stats = list(collection.aggregate(pipeline))
    result = {
        "total": collection.count_documents({}),
        "by_status": {stat["_id"]: stat["count"] for stat in stats}
    }
    return result
