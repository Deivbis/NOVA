# NOVA – Estados

## Estados principales

- STARTING
- IDLE
- LISTENING
- PROCESSING
- RESPONDING
- WAITING_CONFIRMATION
- OFFLINE
- ERROR
- SHUTTING_DOWN

## Estados del Orbe

- IDLE
- LISTENING
- PROCESSING
- RESPONDING
- ERROR

## Flujo normal

IDLE
↓
LISTENING
↓
PROCESSING
↓
RESPONDING
↓
IDLE

## Error

Cualquier estado
↓
ERROR
↓
IDLE

## Offline

NOVA puede continuar funcionando offline.

Una operación que requiera Internet debe devolver una respuesta controlada cuando no exista conectividad.