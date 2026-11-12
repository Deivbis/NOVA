# NOVA – Registro de decisiones (v0.1)

Decisiones tomadas donde la documentación oficial no definía el detalle
(NOVA-SPEC-014 §20) o donde dos documentos se contradecían
(NOVA-SPEC-012 §19).

## Decididas

- **D-001 Estados globales.** `NovaState` adopta los nombres de DOC-017
  (`SPEAKING`, `THINKING`, `EXECUTING`, `STOPPING`, `STOPPED`) en lugar de
  los de ARCH-003 (`RESPONDING`, `SHUTTING_DOWN`). Los estados visuales del
  orbe (`OrbState`, SPEC-008/009) no cambian; `SPEAKING` se muestra como
  "Hablando".
- **D-002 Transiciones de estado.** DOC-017 no las define. Reglas mínimas:
  los estados activos cambian libremente entre sí y pueden ir a `ERROR` o
  `STOPPING`; `STARTING` no puede ir a `STOPPED`; `ERROR` solo se recupera a
  `IDLE`; `STOPPING` solo va a `STOPPED`; `STOPPED` es final. Una transición
  no permitida se rechaza y se registra.
- **D-003 Niveles de riesgo.** DOC-017 los menciona sin definirlos. Se usan
  `LOW`, `MEDIUM` y `HIGH`, a revisar cuando exista el módulo Security.
- **D-004 Logging.** Archivo JSON con rotación y consola legible. Nunca se
  registran payloads, contenido de conversaciones ni secretos (SPEC-014 §9).
- **D-005 Eventos del Core.** `command.completed`, `command.failed`,
  `state.changed`, `core.started` y `core.stopped`. Llevan solo metadatos.
- **D-006 Secretos.** Se leen de variables de entorno `NOVA_<NOMBRE>`
  (SPEC-014 §5, DOC-022). Nunca se guardan en Git, base de datos ni logs.
- **D-007 Pruebas de UI en cuarentena.** `tests/conftest.py` excluye dos
  archivos que cierran el proceso de pytest al lanzar un `QThread` real. Se
  corrigen en la fase de UI (hace falta un `bridge.shutdown()`).

- **D-010 Arranque y cierre de la app de escritorio.** `application.py`
  usa el mismo `create_core()` y `create_configuration()` que la consola,
  activa el logging y registra la capacidad `chat.local`. Al cerrar, el
  orden es: `bridge.shutdown()`, `orchestrator.stop()` y, al final, cierre
  de la base de datos (una respuesta tardía no debe escribir en una base
  cerrada).

- **D-009 Modelo local.** `qwen3:4b-instruct` (Qwen3-4B-Instruct-2507, sin
  razonamiento), en Ollama con `keep_alive="2m"`. La etiqueta `qwen3:4b`
  genera cientos de tokens de razonamiento antes de responder (85 s frente
  a 4 s en un Ryzen 5 8600G solo con CPU) y `think=false` no lo desactiva.
  La capa de IA además descarta cualquier bloque `<think>` de la respuesta.

- **D-011 Voz de salida.** Piper por defecto (100 % local, offline-first);
  edge-tts como "voz online" opcional, apagada por defecto (envía el texto
  a servidores de Microsoft). Nota: piper-tts 1.3+ es GPL-3.0.
- **D-012 Voces.** Sin conexión: Atlas `es_MX-ald`, Asti `es_MX-claude`.
  Con conexión: Atlas `es-MX-JorgeNeural`, Asti `es-MX-DaliaNeural`.
  Reserva (España): `davefx` y `sharvard`. Género y calidad por confirmar
  al escucharlas.
- **D-013 Activación.** Primero "pulsar para hablar" con tecla global
  `Pause/Break` (configurable): una pulsación escucha, se detiene sola por
  silencio, y otra pulsación cancela o interrumpe. La palabra clave va al
  final de la fase; el modo continuo, después.
- **D-014 Palabra clave.** Frases de dos palabras (los modelos de
  openWakeWord ya entrenados son solo en inglés; hay que entrenar uno propio).
- **D-015 Reconocimiento.** faster-whisper `small`, CPU, español. Se carga
  al primer uso y se libera tras 5 min sin hablar (configurable).
- **D-016 Audio.** Nunca se guarda. Se procesa en memoria y solo la
  transcripción entra a la conversación, con las mismas reglas que el texto.
