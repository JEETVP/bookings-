from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import os
import logging
from routers.notifications import router as notifications_router
from rooms.rooms import router as rooms_router
from utils.mongodb import get_mongo_client, close_mongo_connection
from scheduler import start_scheduler, stop_scheduler

def _get_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if raw == "*" or raw == "":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    get_mongo_client()
    app.state.scheduler = start_scheduler()
    logging.info("Aplicación iniciada correctamente")
    yield
    stop_scheduler(app.state.scheduler)
    close_mongo_connection()
    logging.info("Aplicación detenida")

app = FastAPI(title="Api Booking", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "Service is running",
        "environment": os.getenv("ENVIRONMENT", "production"),
    }
