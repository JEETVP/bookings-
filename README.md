# 🏨 Bookings API

API REST para sistema de reservas de habitaciones construida con FastAPI y MongoDB.

## 📋 Características

- 🔐 Sistema de autenticación JWT
- 👥 Gestión de usuarios
- 🏠 Gestión de habitaciones
- 📅 Sistema de reservas (bookings)
- 🔔 Notificaciones
- 🗄️ Base de datos MongoDB con Beanie ODM

## 🛠️ Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **MongoDB** - Base de datos NoSQL
- **Beanie** - ODM (Object Document Mapper) para MongoDB
- **Pydantic** - Validación de datos
- **Motor** - Driver asíncrono para MongoDB
- **Python 3.10+**

## 📦 Instalación

1. Clona el repositorio:

```bash
git clone <repository-url>
cd bookings-
```

2. Crea un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Configura las variables de entorno:

```bash
cp .env.example .env
# Edita .env con tus configuraciones
```

5. Asegúrate de tener MongoDB ejecutándose:

```bash
# Con Docker:
docker run -d -p 27017:27017 --name mongodb mongo:latest

# O instala MongoDB localmente
```

## 🚀 Uso

Ejecuta el servidor de desarrollo:

```bash
uvicorn main:app --reload
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

## 📁 Estructura del Proyecto

```
bookings-/
├── main.py              # Punto de entrada de la aplicación
├── requirements.txt     # Dependencias del proyecto
├── .env.example        # Variables de entorno de ejemplo
├── lib/
│   ├── config.py       # Configuración de la aplicación
│   └── database.py     # Configuración de MongoDB
├── models/
│   └── models.py       # Modelos de datos (User, Booking, Room, Notification)
├── routers/            # Endpoints de la API (próximamente)
├── schemas/            # Esquemas Pydantic (próximamente)
└── utils/              # Utilidades (próximamente)
```

## 🔄 Estado del Proyecto

### ✅ Completado

- Configuración base de FastAPI
- Limpieza de dependencias SQL
- Modelos Pydantic base definidos
- Configuración de MongoDB preparada

### 🚧 En Desarrollo

- Integración con MongoDB usando Beanie
- Endpoints de autenticación
- CRUD de habitaciones
- Sistema de reservas
- Sistema de notificaciones

## 📝 Variables de Entorno

Ver `.env.example` para las variables necesarias:

- `MONGODB_URL` - URL de conexión a MongoDB
- `MONGODB_DATABASE` - Nombre de la base de datos
- `SECRET_KEY` - Clave secreta para JWT
- `ALGORITHM` - Algoritmo de encriptación JWT

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir los cambios que te gustaría hacer.

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.
