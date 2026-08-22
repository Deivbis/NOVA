# NOVA – Responsabilidades de módulos

| Módulo | Responsabilidad |
|---|---|
| core | Orquestación |
| ai | Inteligencia |
| voice | Voz |
| memory | Memoria conceptual |
| storage | Persistencia |
| automation | Acciones |
| security | Autorización y protección |
| plugins | Extensiones |
| ui | Interfaces |

## Regla

Cada módulo debe realizar únicamente las responsabilidades que le corresponden.

Un módulo no debe asumir responsabilidades pertenecientes a otro.

## Core

Core coordina.

No implementa directamente las capacidades especializadas.

## AI

AI interpreta y genera.

No ejecuta acciones críticas directamente.

## Voice

Voice transforma voz ↔ texto/audio.

No toma decisiones de negocio.

## Memory

Memory define qué representa una memoria.

Storage define cómo se persiste.

## Automation

Automation ejecuta acciones autorizadas.

## Security

Security autoriza o rechaza operaciones sensibles.

## UI

UI muestra estados y recibe interacción.

No debe convertirse en el orquestador.