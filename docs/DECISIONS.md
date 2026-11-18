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

- **P-015 Palabra clave (pospuesta).** Se entrena fuera del proyecto, en
  Google Colab (CPU local: 12-24 h; Colab: ~1,5-2,5 h), un modelo por frase.
  Candidatas: "hey atlas" y "hey asti"; "hey abi" se decide después (suena
  muy parecido a "asti"). Al integrarla: opción desactivada por defecto,
  silenciada mientras NOVA habla, indicador visible de escucha (Fase 10) y
  prueba técnica previa con Python 3.13. La activación de la v0.3.0 es la
  tecla global.

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

- **D-023 Servicio de voz.** `VoiceService` habla fuera del hilo de la UI
  (hilo daemon). `speak()` activa `SPEAKING` de inmediato y reemplaza lo que
  esté sonando; `stop()` corta el audio al instante; solo corre una
  síntesis a la vez (espeak no es seguro entre hilos). Publica
  `voice.speaking_started`, `voice.speaking_finished` (con `cancelled`) y
  `voice.error`, solo con metadatos. Un fallo de voz NO pone el Core en
  `ERROR`: se registra el código y el bridge muestra una burbuja transitoria
  (el texto de la respuesta ya está en el chat). El bridge no vuelve a
  `IDLE` mientras suena la voz y expone `voiceEnabled`, `voiceIdentity`,
  `stop_speaking`, `set_voice_enabled`, `set_voice_identity` y
  `set_online_voice` para la interfaz de la Fase 10. Mientras tanto, las
  preferencias se cambian con `scripts/set_voice.py`.


- **D-024 Entrada de voz.** Fin de frase por energía (RMS en bloques de
  100 ms): voz tras 0,3 s seguidos sobre el umbral, fin tras 1,2 s de
  silencio, "no detecté voz" a los 6 s y corte a los 20 s. El umbral es
  adaptativo, entre 0,008 y 0,025. Limitación conocida: en una sala con
  ruido de fondo por encima de ~0,025 de nivel no distingue la voz y graba
  hasta el máximo; los parámetros están en `EndOfSpeechConfig`.
  Transcripción con faster-whisper `small`, VAD y `beam_size=1`; el
  vocabulario (`settings.vocabulary`, por defecto Atlas, Asti, NOVA; se
  amplía con `scripts/set_voice.py "vocab=..."`) se pasa como `hotwords`.
  `VoiceInputService`: LISTENING → PROCESSING; eventos de escucha solo con
  metadatos (la transcripción viaja por callback, nunca por evento ni log);
  una pulsación cancela la escucha, interrumpe la voz o empieza a escuchar;
  se ignora si NOVA está ocupada. Los errores de entrada se publican como
  `voice.error` con `direction: "input"`.
  
- **D-025 Tecla de voz y chat por voz.** El atajo global (por defecto
  `Pause/Break`, configurable con `set_voice.py "hotkey=..."`) se registra
  con `RegisterHotKey` de Windows (sin librerías) y se recibe en la app Qt
  mediante un filtro de eventos nativos. Solo se registra si la voz está
  activada; si otra aplicación ya usa la tecla, NOVA arranca igual y lo
  anota en el log. Lo que dices llega al bridge por una señal de Qt (desde
  el hilo de escucha al hilo principal) y se envía al chat como si lo
  hubieras escrito. Los errores de entrada se muestran como "No pude
  escucharte..." y los de salida como "No pude hablar..." (campo
  `direction` del evento `voice.error`). Cierre: atajo, interfaz (con la
  escucha), Core y base de datos.


- **D-026 Habla por frases.** El texto de la respuesta se limpia para voz
  (sin Markdown, emojis, bloques de código ni URLs; las URL se leen como
  "enlace") y se parte en frases de al menos 20 caracteres (máximo 240,
  cortando en comas). Mientras suena una frase se sintetiza la siguiente
  (un hilo daemon de prefetch, una sola síntesis a la vez). `speaking_started`
  se publica una vez por respuesta, con el número de frases. Un fallo en una
  frase detiene la voz y se reporta una sola vez. Esto ajusta D-018: el
  streaming del modelo de lenguaje queda fuera de la v0.3.0.

