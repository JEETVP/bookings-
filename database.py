from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from utils.config import settings

# Base para los modelos
Base = declarative_base()

# Configuración de la base de datos
DATABASE_URL = settings.DATABASE_URL

# Crear el engine
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Crear sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para inicializar la base de datos
def init_db():
    """Crear todas las tablas"""
    # Importar aquí para evitar import circular
    from models import User  
    Base.metadata.create_all(bind=engine)