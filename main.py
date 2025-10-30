from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.auth import router as auth_router
from datetime import datetime
from utils.config import settings
from database import init_db

load_dotenv()

# Inicializar la base de datos
init_db()

app = FastAPI(
    title="Booking API",
    description="API para sistema de reservas",
    version="1.0.1"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/")
async def read_root():
    return {"Api Booking": app.version}

@app.get("/health")
async def health_check():
    # Punto de verificación de salud con fecha y hora actuales
    return {
        "status": "healthy",
        "version": app.version,
        "timestamp": datetime.now().astimezone().isoformat(),
        "uptime": "Service is running",
        "environment": "production"
    }