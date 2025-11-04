from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from typing import Optional, List, Dict, Any
from utils.mongodb import get_notifications_collection
from notifications.schemas import NotificationCreate, NotificationUpdate

def _doc_to_response(doc: Dict[str, Any]) -> Dict[str, Any]: #Convierte el documento de mongo para que pueda ser enviado como respuesta response_model
    return {
        "id": str(doc["_id"]),
        "user_id": doc["user_id"],
        "titulo": doc.get("titulo"),
        "mensaje": doc["mensaje"],
        "canal": doc["canal"],
        "estado": doc["estado"],
        "intentos": doc["intentos"],
        "created_at": doc["created_at"],
        "updated_at": doc.get("updated_at"),
        "scheduled_at": doc.get("scheduled_at"),
        "sent_at": doc.get("sent_at"),
    }

def create_notification(data: NotificationCreate) -> Dict[str, Any]: #crea una notificación apartir del schema definido en notificationcreate y devuelve la notificación formateada como doc_response
    col = get_notifications_collection()
    doc = {
        "user_id": data.user_id,
        "titulo": data.titulo,
        "mensaje": data.mensaje,
        "canal": data.canal,
        "estado": "pendiente",
        "intentos": 0,
        "created_at": datetime.now(),
        "updated_at": None,
        "scheduled_at": data.scheduled_at,
        "sent_at": None,
        "read_at": None,
    }
    res = col.insert_one(doc)
    return _doc_to_response(col.find_one({"_id": res.inserted_id}))

def get_notification_by_id(notif_id: str) -> Optional[Dict[str, Any]]: #busca la notificacion que este insertada en mongo, si esta insertada la devuelve en el formato
    try:
        oid = ObjectId(notif_id)
    except InvalidId:
        return None
    col = get_notifications_collection()
    doc = col.find_one({"_id": oid})
    return _doc_to_response(doc) if doc else None

def list_notifications( #construye el query y devuelve como una lista ya formateada de docresponsed, dependiendo del filtro que se le haya aplicado
    user_id: Optional[int] = None,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    col = get_notifications_collection()
    query: Dict[str, Any] = {}
    if user_id is not None:
        query["user_id"] = user_id
    if estado is not None:
        query["estado"] = estado
    docs = col.find(query).skip(skip).limit(limit).sort("created_at", -1)
    return [_doc_to_response(d) for d in docs]

def mark_as_read(notif_id: str) -> bool: #validacion de object id, jace el update one para cambiar el estado a leido
    try:
        oid = ObjectId(notif_id)
    except InvalidId:
        return False
    col = get_notifications_collection()
    res = col.update_one({"_id": oid}, {"$set": {"estado": "leido", "updated_at": datetime.now(), "read_at": datetime.now()}})
    return res.modified_count == 1

def update_notification(notif_id: str, data: NotificationUpdate) -> Optional[Dict[str, Any]]: #hace la validacion de que sea un objectid, para poder hacer el update de los campos de la notificacion
    try:
        oid = ObjectId(notif_id)
    except InvalidId:
        return None
    update = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
    if not update:
        return get_notification_by_id(notif_id)
    update["updated_at"] = datetime.now()
    col = get_notifications_collection()
    col.update_one({"_id": oid}, {"$set": update})
    return get_notification_by_id(notif_id)

def delete_notification(notif_id: str) -> bool: #valida que la notificacion sea objectId y si es verdadero elimina segun el id
    try:
        oid = ObjectId(notif_id)
    except InvalidId:
        return False
    col = get_notifications_collection()
    res = col.delete_one({"_id": oid})
    return res.deleted_count == 1