- **D-027 Personalidad e identidad (Fase 5).** `nova/personality/`: perfiles
  de Atlas y Asti con un system prompt corto (~140 tokens: español, "Jefe"
  o "Señor" si el tono es formal, 1-3 frases, sin emojis ni Markdown, nunca
  finge acciones, pide aclaración si es ambiguo). El prompt se antepone al
  historial al enviarlo al modelo y NO se guarda en la conversación ni en
  la base. La identidad sigue en `settings.json` (`voice.identity`); un
  `IdentityService` la lee/cambia y publica `identity.changed`. El cambio
  por texto o voz ("cambia a Asti", "pasa a Abi"; Abi = alias de Asti) es
  determinista (frase completa, sin pasar por el modelo): responde con una
  confirmación fija del personaje, hablada con la voz nueva, y la
  conversación continúa intacta.

- **D-028 Ajuste del prompt tras el demo.** El primer prompt hacía que NOVA
  ofreciera acciones inexistentes (preparar café, buscar, agendar), se negara
  a contar chistes por el sarcasmo y diera consejos vagos. Se añadieron:
  "útil y concreto", sarcasmo "muy ligero y ocasional; nunca te niegues a
  ayudar", "no ofrezcas lo que no puedes" (con la lista de lo que no hace) y
  "ofrece solo explicar, aconsejar, ordenar ideas o redactar". El prompt pasó
  de ~140 a ~205 tokens (límite de prueba: 1000 caracteres). Verificado a
  mano con `scripts/demo_personality.py` y el cambio de identidad en la app.

- **D-029 Memoria persistente (Fase 6).** Solo se guarda lo que el usuario
  ordena ("recuerda que...", "anota...", "recuerda en Música que...").
  Tablas `memories` y `audit_logs` (migración v003); la auditoría registra
  acción, id y categoría, nunca el contenido. Categorías de SPEC-005 más
  "General" (añadida por no estar en la spec), asignadas por palabras clave o
  indicadas por el usuario. "Olvidar" desactiva (recuperable); el borrado
  definitivo solo existe en `scripts/memory.py purge --yes`. Las órdenes
  ("recuerda...", "olvida...", "qué recuerdas...") son deterministas: no
  pasan por el modelo y responden con una frase fija. Con varias
  coincidencias, "olvida X" pide más detalle en vez de borrar. En cada turno
  se seleccionan por coincidencia de palabras hasta 5 recuerdos (600
  caracteres) y se añaden al final del prompt de sistema como "Recuerdos
  autorizados"; si nada coincide, no se envía nada. Acceso solo a través de
  `MemoryService` (SPEC-014 §17).

- **D-030 Aprendizaje (Fase 7).** Dos señales: frases explícitas
  ("prefiero…", "me gusta…", "siempre uso…", "suelo…", "odio…") y patrones
  (mismo tema en ≥5 mensajes y ≥3 conversaciones en 30 días). Solo se
  guarda el tema, nunca el texto de las observaciones. Todo candidato se
  propone en el chat con su motivo y exige «sí»; un «no» no se vuelve a
  proponer. Confirmado → `MemoryService.remember(source="learned")`.
  Órdenes deterministas: "qué has aprendido", "deja de aprender" /
  "activa el aprendizaje" (`system.learning.enabled`), "confirma/descarta
  lo aprendido". Olvidar un aprendizaje = "olvida X" (memoria). Tablas
  `learning_candidates` y `learning_observations` (migración v004).
- **P-024 Patrones por categoría.** El patrón usa la categoría del
  clasificador; mejorar a palabras concretas.
- **P-025 Correcciones.** SPEC-015 §10 (la corrección prima sobre
  inferencias): hoy se corrige con "olvida X" + "recuerda que…".

