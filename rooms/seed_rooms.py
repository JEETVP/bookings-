"""
Script para poblar la base de datos con habitaciones de ejemplo
"""
from datetime import datetime
from utils.mongodb import get_rooms_collection, get_mongo_client

def seed_rooms():
    """Crear habitaciones de ejemplo"""
    # Conectar a MongoDB
    get_mongo_client()
    collection = get_rooms_collection()
    
    # Verificar si ya hay habitaciones
    count = collection.count_documents({})
    if count > 0:
        print(f"Ya existen {count} habitaciones en la base de datos.")
        response = input("¿Deseas eliminar todas y crear nuevas? (s/n): ")
        if response.lower() == 's':
            collection.delete_many({})
            print("Habitaciones eliminadas")
        else:
            print("Operación cancelada")
            return
    
    # Habitaciones de ejemplo
    sample_rooms = [
        {
            "status": "disponible",
            "descripcion": "Habitación individual con baño privado",
            "created_at": datetime.now(),
            "updated_at": None
        },
        {
            "status": "disponible",
            "descripcion": "Habitación doble con vista al mar",
            "created_at": datetime.now(),
            "updated_at": None
        },
        {
            "status": "disponible",
            "descripcion": "Suite presidencial con jacuzzi",
            "created_at": datetime.now(),
            "updated_at": None
        },
        {
            "status": "disponible",
            "descripcion": "Habitación familiar para 4 personas",
            "created_at": datetime.now(),
            "updated_at": None
        },
        {
            "status": "ocupada",
            "descripcion": "Habitación doble estándar",
            "created_at": datetime.now(),
            "updated_at": None
        },
        {
            "status": "disponible",
            "descripcion": "Habitación con balcón y vista a la ciudad",
            "created_at": datetime.now(),
            "updated_at": None
        },
        {
            "status": "mantenimiento",
            "descripcion": "Habitación triple en renovación",
            "created_at": datetime.now(),
            "updated_at": None
        },
        {
            "status": "disponible",
            "descripcion": "Penthouse con terraza privada",
            "created_at": datetime.now(),
            "updated_at": None
        },
        {
            "status": "reservada",
            "descripcion": "Habitación doble deluxe",
            "created_at": datetime.now(),
            "updated_at": None
        },
        {
            "status": "disponible",
            "descripcion": "Habitación accesible para personas con movilidad reducida",
            "created_at": datetime.now(),
            "updated_at": None
        }
    ]
    
    # Insertar habitaciones
    result = collection.insert_many(sample_rooms)
    
    print(f"Se crearon {len(result.inserted_ids)} habitaciones de ejemplo:")
    print(f"   - Disponibles: {len([r for r in sample_rooms if r['status'] == 'disponible'])}")
    print(f"   - Ocupadas: {len([r for r in sample_rooms if r['status'] == 'ocupada'])}")
    print(f"   - Reservadas: {len([r for r in sample_rooms if r['status'] == 'reservada'])}")
    print(f"   - En mantenimiento: {len([r for r in sample_rooms if r['status'] == 'mantenimiento'])}")
    
    # Mostrar IDs
    print("\nIDs generados:")
    for i, room_id in enumerate(result.inserted_ids, 1):
        print(f"   {i}. {room_id}")

if __name__ == "__main__":
    print("Seeder de Habitaciones")
    seed_rooms()
    print("\nProceso completado")
