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

  - **D-008 Ubicación de datos.** La carpeta de datos es `%APPDATA%/NOVA`,
  reemplazable con la variable `NOVA_DATA_DIR` (en desarrollo, p. ej.
  `C:\NOVA\data`, como describe DOC-016). La base es `<datos>/nova.db`, los
  logs `<datos>/logs`. La consola y la app de escritorio usan
  `default_database_path()`, un único punto de verdad. Esto precisa
  DOC-016, que indica `data/nova.db` sin considerar el empaquetado `.exe`.

- **D-009 Modelo local.** `qwen3:4b-instruct` (Qwen3-4B-Instruct-2507, sin
  razonamiento), en Ollama con `keep_alive="2m"`. La etiqueta `qwen3:4b`
  genera cientos de tokens de razonamiento antes de responder (85 s frente
  a 4 s en un Ryzen 5 8600G solo con CPU) y `think=false` no lo desactiva.
  La capa de IA además descarta cualquier bloque `<think>` de la respuesta.

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