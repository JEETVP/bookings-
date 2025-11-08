from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from schemas import BookingCreate, BookingOut


#Co n esto inicializamos mongodb
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

#Get general de los bookings
@router.get("/", response_model=list[BookingOut])
def get_bookings():
    docs = list(bookings_col.find({}))
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


#Post de los bookings
@router.post("/", response_model=BookingOut)
def create_booking(booking_in: BookingCreate):
    #Una pequeña validación manual para verificar que el user_id y room_id existan
    if not users_col.find_one({"_id": booking_in.user_id}):
        raise HTTPException(400, "User no existe")
    if not rooms_col.find_one({"_id": booking_in.room_id}):
        raise HTTPException(400, "Room no existe")

    doc = booking_in.model_dump()
    doc["created_at"] = datetime.utcnow()

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