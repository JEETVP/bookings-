from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager
from utils.config import settings
from routers.notifications import router as notifications_router
from rooms.rooms import router as rooms_router
from bookings.bookings import router as bookings_router
from utils.mongodb import get_mongo_client, close_mongo_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionar el ciclo de vida de la aplicación"""
    # Startup: Inicializar MongoDB
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

app.include_router(notifications_router)
app.include_router(rooms_router)
app.include_router(bookings_router)

@app.get("/")
async def read_root():
    return {"Api Booking": app.version}

@app.get("/get-test-token")
async def get_test_token():
    """Endpoint para obtener un token de prueba (admin)"""
    from utils.auth import create_access_token, create_refresh_token
    from datetime import timedelta
    
    access_token = create_access_token(
        data={"sub": "1", "role": "admin"},
        expires_delta=timedelta(minutes=60)
    )
    refresh_token = create_refresh_token(
        data={"sub": "1", "role": "admin"},
        expires_delta=timedelta(days=7)
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "message": "Use este token en el header Authorization: Bearer {access_token}"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": app.version,
        "timestamp": datetime.now().astimezone().isoformat(),
        "uptime": "Service is running",
        "environment": "production",
    }
