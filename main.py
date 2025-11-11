from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime
from contextlib import asynccontextmanager
from lib.config import settings
from lib.database import connect_to_mongo, close_mongo_connection, init_db
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación
    Se ejecuta al inicio y al cierre de la aplicación
    """
    # Startup: Conectar a MongoDB
    logger.info("🚀 Iniciando aplicación...")
    await connect_to_mongo()
    await init_db()
    logger.info("Aplicación iniciada correctamente")
    
    yield
    
    # Shutdown: Cerrar conexión a MongoDB
    logger.info("Cerrando aplicación...")
    await close_mongo_connection()
    logger.info("Aplicación cerrada")


app = FastAPI(
    title="Booking API",
    description="API para sistema de reservas",
    version="1.0.1",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(auth_router)

@app.get("/")
async def read_root():
    return {"Api Booking": app.version}

@app.get("/health")
async def health_check():
    """Punto de verificación de salud con estado de MongoDB"""
    from lib.database import client
    
    mongodb_status = "disconnected"
    try:
        if client:
            # Ping a MongoDB para verificar conexión
            await client.admin.command('ping')
            mongodb_status = "connected"
    except Exception as e:
        logger.error(f"Error al verificar estado de MongoDB: {e}")
        mongodb_status = "error"
    
    return {
        "status": "healthy" if mongodb_status == "connected" else "degraded",
        "version": app.version,
        "timestamp": datetime.now().astimezone().isoformat(),
        "uptime": "Service is running",
        "environment": "development",
        "database": {
            "mongodb": mongodb_status,
            "database_name": settings.MONGODB_DATABASE
        }
    }