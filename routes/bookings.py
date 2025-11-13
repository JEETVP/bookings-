from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from schemas import BookingCreate, BookingOut

from bson.errors import InvalidId



#Con esto inicializamos mongodb
#Aqui ajustamos el nombre y todo eso de acuerdo a lo que tengamos en nuestro entorno
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["bookings_db"]
bookings_col = db["bookings"]
users_col = db["users"]
rooms_col = db["rooms"]



router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
    responses={404: {"description": "Not found"}},
)

# --------------------------------------Endpoints ----------------------------------------------------------------

#Get general de los bookings con query params
@router.get("/", response_model=list[BookingOut])    
def get_bookings(
    estado: str | None = None,
    user_id: str | None = None,
    room_id: str | None = None,
):
    query = {}

    if estado:
        query["estado"] = estado
    if user_id:
        query["user_id"] = user_id
    if room_id:
        query["room_id"] = room_id

    docs = list(bookings_col.find(query))
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


#Post de los bookings
@router.post("/", response_model=BookingOut)
def create_booking(booking_in: BookingCreate):
    # Validar existencia de user_id
    try:
        user_oid = ObjectId(booking_in.user_id)
    except InvalidId:
        raise HTTPException(400, "user_id inválido")
    if not users_col.find_one({"_id": user_oid}):
        raise HTTPException(400, "Usuario no existe")

    # Validar existencia del room_id
    try:
        room_oid = ObjectId(booking_in.room_id)
    except InvalidId:
        raise HTTPException(400, "room_id inválido")
    room = rooms_col.find_one({"_id": room_oid})
    if not room:
        raise HTTPException(400, "Room no existe")
    
    #Verificacion del estado de la habitacion para que permita reservar
    estado_room = room.get("status") or room.get("Status")
    if estado_room.lower() not in ["available", "disponible"]:
        raise HTTPException(400, f"Room no está disponible para reservar (estado: {estado_room})")
    
    #Validar que el num_guests no exceda la capacidad del room
    capacidad = room.get("capacity") or room.get("Capacity")
    if capacidad and booking_in.num_guests > capacidad:
        raise HTTPException(
            400, f"Número de huéspedes excede la capacidad del room ({capacidad})"
        )
    
    #Validar que no haya reservas enpalmadas para el mismo room
    overlapping = bookings_col.find_one({
        "room_id":booking_in.room_id,
        "$or":[
            {
                "booking_in": {"$lt": booking_in.booking_on},
                "booking_on": {"$gt": booking_in.booking_in}
            }
        ]
    })
    if overlapping:
        raise HTTPException(400, "El room ya está reservado en las fechas indicadas")

    doc = booking_in.model_dump()
    doc["created_at"] = datetime.utcnow()
    doc["estado"] = "Confirmada"  # Aseguramos que el estado inicial sea CONFIRMADA

    result = bookings_col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)

    return doc

#Put de los bookings
@router.put("/{booking_id}", response_model=BookingOut)
def update_booking(booking_id: str, booking_in: BookingCreate):
    #Pequeña validación manual para verificar que el booking_id exista
    if not bookings_col.find_one({"_id": ObjectId(booking_id)}):
        raise HTTPException(404, "Booking no encontrado")
    
    #Validación manual para verificar que el user_id exista
    if not users_col.find_one({"_id": booking_in.user_id}):
        raise HTTPException(400, "User no existe")
    
    #Validación manual para verificar que el room_id exista
    if not rooms_col.find_one({"_id": booking_in.room_id}):
        raise HTTPException(400, "Room no existe")
    
    doc = booking_in.model_dump()
    bookings_col.update_one({"_id": ObjectId(booking_id)}, {"$set": doc})
    doc["_id"] = booking_id
    return doc

#Delete de los bookings
@router.delete("/{booking_id}")
def delete_booking(booking_id: str):
    result = bookings_col.delete_one({"_id": ObjectId(booking_id)})
    if result.deleted_count == 0:
        raise HTTPException(404, "Booking no encontrado")
    return {"detail": "Booking eliminado"}

# Get de un booking por ID
@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: str):
    try:
        oid = ObjectId(booking_id)
    except InvalidId:
        # Si mandan un id que ni siquiera es ObjectId válido
        raise HTTPException(status_code=400, detail="booking_id inválido")

    doc = bookings_col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Booking no encontrado")

    doc["_id"] = str(doc["_id"])
    return doc

'''
#Get normal sin query params (todavia)
@router.get("/", response_model=list[Booking])
def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(Booking).all()
    return bookings

#Get booking by id
@router.get("/{booking_id}", response_model=Booking)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking
'''