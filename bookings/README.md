# Sistema de Reservas (Bookings)

## Flujo de Estados

### Estados de Reserva
1. **pendiente**: Reserva creada, esperando confirmacion
2. **confirmada**: Reserva confirmada, habitacion reservada
3. **en_progreso**: Huesped ha hecho check-in, habitacion ocupada
4. **completada**: Huesped ha hecho check-out, habitacion en mantenimiento
5. **cancelada**: Reserva cancelada

### Estados de Habitacion (automaticos)
1. **disponible**: Habitacion lista para reservar
2. **reservada**: Habitacion reservada para una fecha futura
3. **ocupada**: Habitacion actualmente ocupada por un huesped
4. **mantenimiento**: Habitacion en limpieza (30 minutos despues del check-out)

## Flujo Completo de una Reserva

```
CREAR RESERVA
│
├─> Estado Reserva: confirmada
├─> Estado Habitacion: disponible -> reservada
│
CHECK-IN (manual o automatico en fecha/hora)
│
├─> Estado Reserva: confirmada -> en_progreso
├─> Estado Habitacion: reservada -> ocupada
│
CHECK-OUT (manual o automatico en fecha/hora)
│
├─> Estado Reserva: en_progreso -> completada
├─> Estado Habitacion: ocupada -> mantenimiento
│
MANTENIMIENTO (automatico despues de 30 min)
│
├─> Estado Reserva: completada (sin cambios)
└─> Estado Habitacion: mantenimiento -> disponible
```

## Endpoints Disponibles

### 1. Crear Reserva
**POST** `/bookings/`

**Requiere**: Token de autenticacion

**Body**:
```json
{
  "room_id": "673f8a5b2c1e4d3f2a1b9c8d",
  "user_id": 1,
  "check_in": "2025-11-20T14:00:00",
  "check_out": "2025-11-23T12:00:00",
  "guest_name": "Juan Perez",
  "guest_email": "juan@example.com",
  "guest_phone": "5551234567",
  "number_of_guests": 2,
  "special_requests": "Cama king size"
}
```
PONER ATENCION EN FORMATO DE LA HORA, el que acepta es  T[HH/MM/SS], si se agrega algo mas dara error

**Validaciones**:
- Check-in no puede ser en el pasado
- Check-out debe ser posterior al check-in
- Habitacion debe estar disponible en las fechas
- No debe haber reservas que se traslapen

### 2. Listar Reservas
**GET** `/bookings/`

**Query Parameters**:
- `room_id`: Filtrar por habitacion
- `user_id`: Filtrar por usuario
- `status`: Filtrar por estado (pendiente, confirmada, en_progreso, completada, cancelada)
- `date_from`: Fecha desde
- `date_to`: Fecha hasta
- `skip`: Paginacion (default: 0)
- `limit`: Limite de resultados (default: 100)

### 3. Ver Reserva Especifica
**GET** `/bookings/{booking_id}`

### 4. Actualizar Reserva
**PUT** `/bookings/{booking_id}`

**Requiere**: Token de admin

**Body** (todos los campos opcionales):
```json
{
  "check_in": "2025-11-21T14:00:00",
  "check_out": "2025-11-24T12:00:00",
  "guest_name": "Juan Perez Garcia",
  "number_of_guests": 3
}
```

### 5. Check-In Manual
**POST** `/bookings/{booking_id}/check-in`

**Requiere**: Token de admin

**Efecto**:
- Reserva: confirmada -> en_progreso
- Habitacion: reservada -> ocupada

### 6. Check-Out Manual
**POST** `/bookings/{booking_id}/check-out`

**Requiere**: Token de admin

**Efecto**:
- Reserva: en_progreso -> completada
- Habitacion: ocupada -> mantenimiento
- Habitacion volvera a "disponible" automaticamente en 30 minutos

### 7. Completar Mantenimiento Manualmente
**POST** `/bookings/{booking_id}/complete-maintenance`

**Requiere**: Token de admin

**Efecto**:
- Habitacion: mantenimiento -> disponible (antes de los 30 minutos)

### 8. Cancelar Reserva
**DELETE** `/bookings/{booking_id}`

**Efecto**:
- Reserva: cualquier estado -> cancelada
- Habitacion: reservada -> disponible (si no hay otras reservas)

**Restricciones**:
- No se pueden cancelar reservas en_progreso o completadas

### 9. Estadisticas
**GET** `/bookings/stats/summary`

