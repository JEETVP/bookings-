from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.core import settings  
from app.routers.auth import router as auth_router
from app.routers.notifications import router as notifications_router
from app.routers.bookings import router as bookings_router  

app = FastAPI(title="Api Booking")
app.version = "1.0.0"

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(notifications_router)  
app.include_router(bookings_router)

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
