# NOVA – Integración del Orbe

## Principio

El Orbe no es una NOVA independiente.

Es una interfaz del mismo Core.

## Arquitectura

Core
├── Main UI
└── Orb UI

## Estados

El Orbe utiliza:

- IDLE
- LISTENING
- PROCESSING
- RESPONDING
- ERROR

## Regla de no interferencia

El Orbe no debe:

- robar foco;
- mover el cursor;
- bloquear innecesariamente aplicaciones;
- capturar teclado accidentalmente;
- abrir la ventana principal sin autorización;
- interferir con videojuegos.

## Click-through

El Orbe debe poder utilizar comportamiento click-through cuando se encuentre en estado pasivo.

## Gaming Mode

Posteriormente podrá reducir:

- tamaño;
- opacidad;
- actividad visual.

Las funciones esenciales permanecerán disponibles.

## Arquitectura futura

NOVA Background
↓
Core
├── Main UI
└── Orb UI

El cierre de la Main UI no implica necesariamente detener Core.