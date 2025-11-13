import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuración de la aplicación"""
    
    # MongoDB (para rooms, bookings, notifications)
    MONGODB_URI: str = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DB_NAME: str = os.getenv('MONGODB_DB_NAME', 'booking_db')
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'super-secret')
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRES', 15))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv('REFRESH_TOKEN_EXPIRES_DAYS', 7))
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        # Desarrollo local
        'http://localhost:3000', 
        'http://localhost:5173', 
        'http://127.0.0.1:3000', 
        'http://127.0.0.1:5173',
        # Frontend en Vercel
        'https://login-proyect-umber.vercel.app',
        # IPs específicas
        'http://44.226.145.213', 
        'https://44.226.145.213',
        'http://54.187.200.255', 
        'https://54.187.200.255',
        'http://34.213.214.55', 
        'https://34.213.214.55',
        'http://35.164.95.156', 
        'https://35.164.95.156',
        'http://44.230.95.183', 
        'https://44.230.95.183',
        'http://44.229.200.200', 
        'https://44.229.200.200'
    ]
    
    ALLOWED_CIDRS: List[str] = [
        '74.220.48.0/24',
        '74.220.56.0/24'
    ]
    
    # Roles válidos
    VALID_ROLES: List[str] = [
        'admin', 'clientes'
    ]

settings = Settings()