- **D-031 Automatización y Security (Fase 8).** Orden: comando → plan
  (resuelve destino) → Security → confirmación hablada si es la primera
  vez → ejecución → auditoría. Lista blanca incorporada (programas básicos,
  carpetas de usuario, webs conocidas, multimedia) + permisos del usuario
  por destino (`permissions`, migración v005), revocables. Programas
  resueltos desde el menú Inicio (nunca ejecución libre de texto). Solo
  http/https; sin rutas de red. Multimedia por teclas de medios de Windows
  (controla la app que esté sonando). Auditoría: solo el tipo de acción.
- **P-026 Sí/no compartido** en `core/confirmation.py`; si hay varias
  confirmaciones pendientes manda la de automatización.

- **D-032 Archivos (Fase 8.2a).** Alcance: carpetas de usuario + carpetas
  autorizadas con «autoriza la carpeta X» (permiso `files`, distinto de
  `folder`). Bloqueado siempre: sistema, raíz de disco, red y raíces
  autorizadas como objetivo. Sin confirmación: buscar, listar, crear
  carpeta y copiar. Confirmación siempre y sin permiso permanente: mover,
  renombrar, borrar (solo papelera, SHFileOperation) y organizar (plan
  previo por tipo, solo archivos sueltos). Nunca sobrescribe. Auditoría:
  solo `file.<tipo>`.
- **P-027** Parser: el origen de copiar/mover (`de X a Y`) no admite
  espacios si es ruta; nombres con " de " se parten por el último «de».

- **D-033 Pendientes y recordatorios (8.2b).** Tablas `tasks` (migración
  v006). Recordatorio = pendiente con hora (en N min/horas/días, «a las
  H», «mañana a las H», «hoy»; sin am/pm y ya pasado → heurística +12 h).
  Aviso por voz y chat con un QTimer de 15 s; los vencidos con la app
  cerrada salen al iniciar indicando su hora. Sin hora → se pregunta.
  Auditoría: `task.created|done|cancelled|fired` con `todo|reminder`.
- **D-034 Rutinas (8.2c, ActionPlan).** Lista ordenada de pasos (solo
  abrir y multimedia), validada al crearla. Cada paso pasa por Security;
  si uno pide confirmación la rutina se pausa y continúa con «sí»; otro
  texto la detiene. Máx. 10 pasos. Auditoría: `routine.*`.
- **P-028** Recordatorios solo con la app abierta (no hay servicio en
  segundo plano); notificaciones del sistema para Fase 10 (UI).
- **P-029** Sin recordatorios recurrentes ni fechas por día de semana.

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

- **P-010 Markdown en la interfaz.** El QML muestra `**texto**` sin
  interpretar. Activar `textFormat: Text.MarkdownText` al integrar la
  interfaz (Fase 10).

- **P-012 Palabra clave.** Falta decidir las frases (¿una por identidad,
  "Hey Atlas" y "Hey Asti", o una común?).
- **P-013 Router de IA en la nube.** Previsto en DOC-022 (Gemini, Groq,
  OpenRouter), sin fase asignada en el roadmap.

- **P-014 Streaming del modelo de lenguaje.** Hablar mientras el modelo aún
  escribe exige llenar el mensaje del chat poco a poco (QML, Fase 10) y
  definir su persistencia. Estimación: ahorra unos 3-4 s en respuestas
  largas.
- **P-015 Palabra clave.** Pospuesta a la v0.3.1 (requiere entrenar un
  modelo propio; ver D-014 y P-012). La activación de la v0.3.0 es la tecla
  global.

- **P-019 Olvidar no borra el chat.** Un recuerdo olvidado sigue visible en
  la conversación donde se ordenó guardarlo; borrar esa conversación sí lo
  elimina.
- **P-020 Recuerdos y nube.** Los recuerdos solo se envían al modelo local;
  el router de nube (P-013) debe excluirlos por regla.
- **P-021 Clasificación.** Por palabras clave; mejorar con el modelo cuando
  convenga.
- **P-022 Hora y fecha reales.** Capacidad local sin modelo (Fase 8); hoy
  NOVA dice que no sabe la hora.

- **P-023 Memoria sin el modelo.** Las órdenes de memoria funcionan con
  Ollama apagado; responder una pregunta libre sobre un recuerdo ("¿cómo me
  llamo?") requiere el modelo local.