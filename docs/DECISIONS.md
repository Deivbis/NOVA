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