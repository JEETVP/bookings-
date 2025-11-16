"""
Router para manejo de Bookings (Reservas)
Incluye logica de transicion de estados automatica
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query, BackgroundTasks
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from bson.errors import InvalidId

from bookings.schemas import BookingCreate, BookingUpdate, BookingResponse, BookingStatusResponse
from utils.mongodb import get_rooms_collection, get_bookings_collection
from utils.auth import get_current_user
from models import User

router = APIRouter(prefix="/bookings", tags=["Bookings"])

# Estados validos de reserva
BOOKING_STATUSES = {
    'pendiente': 'Reserva creada, esperando confirmacion',
    'confirmada': 'Reserva confirmada, habitacion reservada',
    'en_progreso': 'Huesped ha hecho check-in, habitacion ocupada',
    'completada': 'Huesped ha hecho check-out, habitacion en mantenimiento',
    'cancelada': 'Reserva cancelada'
}

# Estados validos de habitacion
ROOM_STATUSES = {
    'disponible': 'Habitacion lista para reservar',
    'reservada': 'Habitacion reservada para una fecha futura',
    'ocupada': 'Habitacion actualmente ocupada',
    'mantenimiento': 'Habitacion en limpieza/mantenimiento'
}

# Helper functions
def booking_helper(booking) -> dict:
    """Convertir documento de MongoDB a diccionario"""
    return {
        "id": str(booking["_id"]),
        "room_id": booking["room_id"],
        "user_id": booking["user_id"],
        "check_in": booking["check_in"],
        "check_out": booking["check_out"],
        "guest_name": booking["guest_name"],
        "guest_email": booking["guest_email"],
        "guest_phone": booking["guest_phone"],
        "number_of_guests": booking["number_of_guests"],
        "special_requests": booking.get("special_requests"),
        "status": booking["status"],
        "room_status": booking.get("room_status", "unknown"),
        "created_at": booking["created_at"],
        "updated_at": booking.get("updated_at")
    }

def validate_room_availability(room_id: str, check_in: datetime, check_out: datetime, exclude_booking_id: Optional[str] = None):
    """Verificar si una habitacion esta disponible en las fechas solicitadas"""
    rooms_collection = get_rooms_collection()
    bookings_collection = get_bookings_collection()
    
    # Verificar que la habitacion existe
    try:
        room_obj_id = ObjectId(room_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de habitacion invalido"
        )
    
    room = rooms_collection.find_one({"_id": room_obj_id})
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitacion no encontrada"
        )
    
    # Buscar reservas que se traslapen con las fechas solicitadas
    query = {
        "room_id": room_id,
        "status": {"$in": ["confirmada", "en_progreso", "pendiente"]},
        "$or": [
            # Check-in dentro del rango existente
            {"check_in": {"$lte": check_out}, "check_out": {"$gte": check_in}},
        ]
    }
    
    # Excluir la reserva actual si se esta actualizando
    if exclude_booking_id:
        try:
            query["_id"] = {"$ne": ObjectId(exclude_booking_id)}
        except InvalidId:
            pass
    
    conflicting_bookings = list(bookings_collection.find(query))
    
    if conflicting_bookings:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La habitacion no esta disponible en las fechas solicitadas. Hay {len(conflicting_bookings)} reserva(s) que se traslapan."
        )
    
    return room

def update_room_status(room_id: str, new_status: str):
    """Actualizar el estado de una habitacion"""
    rooms_collection = get_rooms_collection()
    
    try:
        room_obj_id = ObjectId(room_id)
    except InvalidId:
        return False
    
    result = rooms_collection.update_one(
        {"_id": room_obj_id},
        {"$set": {"status": new_status, "updated_at": datetime.now()}}
    )
    
    return result.modified_count > 0

async def process_booking_transitions():
    """Procesar transiciones automaticas de estado basadas en fechas"""
    bookings_collection = get_bookings_collection()
    now = datetime.now()
    
    # Buscar reservas que deben cambiar de estado
    # 1. Confirmadas -> En progreso (check-in time reached)
    bookings_to_checkin = bookings_collection.find({
        "status": "confirmada",
        "check_in": {"$lte": now}
    })
    
    for booking in bookings_to_checkin:
        bookings_collection.update_one(
            {"_id": booking["_id"]},
            {"$set": {"status": "en_progreso", "updated_at": now}}
        )
        update_room_status(booking["room_id"], "ocupada")
    
    # 2. En progreso -> Completadas (check-out time reached)
    bookings_to_checkout = bookings_collection.find({
        "status": "en_progreso",
        "check_out": {"$lte": now}
    })
    
    for booking in bookings_to_checkout:
        bookings_collection.update_one(
            {"_id": booking["_id"]},
            {"$set": {"status": "completada", "updated_at": now}}
        )
        update_room_status(booking["room_id"], "mantenimiento")
    
    # 3. Habitaciones en mantenimiento -> Disponibles (30 minutos despues del checkout)
    maintenance_threshold = now - timedelta(minutes=30)
    completed_bookings = bookings_collection.find({
        "status": "completada",
        "check_out": {"$lte": maintenance_threshold}
    })
    
    for booking in completed_bookings:
        # Verificar que no haya otra reserva inmediata
        next_booking = bookings_collection.find_one({
            "room_id": booking["room_id"],
            "status": {"$in": ["confirmada", "pendiente"]},
            "check_in": {"$gte": booking["check_out"]}
        }, sort=[("check_in", 1)])
        
        if not next_booking or next_booking["check_in"] > now:
            update_room_status(booking["room_id"], "disponible")

@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking: BookingCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Crear una nueva reserva
    
    La habitacion pasa de 'disponible' a 'reservada'
    """
    bookings_collection = get_bookings_collection()
    
    # Validar disponibilidad
    room = validate_room_availability(booking.room_id, booking.check_in, booking.check_out)
    
    # Verificar que la habitacion este disponible o en mantenimiento (recien limpiada)
    if room["status"] not in ["disponible", "mantenimiento"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La habitacion no esta disponible para reserva. Estado actual: {room['status']}"
        )
    
    # Crear la reserva
    booking_dict = {
        "room_id": booking.room_id,
        "user_id": booking.user_id,
        "check_in": booking.check_in,
        "check_out": booking.check_out,
        "guest_name": booking.guest_name,
        "guest_email": booking.guest_email,
        "guest_phone": booking.guest_phone,
        "number_of_guests": booking.number_of_guests,
        "special_requests": booking.special_requests,
        "status": "confirmada",
        "room_status": "reservada",
        "created_at": datetime.now(),
        "updated_at": None
    }
    
    result = bookings_collection.insert_one(booking_dict)
    
    # Actualizar estado de la habitacion a 'reservada'
    update_room_status(booking.room_id, "reservada")
    
    # Programar verificacion de transiciones en background
    background_tasks.add_task(process_booking_transitions)
    
    # Obtener la reserva creada
    created_booking = bookings_collection.find_one({"_id": result.inserted_id})
    
    return booking_helper(created_booking)

