"""
Script de ejemplo para probar el flujo completo de reservas
"""
import requests
from datetime import datetime, timedelta
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_response(response, title="Respuesta"):
    print(f"\n{title}:")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, default=str))
    except:
        print(response.text)

def main():
    print_section("FLUJO COMPLETO DE RESERVA - DEMO")
    
    # 1. Obtener token
    print_section("1. Obtener Token de Autenticacion")
    response = requests.get(f"{BASE_URL}/get-test-token")
    print_response(response)
    
    if response.status_code != 200:
        print("Error obteniendo token. Asegurate de que el servidor este corriendo.")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Crear una habitacion
    print_section("2. Crear Habitacion de Prueba")
    room_data = {
        "status": "disponible",
        "descripcion": "Habitacion de prueba para demo de reservas"
    }
    response = requests.post(f"{BASE_URL}/rooms/", json=room_data, headers=headers)
    print_response(response)
    
    if response.status_code != 201:
        print("Error creando habitacion")
        return
    
    room_id = response.json()["id"]
    print(f"\nHABITACION CREADA: {room_id}")
    print(f"Estado inicial: disponible")
    
    # 3. Crear una reserva
    print_section("3. Crear Reserva")
    now = datetime.now()
    check_in = now + timedelta(hours=1)
    check_out = now + timedelta(days=2)
    
    booking_data = {
        "room_id": room_id,
        "user_id": 1,
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "guest_name": "Juan Perez Demo",
        "guest_email": "juan.demo@example.com",
        "guest_phone": "5551234567",
        "number_of_guests": 2,
        "special_requests": "Vista al mar si es posible"
    }
    
    response = requests.post(f"{BASE_URL}/bookings/", json=booking_data, headers=headers)
    print_response(response)
    
    if response.status_code != 201:
        print("Error creando reserva")
        return
    
    booking_id = response.json()["id"]
    print(f"\nRESERVA CREADA: {booking_id}")
    print(f"Estado reserva: confirmada")
    print(f"Estado habitacion: reservada")
    
    # 4. Ver estado de la habitacion
    print_section("4. Verificar Estado de Habitacion")
    response = requests.get(f"{BASE_URL}/rooms/{room_id}", headers=headers)
    print_response(response)
    print(f"\nEstado actual: {response.json()['status']}")
    
    # 5. Hacer check-in
    print_section("5. Hacer Check-In")
    response = requests.post(f"{BASE_URL}/bookings/{booking_id}/check-in", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nTRANSICION EXITOSA:")
        print(f"  Reserva: {result['previous_status']} -> {result['new_status']}")
        print(f"  Habitacion: {result['room_previous_status']} -> {result['room_new_status']}")
    
    # 6. Ver reserva actualizada
    print_section("6. Ver Reserva Actualizada")
    response = requests.get(f"{BASE_URL}/bookings/{booking_id}", headers=headers)
    print_response(response)
    
    # 7. Ver habitacion ocupada
    print_section("7. Verificar Habitacion Ocupada")
    response = requests.get(f"{BASE_URL}/rooms/{room_id}", headers=headers)
    print_response(response)
    print(f"\nEstado actual: {response.json()['status']}")
    
    # 8. Hacer check-out
    print_section("8. Hacer Check-Out")
    response = requests.post(f"{BASE_URL}/bookings/{booking_id}/check-out", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nTRANSICION EXITOSA:")
        print(f"  Reserva: {result['previous_status']} -> {result['new_status']}")
        print(f"  Habitacion: {result['room_previous_status']} -> {result['room_new_status']}")
        print(f"\nNOTA: La habitacion estara en mantenimiento por 30 minutos")
    
    # 9. Ver habitacion en mantenimiento
    print_section("9. Verificar Habitacion en Mantenimiento")
    response = requests.get(f"{BASE_URL}/rooms/{room_id}", headers=headers)
    print_response(response)
    print(f"\nEstado actual: {response.json()['status']}")
    
    # 10. Completar mantenimiento manualmente (opcional)
    print_section("10. Completar Mantenimiento Manualmente")
    response = requests.post(f"{BASE_URL}/bookings/{booking_id}/complete-maintenance", headers=headers)
    print_response(response)
    
    # 11. Ver habitacion disponible
    print_section("11. Verificar Habitacion Disponible Nuevamente")
    response = requests.get(f"{BASE_URL}/rooms/{room_id}", headers=headers)
    print_response(response)
    print(f"\nEstado final: {response.json()['status']}")
    
    # 12. Ver estadisticas
    print_section("12. Estadisticas de Reservas")
    response = requests.get(f"{BASE_URL}/bookings/stats/summary", headers=headers)
    print_response(response)
    
    # Resumen final
    print_section("RESUMEN DEL FLUJO")
    print(f"""
    Habitacion ID: {room_id}
    Reserva ID: {booking_id}
    
    ESTADOS RECORRIDOS:
    
    1. Habitacion creada -> disponible
    2. Reserva creada -> Habitacion: reservada
    3. Check-in -> Habitacion: ocupada
    4. Check-out -> Habitacion: mantenimiento
    5. Mantenimiento completado -> Habitacion: disponible
    
    CICLO COMPLETADO EXITOSAMENTE
    """)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\nERROR: No se pudo conectar al servidor.")
        print("Asegurate de que el servidor este corriendo:")
        print("  fastapi dev main.py")
    except Exception as e:
        print(f"\nERROR: {e}")
