"""
Router para manejo de Rooms (Habitaciones)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from rooms.schemas import RoomUpdate, RoomResponse, RoomBase
from utils.mongodb import get_rooms_collection
from utils.auth import get_current_user
from models import User

router = APIRouter(prefix="/rooms", tags=["Rooms"])

# Helper function para convertir documento de MongoDB a dict
def room_helper(room) -> dict:
    """Convertir documento de MongoDB a diccionario"""
    return {
        "id": str(room["_id"]),
        "status": room["status"],
        "descripcion": room["descripcion"],
        "characteristics": room.get("characteristics"),
        "created_at": room["created_at"],
        "updated_at": room.get("updated_at")
    }

@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room: RoomBase,
    current_user: User = Depends(get_current_user)
):
    """
    Crear una nueva habitación
    
    Requiere autenticación (admin)
    """
    # Verificar que el usuario sea admin
    if str(current_user.role) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden crear habitaciones"
        )
    
    collection = get_rooms_collection()
    
    # Preparar el documento
    room_dict = {
        "status": room.status,
        "descripcion": room.descripcion,
        "characteristics": room.characteristics,
        "created_at": datetime.now(),
        "updated_at": None
    }
    
    # Insertar en MongoDB
    result = collection.insert_one(room_dict)
    
    # Obtener el documento creado
    created_room = collection.find_one({"_id": result.inserted_id})
    
    return room_helper(created_room)

@router.get("/", response_model=List[RoomResponse])
async def get_rooms(
    status_filter: Optional[str] = Query(None, description="Filtrar por estado"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a devolver"),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de habitaciones
    
    Requiere autenticación
    """
    collection = get_rooms_collection()
    
    # Construir filtro
    filter_query = {}
    if status_filter:
        filter_query["status"] = status_filter.lower()
    
    # Obtener habitaciones
    rooms = list(collection.find(filter_query).skip(skip).limit(limit))
    
    return [room_helper(room) for room in rooms]

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtener una habitación por ID
    
    Requiere autenticación
    """
    collection = get_rooms_collection()
    
    # Validar ObjectId
    if not ObjectId.is_valid(room_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de habitación inválido"
        )
    
    obj_id = ObjectId(room_id)
    
    # Buscar habitación
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
    """
    Actualizar una habitación
    
    Requiere autenticación (admin)
    """
    # Verificar que el usuario sea admin
    if str(current_user.role) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden actualizar habitaciones"
        )
    
    collection = get_rooms_collection()
    
    # Validar ObjectId
    if not ObjectId.is_valid(room_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de habitación inválido"
        )
    
    obj_id = ObjectId(room_id)
    
    # Verificar que la habitación existe
    existing_room = collection.find_one({"_id": obj_id})
    if not existing_room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )
    
    # Preparar actualización
    update_data = room_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now()
        
        # Actualizar en MongoDB
        collection.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
    
    # Obtener habitación actualizada
    updated_room = collection.find_one({"_id": obj_id})
    
    return room_helper(updated_room)

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar una habitación
    
    Requiere autenticación (admin)
    """
    # Verificar que el usuario sea admin
    if str(current_user.role) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden eliminar habitaciones"
        )
    
    collection = get_rooms_collection()
    
    # Validar ObjectId
    if not ObjectId.is_valid(room_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de habitación inválido"
        )
    
    obj_id = ObjectId(room_id)
    
    # Eliminar habitación
    result = collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )
    
    return None

@router.get("/stats/summary", response_model=dict)
async def get_rooms_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas de habitaciones
    
    Requiere autenticación
    """
    collection = get_rooms_collection()
    
    # Contar por estado
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]
    
    stats = list(collection.aggregate(pipeline))
    
    # Formatear resultado
    result = {
        "total": collection.count_documents({}),
        "by_status": {stat["_id"]: stat["count"] for stat in stats}
    }
    
    return result
