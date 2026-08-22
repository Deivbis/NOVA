# NOVA – Arquitectura Base

## 1. Identidad

Nombre oficial:

NOVA – Personal Intelligence Platform.

Idioma principal:

Español.

Arquitectura:

Modular, híbrida y orientada a servicios internos.

---

## 2. Principio principal

Core es el orquestador central de NOVA.

Los módulos especializados no deben convertirse en orquestadores independientes.

---

## 3. Módulos principales

### Core

Responsable de:

- orquestación;
- comandos;
- eventos;
- estados;
- coordinación de servicios;
- flujo online/offline.

No implementa directamente las capacidades especializadas.

### AI

Responsable de inteligencia y procesamiento de solicitudes.

### Voice

Responsable de entrada y salida de voz.

Flujo:

Micrófono → Wake Word → STT → Core → AI → TTS → Altavoz.

### Memory

Responsable del concepto de memoria.

### Storage

Responsable de persistencia.

### Automation

Responsable de acciones sobre el sistema.

### Security

Responsable de autorización y protección de acciones sensibles.

### Plugins

Responsable de extensibilidad.

### UI

Responsable de interfaces de usuario.

Incluye:

- Main UI
- Orb UI

---

## 4. Comunicación

Los módulos deben comunicarse mediante contratos definidos por Core.

El acceso directo entre módulos debe evitarse cuando no sea necesario.

---

## 5. Arquitectura híbrida

NOVA debe poder funcionar sin Internet.

Cuando una operación requiere Internet:

1. Core identifica el requisito.
2. Core comprueba conectividad.
3. Si existe conexión, permite continuar.
4. Si no existe conexión, devuelve un resultado controlado.

NOVA no debe fingir que tiene conexión cuando está offline.

---

## 6. Orbe

El Orbe es una interfaz del mismo NOVA Core.

No es un asistente independiente.

Main UI y Orb UI consumen el mismo Core y los mismos estados.

---

## 7. Seguridad

Las operaciones críticas deben pasar por Security.

Automation puede solicitar una acción.

Security decide si está autorizada.

---

## 8. Principios

- Modularidad.
- Separación de responsabilidades.
- Bajo acoplamiento.
- Contratos explícitos.
- Seguridad por diseño.
- Funcionamiento offline.
- Uso de Internet únicamente cuando sea necesario.
- No interferencia del Orbe.
- Evolución incremental.