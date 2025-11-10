import os
from typing import Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "appdb")
CONNECT_TIMEOUT_MS = int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "5000"))
SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000"))
INIT_INDEXES = os.getenv("MONGODB_INIT_INDEXES", "true").lower() in {"1", "true", "yes", "y"}
_mongo_client: Optional[MongoClient] = None
_mongo_db: Optional[Database] = None
_indexes_initialized: bool = False


def get_mongo_client() -> MongoClient:
    """Obtiene (o crea) el cliente de MongoDB con timeouts sensatos."""
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(
                MONGODB_URI,
                connectTimeoutMS=CONNECT_TIMEOUT_MS,
                serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_MS,
                # retryWrites y demás flags suelen venir en el URI (sobre todo en SRV)
            )
            # Verificar la conexión (lanza si falla)
            _mongo_client.admin.command("ping")
            print(f"[Mongo] Conexión exitosa → {MONGODB_URI}")
        except ConnectionFailure as e:
            print(f"[Mongo] Error al conectar: {e}")
            raise
    return _mongo_client

def get_mongo_db() -> Database:
    """Obtiene (o crea) el objeto Database y asegura índices si aplica."""
    global _mongo_db, _indexes_initialized
    if _mongo_db is None:
        client = get_mongo_client()
        _mongo_db = client[MONGODB_DB_NAME]
        if INIT_INDEXES and not _indexes_initialized:
            _ensure_indexes(_mongo_db)
            _indexes_initialized = True
    return _mongo_db

def close_mongo_connection():
    """Cierra el cliente y limpia el singleton (útil en tests)."""
    global _mongo_client, _mongo_db, _indexes_initialized
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        _indexes_initialized = False
        print("[Mongo] Conexión cerrada")


# ===================== Colecciones =============================
def get_rooms_collection():
    return get_mongo_db()["rooms"]

def get_bookings_collection():
    return get_mongo_db()["bookings"]

def get_notifications_collection():
    return get_mongo_db()["notifications"]

def get_users_collection():
    return get_mongo_db()["users"]

def _ensure_indexes(db: Database):
    # Users
    users = db["users"]
    try:
        users.create_index([("email", ASCENDING)], unique=True, name="u_email")
        users.create_index([("role", ASCENDING)], name="i_role")
    except Exception as e:
        print(f"[Mongo][indexes][users] Warning: {e}")
    # Notifications
    notifs = db["notifications"]
    try:
        # Listado por usuario + orden reciente
        notifs.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="i_user_created")
        # Scheduler/worker por estado + fecha programada
        notifs.create_index([("estado", ASCENDING), ("scheduled_at", ASCENDING)], name="i_estado_sched")
        # Si implementas idempotencia:
        # notifs.create_index([("idempotency_key", ASCENDING)], unique=True, name="u_idem_key")
        # Si implementas reintentos con ventana:
        # notifs.create_index([("next_attempt_at", ASCENDING), ("estado", ASCENDING)], name="i_next_attempt_estado")
    except Exception as e:
        print(f"[Mongo][indexes][notifications] Warning: {e}")

    # Bookings (suele usarse por usuario y por fechas)
    bookings = db["bookings"]
    try:
        bookings.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)], name="i_user_created")
        bookings.create_index([("room_id", ASCENDING), ("check_in", ASCENDING)], name="i_room_checkin")
        bookings.create_index([("status", ASCENDING)], name="i_status")
    except Exception as e:
        print(f"[Mongo][indexes][bookings] Warning: {e}")

    # Rooms
    rooms = db["rooms"]
    try:
        rooms.create_index([("status", ASCENDING)], name="i_status")
        rooms.create_index([("name", ASCENDING)], name="i_name")
    except Exception as e:
        print(f"[Mongo][indexes][rooms] Warning: {e}")

    print("[Mongo] Índices verificados/creados")