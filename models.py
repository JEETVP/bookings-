# Clases de modelos para la aplicación de reservas de habitaciones
# Clases base: User, Booking, Room, Notification 
from pydantic import BaseModel, Field
from typing import  Optional, List
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
import bcrypt
import enum

# Importar Base desde database para evitar imports circulares
from database import Base

#User
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre_completo = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    direccion = Column(String(255), nullable=False)
    edad = Column(Integer, nullable=False)
    telefono = Column(String(20), nullable=False)
    role = Column(String(20), nullable=False, default="clientes", index=True)
    is_authorized = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    def set_password(self, raw_password: str):
        # Convertir la contraseña a bytes y generar hash
        password_bytes = raw_password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, raw_password: str) -> bool:
        # Verificar la contraseña
        try:
            # Validar que el hash existe y no está vacío
            if not self.password_hash:
                return False
            
            # Validar que el hash tiene el formato correcto de bcrypt
            if not (self.password_hash.startswith('$2a$') or 
                    self.password_hash.startswith('$2b$') or 
                    self.password_hash.startswith('$2y$')):
                return False
            
            # Validar que el hash tiene la longitud correcta (60 caracteres)
            if len(self.password_hash) != 60:
                return False
                
            password_bytes = raw_password.encode('utf-8')
            hash_bytes = self.password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
            
        except ValueError as e:
            # Log del error para debugging
            print(f"Error de validación de contraseña para usuario {self.email}: {e}")
            return False
        except Exception as e:
            # Log de cualquier otro error
            print(f"Error inesperado al validar contraseña para usuario {self.email}: {e}")
            return False
        
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nombre_completo': self.nombre_completo,
            'apellidos': self.apellidos,
            'direccion': self.direccion,
            'edad': self.edad,
            'telefono': self.telefono,
            'role': self.role,
            "created_at": self.created_at.isoformat() if hasattr(self, 'created_at') else None
        }

    def __repr__(self):
        return f"User('{self.nombre_completo} {self.apellidos}', '{self.email}'), role='{self.role}')"


#Booking
class Booking(BaseModel):
    Id: int = Field(..., description="Primary Key")
    Room_Id: int = Field(..., description="Foreign Key to Room")
    User_Id: int = Field(..., description="Foreign Key to User")
    Estado: str = Field(default="Pendiente", description="Estado de la reserva")
    BookingIn: Optional[datetime] = Field(None, description="Fecha y hora de entrada")
    BookingOn: Optional[datetime] = Field(None, description="Fecha y hora de salida")

#Room
class Room(BaseModel):
    Id: int = Field(..., description="Primary Key")
    Estado: str = Field(default="Disponible", description="Estado de la habitación")
    Capacidad: int = Field(..., ge=1, description="Capacidad de la habitación")
    Características: List = Field(..., description="Características de la habitación")
    Ubicación: str = Field(..., description="Ubicación de la habitación")

#Notification
class Notification(BaseModel):
    Id: int = Field(..., description="Primary Key")
    Estado: bool = Field(default=False, description="Estado de la notificación") #Entregado o no
    User_id: int = Field(..., description="Foreign Key to User")
    Mensaje: str = Field(..., description="Contenido del mensaje de la notificación")

# Modelos de Pydantic para autenticación
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class UserLogin(BaseModel):
    email: str
    password: str