- **D-017 Identidad.** Concepto mínimo `ATLAS`/`ASTI` que elige la voz; el
  cambio no afecta a la conversación ni a la memoria. La personalidad
  (tono, "Jefe") es la Fase 5.
- **D-018 Latencia.** Primero voz con la respuesta completa; el streaming
  de la IA con habla por frases es el último paso de la fase.
- **D-019 Interfaz.** La Fase 4 no toca el QML: se prueba con
  `scripts/demo_voice.py` y funciones en el bridge. El micrófono en la
  interfaz llega con la Fase 10.

- **D-020 Resultado de la prueba técnica de voz.** Funcionan en Python 3.13
  / Windows: piper-tts 1.8.0, faster-whisper 1.2.1, ctranslate2 4.9.0,
  edge-tts 7.3.1 y onnxruntime 1.31.1. STT `small` en CPU: 1,1 s para 6 s de
  audio. Micrófono: dispositivo predeterminado a 16 kHz mono. Voces
  confirmadas por oído: Piper (sin conexión) y edge-tts (con conexión). Las
  voces de Piper se guardan en `%APPDATA%/NOVA/voices`. Whisper falla con
  nombres propios: se sesgará el vocabulario (`hotwords`) con "Atlas",
  "Asti", "NOVA" y el nombre del usuario. Un fallo de micrófono (MME error
  1) apareció en un entorno anterior y desapareció al unificar entornos
  (causa no determinada).
- **D-021 Selector de voz.** `TTSRouter` usa la voz local por defecto; la
  voz en línea solo si está activada y la conectividad no es OFFLINE. Si
  falla, vuelve a la local y no reintenta durante 60 s. Nunca registra el
  texto hablado.

- **D-022 Voz de salida real y preferencias.** `PiperTTSProvider` carga
  cada voz una sola vez (carga perezosa) desde `%APPDATA%/NOVA/voices`;
  `EdgeTTSProvider` decodifica el MP3 con PyAV y tiene un tope de 15 s;
  `SoundDevicePlayer` reproduce por la salida predeterminada. Ningún módulo
  importa las librerías de audio al arrancar. Las preferencias de voz viven
  en `%APPDATA%/NOVA/settings.json` (sección `voice`: `enabled`,
  `identity`, `prefer_online`, `hotkey`); si falta o es inválido se usan los
  valores por defecto, con la voz apagada.

## Pendientes

- **P-001 Ubicación de la base de datos.** DOC-016: `data/nova.db`. Código:
  `data/database/nova.db` (CLI) y `%APPDATA%/NOVA/nova.db` (app).
- **P-002 Nombre de campo.** DOC-017 usa `type` en Command y Event; el código
  usa `name`.
- **P-003 ORM.** DOC-022 indica SQLAlchemy; el código usa `sqlite3`.
- **P-004 Numeración duplicada.** Existen SPEC-015 y DOC-015, ambos
  "Sistema de Maestría", con contenido distinto y solapado con SPEC-006.
- **P-005 Documentos perdidos.** SPEC-001, DOC-001, DOC-019 y DOC-020.
- **P-006 Conectividad.** Nada detecta hoy si hay Internet; el estado
  `OFFLINE` se conectará con el chequeo real en la Fase 3.

- **D-007 Cierre de hilos de la UI.** `NovaUiBridge.shutdown()` detiene el
  temporizador, descarta lo pendiente y espera hasta 3 s al hilo activo
  (si no termina, lo fuerza). Las señales tardías se ignoran. Las pruebas
  que lanzaban un `QThread` real sin cerrarlo se reescribieron y ya no están
  en cuarentena.

- **P-009 Personalidad.** Hoy no hay instrucciones de sistema: NOVA responde
  con emojis y tono casual. Implementar Atlas/Asti, el tratamiento "Jefe" y
  el estilo sobrio de SPEC-002/003 en la Fase 5.
- **P-010 Markdown en la interfaz.** El QML muestra `**texto**` sin
  interpretar. Activar `textFormat: Text.MarkdownText` al integrar la
  interfaz (Fase 10).

- **P-012 Palabra clave.** Falta decidir las frases (¿una por identidad,
  "Hey Atlas" y "Hey Asti", o una común?).
- **P-013 Router de IA en la nube.** Previsto en DOC-022 (Gemini, Groq,
  OpenRouter), sin fase asignada en el roadmap.