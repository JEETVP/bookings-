from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from database import get_db
from models import Booking, BookingStatus


#Get general de bookings
router = APIRouter(
    prefix="/bookings",
    tags=["bookings"],
    responses={404: {"description": "Not found"}},
)

#Tenemos que serializar esto por algo muy importante: Json
#Serializamos Booking a dict para que se pueda convertir a JSON
def serialize_booking(b: Booking) -> dict:
    return {
        "Id": b.Id,
        "Room_Id": b.Room_Id,
        "User_Id": b.User_Id,
        "Estado": b.Estado.value if isinstance(b.Estado, BookingStatus) else b.Estado,
        "BookingIn": b.BookingIn.isoformat() if b.BookingIn else None,
        "BookingOn": b.BookingOn.isoformat() if b.BookingOn else None,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "num_guests": b.num_guests,
        "total_price": b.total_price,
    }

#Get general
@router.get("/")
def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(Booking).all()
    return [serialize_booking(b) for b in bookings]

#Get con id
@router.get("/{booking_id}")
def get_booking(
    booking_id: int = Path(..., ge=1, description="Id de la reserva (>=1)"),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.Id == booking_id).first() 
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return serialize_booking(booking)




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