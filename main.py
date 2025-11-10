from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager
from utils.config import settings
from routes.auth import router as auth_router
from database import init_db
from routers.notifications import router as notifications_router
from rooms.rooms import router as rooms_router
from utils.mongodb import get_mongo_client, close_mongo_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionar el ciclo de vida de la aplicación"""
    # Startup: Inicializar conexiones
    init_db()
    get_mongo_client()
    print("Aplicación iniciada correctamente")
    
    yield
    
    # Shutdown: Cerrar conexiones
    close_mongo_connection()
    print("Aplicación detenida")

app = FastAPI(title="Api Booking", lifespan=lifespan)
app.version = "1.0.0"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(notifications_router)
app.include_router(rooms_router)

@app.get("/")
async def read_root():
    return {"Api Booking": app.version}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": app.version,
        "timestamp": datetime.now().astimezone().isoformat(),
        "uptime": "Service is running",
        "environment": "production",
    }
