from datetime import datetime
from utils.mongodb import get_notifications_collection

def process_pending(limit: int = 100):
    """
    Procesa notificaciones pendientes o programadas cuya hora ya llegó.
    Marca como 'enviado' si el “envío” (mock) “sale”.
    """
    col = get_notifications_collection()
    now = datetime.now()
    cursor = col.find({
        "estado": "pendiente",
        "$or": [
            {"scheduled_at": None},
            {"scheduled_at": {"$lte": now}}
        ]
    }).sort("created_at", 1).limit(limit)

    for doc in cursor:
        try:
            # simulación de envío
            ok = True  # aquí iría lógica real (email/push/etc.)
            updates = {"intentos": doc.get("intentos", 0) + 1, "updated_at": now}
            if ok:
                updates.update({"estado": "enviado", "sent_at": now})
            else:
                updates.update({"estado": "fallido"})
            col.update_one({"_id": doc["_id"]}, {"$set": updates})
        except Exception:
            col.update_one({"_id": doc["_id"]}, {"$set": {
                "estado": "fallido",
                "intentos": doc.get("intentos", 0) + 1,
                "updated_at": now
            }})