**Respuesta**:
```json
{
  "total": 50,
  "active": 20,
  "by_status": {
    "confirmada": 15,
    "en_progreso": 5,
    "completada": 25,
    "cancelada": 5
  }
}
```

## Transiciones Automaticas

El sistema ejecuta automaticamente en segundo plano (background tasks):

1. **Check-in automatico**: Cuando llega la hora de check-in, la reserva pasa de "confirmada" a "en_progreso"
2. **Check-out automatico**: Cuando llega la hora de check-out, la reserva pasa de "en_progreso" a "completada"
3. **Fin de mantenimiento**: 30 minutos despues del check-out, la habitacion pasa de "mantenimiento" a "disponible"

## Casos de Uso Comunes

### Escenario 1: Reserva Normal

```bash
# 1. Crear reserva
POST /bookings/
{
  "room_id": "673f...",
  "check_in": "2025-11-20T14:00:00",
  "check_out": "2025-11-23T12:00:00",
  ...
}
# Resultado: Reserva confirmada, habitacion reservada

# 2. El dia del check-in (automatico o manual)
POST /bookings/{id}/check-in
# Resultado: Reserva en_progreso, habitacion ocupada

# 3. El dia del check-out (automatico o manual)
POST /bookings/{id}/check-out
# Resultado: Reserva completada, habitacion en mantenimiento

# 4. Despues de 30 minutos (automatico)
# Resultado: Habitacion disponible
```

### Escenario 2: Cancelacion

```bash
# Cliente cancela antes del check-in
DELETE /bookings/{id}
# Resultado: Reserva cancelada, habitacion disponible de nuevo
```

### Escenario 3: Reservas Consecutivas

```bash
# Reserva 1: Nov 20-23
# Reserva 2: Nov 23-26

# Al hacer check-out de Reserva 1:
# - Habitacion pasa a mantenimiento
# - Como hay otra reserva inmediata (Reserva 2), 
#   la habitacion pasa automaticamente a "reservada"
#   en lugar de "disponible"
```

## Validaciones del Sistema

1. **Prevenir doble reserva**: No se pueden crear reservas que se traslapen
2. **Fechas validas**: Check-in no puede ser en el pasado
3. **Orden de fechas**: Check-out debe ser posterior al check-in
4. **Estados validos**: Solo se pueden hacer transiciones permitidas
5. **Permisos**: Solo admin puede hacer check-in/check-out

## Integracion con Rooms

El sistema de bookings actualiza automaticamente el estado de las habitaciones:

```
Booking Status    ->    Room Status
-----------------------------------------
confirmada        ->    reservada
en_progreso       ->    ocupada
completada        ->    mantenimiento
cancelada         ->    disponible
(30 min despues)  ->    disponible
```

## Prueba Rapida

1. Obtener token:
```bash
GET /get-test-token
```

2. Crear habitacion (si no existe):
```bash
POST /rooms/
{
  "status": "disponible",
  "descripcion": "Habitacion de prueba"
}
```

3. Crear reserva:
```bash
POST /bookings/
{
  "room_id": "{id_de_habitacion}",
  "user_id": 1,
  "check_in": "2025-11-17T14:00:00",
  "check_out": "2025-11-18T12:00:00",
  "guest_name": "Test User",
  "guest_email": "test@example.com",
  "guest_phone": "1234567890",
  "number_of_guests": 1
}
```

4. Ver estado de habitacion:
```bash
GET /rooms/{id_de_habitacion}
# Deberia estar en "reservada"
```

5. Hacer check-in:
```bash
POST /bookings/{id_de_reserva}/check-in
```

6. Ver estado de habitacion:
```bash
GET /rooms/{id_de_habitacion}
# Deberia estar en "ocupada"
```

7. Hacer check-out:
```bash
POST /bookings/{id_de_reserva}/check-out
```

8. Ver estado de habitacion:
```bash
GET /rooms/{id_de_habitacion}
# Deberia estar en "mantenimiento"
```

9. Esperar 30 minutos (o completar manualmente):
```bash
POST /bookings/{id_de_reserva}/complete-maintenance
```

10. Ver estado final:
```bash
GET /rooms/{id_de_habitacion}
# Deberia estar en "disponible"
```

## Notas Importantes

- Las transiciones automaticas se ejecutan en background tasks
- El mantenimiento dura 30 minutos por defecto (configurable)
- Si hay reservas consecutivas, el sistema las maneja automaticamente
- Todos los endpoints de modificacion requieren autenticacion
- Solo admin puede hacer check-in/check-out y actualizar reservas
