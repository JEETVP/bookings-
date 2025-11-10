from fastapi import APIRouter, HTTPException, Path
from typing import Any, Dict, List, Optional
from bson import ObjectId
from utils.mongodb import get_bookings_collection

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
    responses={404: {"description": "Not found"}},
)

def _iso(dt: Optional[Any]) -> Optional[str]:
    """Convierte datetime a ISO 8601 si viene, tolera None y strings ya ISO."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    try:
        return dt.isoformat()
    except Exception:
        return str(dt)

def serialize_booking(doc: Dict[str, Any]) -> Dict[str, Any]:
    # Id (string): prioriza _id de Mongo; si no, usa Id legacy
    id_out = str(doc["_id"]) if "_id" in doc else doc.get("Id")

    room_id = doc.get("room_id", doc.get("Room_Id"))
    user_id = doc.get("user_id", doc.get("User_Id"))
    estado = doc.get("status", doc.get("Estado"))

    check_in = doc.get("check_in", doc.get("BookingIn"))
    check_out = doc.get("check_out", doc.get("BookingOn"))

    created_at = doc.get("created_at")
    num_guests = doc.get("num_guests")
    total_price = doc.get("total_price")

    return {
        "Id": id_out,
        "Room_Id": room_id,
        "User_Id": user_id,
        "Estado": estado,
        "BookingIn": _iso(check_in),
        "BookingOn": _iso(check_out),
        "created_at": _iso(created_at),
        "num_guests": num_guests,
        "total_price": total_price,
    }

def _find_booking_by_any_id(col, booking_id: str) -> Optional[Dict[str, Any]]:
    if ObjectId.is_valid(booking_id):
        doc = col.find_one({"_id": ObjectId(booking_id)})
        if doc:
            return doc
    try:
        int_id = int(booking_id)
        doc = col.find_one({"Id": int_id})
        if doc:
            return doc
    except ValueError:
        pass

    return None

@router.get("/", response_model=List[Dict[str, Any]])
def get_bookings():
    """
    Lista todas las reservas desde Mongo, ordenadas por created_at desc si existe,
    fallback por _id desc.
    """
    col = get_bookings_collection()
    cursor = col.find({}).sort([("created_at", -1), ("_id", -1)])
    return [serialize_booking(doc) for doc in cursor]

@router.get("/{booking_id}")
def get_booking(
    booking_id: str = Path(..., description="Id de la reserva: ObjectId o Id entero legacy"),
):
    """
    Busca por `_id` (ObjectId) o por `Id` entero legacy, serializa a shape anterior.
    """
    col = get_bookings_collection()
    doc = _find_booking_by_any_id(col, booking_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Booking not found")
    return serialize_booking(doc)
