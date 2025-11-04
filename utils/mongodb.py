"""
Configuración y conexión a MongoDB
"""
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from utils.config import settings

# Cliente de MongoDB (singleton)
_mongo_client: MongoClient = None
_mongo_db: Database = None

def get_mongo_client() -> MongoClient:
    """Obtener el cliente de MongoDB"""
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(settings.MONGODB_URI)
            # Verificar la conexión
            _mongo_client.admin.command('ping')
            print(f"Conexión a MongoDB exitosa: {settings.MONGODB_URI}")
        except ConnectionFailure as e:
            print(f"Error al conectar con MongoDB: {e}")
            raise
    return _mongo_client

def get_mongo_db() -> Database:
    """Obtener la base de datos de MongoDB"""
    global _mongo_db
    if _mongo_db is None:
        client = get_mongo_client()
        _mongo_db = client[settings.MONGODB_DB_NAME]
    return _mongo_db

def close_mongo_connection():
    """Cerrar la conexión a MongoDB"""
    global _mongo_client, _mongo_db
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        _mongo_db = None
        print("Conexión a MongoDB cerrada")

# Funciones helper para obtener colecciones
def get_rooms_collection():
    """Obtener la colección de rooms"""
    db = get_mongo_db()
    return db["rooms"]

def get_bookings_collection():
    """Obtener la colección de bookings"""
    db = get_mongo_db()
    return db["bookings"]

def get_notifications_collection():
    """Obtener la colección de notifications"""
    db = get_mongo_db()
    return db["notifications"]