@router.get("/", response_model=List[BookingResponse])
async def get_bookings(
    room_id: Optional[str] = Query(None, description="Filtrar por habitacion"),
    user_id: Optional[int] = Query(None, description="Filtrar por usuario"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    date_from: Optional[datetime] = Query(None, description="Filtrar desde fecha"),
    date_to: Optional[datetime] = Query(None, description="Filtrar hasta fecha"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de reservas con filtros
    """
    bookings_collection = get_bookings_collection()
    
    # Procesar transiciones automaticas antes de devolver datos
    background_tasks.add_task(process_booking_transitions)
    
    # Construir filtro
    filter_query = {}
    
    if room_id:
        filter_query["room_id"] = room_id
    
    if user_id:
        filter_query["user_id"] = user_id
    
    if status:
        filter_query["status"] = status.lower()
    
    if date_from or date_to:
        date_filter = {}
        if date_from:
            date_filter["$gte"] = date_from
        if date_to:
            date_filter["$lte"] = date_to
        filter_query["check_in"] = date_filter
    
    # Obtener reservas
    bookings = list(bookings_collection.find(filter_query).skip(skip).limit(limit).sort("check_in", -1))
    
    return [booking_helper(booking) for booking in bookings]

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Obtener una reserva por ID
    """
    bookings_collection = get_bookings_collection()
    
    # Procesar transiciones
    background_tasks.add_task(process_booking_transitions)
    
    try:
        obj_id = ObjectId(booking_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de reserva invalido"
        )
    
    booking = bookings_collection.find_one({"_id": obj_id})
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    return booking_helper(booking)

@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    booking_id: str,
    booking_update: BookingUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar una reserva
    
    Solo admin puede actualizar
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden actualizar reservas"
        )
    
    bookings_collection = get_bookings_collection()
    
    try:
        obj_id = ObjectId(booking_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de reserva invalido"
        )
    
    existing_booking = bookings_collection.find_one({"_id": obj_id})
    if not existing_booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Si se actualizan las fechas, validar disponibilidad
    new_check_in = booking_update.check_in or existing_booking["check_in"]
    new_check_out = booking_update.check_out or existing_booking["check_out"]
    
    if booking_update.check_in or booking_update.check_out:
        validate_room_availability(
            existing_booking["room_id"],
            new_check_in,
            new_check_out,
            exclude_booking_id=booking_id
        )
    
    # Preparar actualizacion
    update_data = booking_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now()
        
        bookings_collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
    
    # Procesar transiciones
    background_tasks.add_task(process_booking_transitions)
    
    updated_booking = bookings_collection.find_one({"_id": obj_id})
    return booking_helper(updated_booking)

@router.post("/{booking_id}/check-in", response_model=BookingStatusResponse)
async def check_in_booking(
    booking_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Hacer check-in de una reserva
    
    Transicion: confirmada -> en_progreso
    Habitacion: reservada -> ocupada
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden hacer check-in"
        )
    
    bookings_collection = get_bookings_collection()
    
    try:
        obj_id = ObjectId(booking_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de reserva invalido"
        )
    
    booking = bookings_collection.find_one({"_id": obj_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if booking["status"] != "confirmada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede hacer check-in. Estado actual: {booking['status']}"
        )
    
    # Actualizar reserva
    previous_status = booking["status"]
    bookings_collection.update_one(
        {"_id": obj_id},
        {"$set": {"status": "en_progreso", "updated_at": datetime.now()}}
    )
    
    # Actualizar habitacion
    rooms_collection = get_rooms_collection()
    room = rooms_collection.find_one({"_id": ObjectId(booking["room_id"])})
    previous_room_status = room["status"] if room else "unknown"
    
    update_room_status(booking["room_id"], "ocupada")
    
    return BookingStatusResponse(
        booking_id=booking_id,
        previous_status=previous_status,
        new_status="en_progreso",
        room_previous_status=previous_room_status,
        room_new_status="ocupada",
        message="Check-in realizado exitosamente. La habitacion ahora esta ocupada."
    )

@router.post("/{booking_id}/check-out", response_model=BookingStatusResponse)
async def check_out_booking(
    booking_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Hacer check-out de una reserva
    
    Transicion: en_progreso -> completada
    Habitacion: ocupada -> mantenimiento
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden hacer check-out"
        )
    
    bookings_collection = get_bookings_collection()
    
    try:
        obj_id = ObjectId(booking_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de reserva invalido"
        )
    
    booking = bookings_collection.find_one({"_id": obj_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if booking["status"] != "en_progreso":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede hacer check-out. Estado actual: {booking['status']}"
        )
    
    # Actualizar reserva
    previous_status = booking["status"]
    bookings_collection.update_one(
        {"_id": obj_id},
        {"$set": {"status": "completada", "updated_at": datetime.now()}}
    )
    
    # Actualizar habitacion a mantenimiento
    rooms_collection = get_rooms_collection()
    room = rooms_collection.find_one({"_id": ObjectId(booking["room_id"])})
    previous_room_status = room["status"] if room else "unknown"
    
    update_room_status(booking["room_id"], "mantenimiento")
    
    # Programar que la habitacion vuelva a disponible despues de 30 minutos
    background_tasks.add_task(process_booking_transitions)
    
    return BookingStatusResponse(
        booking_id=booking_id,
        previous_status=previous_status,
        new_status="completada",
        room_previous_status=previous_room_status,
        room_new_status="mantenimiento",
        message="Check-out realizado. La habitacion entrara en mantenimiento y estara disponible en 30 minutos."
    )

@router.post("/{booking_id}/complete-maintenance")
async def complete_maintenance(
    booking_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Completar mantenimiento manualmente
    
    Habitacion: mantenimiento -> disponible
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden completar mantenimiento"
        )
    
    bookings_collection = get_bookings_collection()
    
    try:
        obj_id = ObjectId(booking_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de reserva invalido"
        )
    
    booking = bookings_collection.find_one({"_id": obj_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if booking["status"] != "completada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se puede completar mantenimiento de reservas completadas"
        )
    
    # Verificar que no haya otra reserva inmediata
    bookings_collection_check = get_bookings_collection()
    next_booking = bookings_collection_check.find_one({
        "room_id": booking["room_id"],
        "status": {"$in": ["confirmada", "pendiente"]},
        "check_in": {"$gte": booking["check_out"]}
    }, sort=[("check_in", 1)])
    
    now = datetime.now()
    if next_booking and next_booking["check_in"] <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hay una reserva inmediata. La habitacion debe permanecer reservada."
        )
    
    # Actualizar habitacion a disponible
    update_room_status(booking["room_id"], "disponible")
    
    return {
        "message": "Mantenimiento completado. La habitacion ahora esta disponible.",
        "room_id": booking["room_id"],
        "new_status": "disponible"
    }

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancelar una reserva
    
    Libera la habitacion si estaba reservada
    """
    bookings_collection = get_bookings_collection()
    
    try:
        obj_id = ObjectId(booking_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de reserva invalido"
        )
    
    booking = bookings_collection.find_one({"_id": obj_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if booking["status"] in ["completada", "en_progreso"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede cancelar una reserva completada o en progreso"
        )
    
    # Actualizar estado a cancelada
    bookings_collection.update_one(
        {"_id": obj_id},
        {"$set": {"status": "cancelada", "updated_at": datetime.now()}}
    )
    
    # Si la habitacion estaba reservada, liberarla
    if booking["status"] == "confirmada":
        # Verificar que no haya otras reservas para la habitacion
        other_bookings = bookings_collection.count_documents({
            "room_id": booking["room_id"],
            "status": {"$in": ["confirmada", "en_progreso"]},
            "_id": {"$ne": obj_id}
        })
        
        if other_bookings == 0:
            update_room_status(booking["room_id"], "disponible")
    
    return None

@router.get("/stats/summary")
async def get_bookings_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadisticas de reservas
    """
    bookings_collection = get_bookings_collection()
    
    # Contar por estado
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]
    
    stats = list(bookings_collection.aggregate(pipeline))
    
    # Calcular ingresos estimados (puedes agregar un campo 'price' despues)
    total_bookings = bookings_collection.count_documents({})
    active_bookings = bookings_collection.count_documents({
        "status": {"$in": ["confirmada", "en_progreso"]}
    })
    
    return {
        "total": total_bookings,
        "active": active_bookings,
        "by_status": {stat["_id"]: stat["count"] for stat in stats}
    }
