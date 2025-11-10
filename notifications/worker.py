from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from pymongo import ReturnDocument
from utils.mongodb import get_notifications_collection
import os
MAX_RETRIES = int(os.getenv("NOTIF_MAX_RETRIES", "5"))
BACKOFF_BASE_SECONDS = int(os.getenv("NOTIF_BACKOFF_BASE_SECONDS", "30"))   # 1er reintento a 30s
BACKOFF_FACTOR = float(os.getenv("NOTIF_BACKOFF_FACTOR", "2.0"))            # exponencial: 30s, 60s, 120s...
FEATURE_FLAG = os.getenv("NOTIF_FEATURE_FLAG", "on").lower()  # on | off | dry-run

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _next_attempt_ts(attempts: int) -> datetime:
    delay = BACKOFF_BASE_SECONDS * (BACKOFF_FACTOR ** max(0, attempts - 1))
    return _utc_now() + timedelta(seconds=delay)

def _claim_one(col) -> Optional[Dict[str, Any]]:
    now = _utc_now()
    query = {
        "estado": "pendiente",
        "$and": [
            {"$or": [
                {"scheduled_at": {"$exists": False}},
                {"scheduled_at": None},
                {"scheduled_at": {"$lte": now}}
            ]},
            {"$or": [
                {"next_attempt_at": {"$exists": False}},
                {"next_attempt_at": None},
                {"next_attempt_at": {"$lte": now}}
            ]}
        ]
    }
    update = {
        "$set": {
            "estado": "processing",
            "updated_at": now
        }
    }
    doc = col.find_one_and_update(
        filter=query,
        update=update,
        sort=[("created_at", 1)],  # FIFO dentro de las elegibles
        return_document=ReturnDocument.AFTER
    )
    return doc

def _deliver(doc: Dict[str, Any]) -> bool:
    if FEATURE_FLAG == "off":
        return False
    if FEATURE_FLAG == "dry-run":
        print(f"[DRY-RUN] Notificación simulada: {doc.get('_id')}")
        return True

    # TODO: aquí integras el canal real (email/push/inapp). Por ahora True.
    return True


def process_pending(limit: int = 100):
    col = get_notifications_collection()
    processed = 0

    while processed < limit:
        doc = _claim_one(col)
        if not doc:
            break  
        now = _utc_now()
        try:
            ok = _deliver(doc)

            if ok:
                updates = {
                    "$set": {
                        "estado": "enviado",
                        "sent_at": now,
                        "updated_at": now
                    }
                }
            else:
                attempts = int(doc.get("intentos", 0)) + 1
                if attempts >= MAX_RETRIES:
                    updates = {
                        "$set": {
                            "estado": "fallido",
                            "updated_at": now,
                            "next_attempt_at": None
                        },
                        "$inc": {"intentos": 1}
                    }
                else:
                    updates = {
                        "$set": {
                            "estado": "pendiente",
                            "updated_at": now,
                            "next_attempt_at": _next_attempt_ts(attempts)
                        },
                        "$inc": {"intentos": 1}
                    }

            col.update_one({"_id": doc["_id"]}, updates)

        except Exception as e:
            attempts = int(doc.get("intentos", 0)) + 1
            fallido = {
                "$set": {
                    "estado": "fallido",
                    "updated_at": now,
                    "last_error_message": str(e),
                    "next_attempt_at": None
                },
                "$inc": {"intentos": 1}
            }
            col.update_one({"_id": doc["_id"]}, fallido)

        processed += 1

    if processed:
        print(f"[worker] Procesadas {processed} notificaciones")
