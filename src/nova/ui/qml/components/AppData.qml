pragma Singleton
import QtQuick

// Datos de ejemplo de la interfaz, en un solo lugar.
// Para conectar datos reales: sustituye estas propiedades por modelos/propiedades de `backend`
// (por ejemplo `readonly property var projects: backend.projects`) y el resto de la UI no cambia.
QtObject {
    // ---- Proyectos --------------------------------------------------------
    // st: "En progreso" | "En pausa" | "Completado"   p: 0-100
    readonly property var projects: [
        { t: "NOVA - Asistente Personal", d: "Desarrollo y mejora continua de NOVA.", st: "En progreso", p: 65 },
        { t: "Sistema de Automatización", d: "Automatización de tareas diarias.", st: "En pausa", p: 60 },
        { t: "Proyecto Creativo", d: "Ideas y diseños futuros.", st: "En progreso", p: 20 },
        { t: "Documentación", d: "Guías y documentación técnica.", st: "Completado", p: 100 },
        { t: "Aprendizaje", d: "Cursos y desarrollo personal.", st: "En progreso", p: 80 },
        { t: "Vida Personal", d: "Metas y organización.", st: "En progreso", p: 38 }
    ]

    // ---- Memoria ----------------------------------------------------------
    // ic: nombre de icono en assets/icons (sin sufijo)
    readonly property var memoryCategories: [
        { ic: "note", t: "Notas importantes", n: "24 elementos" },
        { ic: "doc", t: "Documentos", n: "18 elementos" },
        { ic: "chat", t: "Conversaciones", n: "42 elementos" },
        { ic: "bulb", t: "Ideas", n: "36 elementos" }
    ]
    readonly property var memoryRecents: [
        { ic: "doc", t: "Plan de proyecto Nova", s: "Actualizado hace 2 horas" },
        { ic: "bulb", t: "Ideas para el futuro", s: "Actualizado hace 5 horas" },
        { ic: "chat", t: "Reunión con el equipo", s: "Actualizado ayer" }
    ]

    // ---- Dashboard --------------------------------------------------------
    // ic: "orb" muestra el orbe; cualquier otro valor es un icono de assets/icons
    readonly property var activity: [
        { ic: "orb", who: "NOVA", what: "Procesando solicitud de usuario", when: "Hace 2 min" },
        { ic: "doc", who: "Sistema", what: "Sincronizando memoria", when: "Hace 5 min" },
        { ic: "folder", who: "Proyectos", what: "Guardado automático", when: "Hace 12 min" },
        { ic: "windows", who: "Windows", what: "Conexión establecida", when: "Hace 1 h" },
        { ic: "memory", who: "Memoria", what: "Nueva nota importante guardada", when: "Hace 2 h" },
        { ic: "chat", who: "Conversación", what: "Resumen de la reunión generado", when: "Hace 3 h" },
        { ic: "cpu", who: "Sistema", what: "Optimización de recursos completada", when: "Hace 5 h" },
        { ic: "folder", who: "Proyectos", what: "Proyecto Creativo actualizado", when: "Ayer" }
    ]
    // pg: índice de página (0 Inicio, 1 Conversación, 2 Memoria, 3 Proyectos, 4 Dashboard, 5 Configuración); -1 = sin acción
    readonly property var quickActions: [
        { ic: "folderplus", t: "Crear proyecto", pg: 3 },
        { ic: "memory", t: "Abrir memoria", pg: 2 },
        { ic: "gear", t: "Configuración", pg: 5 },
        { ic: "help", t: "Ayuda", pg: -1 }
    ]

    // ---- Conversación -----------------------------------------------------
    // chats: lista de conversaciones   {cid, title, preview, time}
    readonly property var chats: [
        { cid: "c1", title: "Planificar el proyecto NOVA", preview: "Perfecto, empecemos por la interfaz.", time: "10:24" },
        { cid: "c2", title: "Ideas para el lanzamiento", preview: "Podemos preparar una demo corta.", time: "Ayer" },
        { cid: "c3", title: "Resumen de la reunión", preview: "Estos son los puntos principales:", time: "Ayer" },
        { cid: "c4", title: "Aprender QML", preview: "Los anchors sirven para alinear.", time: "Lun" },
        { cid: "c5", title: "Rutina de enfoque", preview: "Bloques de 50 minutos funcionan bien.", time: "Dom" }
    ]
    // messages: mensajes por chat, indexados por cid   {role: "user" | "nova", text, time}
    readonly property var messages: ({
        "c1": [
            { role: "user", text: "Hola NOVA, quiero planificar el desarrollo de mi asistente personal.", time: "10:20" },
            { role: "nova", text: "¡Hola Deivis! Con gusto. Podemos dividirlo en tres etapas: interfaz, memoria y voz. ¿Por cuál quieres empezar?", time: "10:21" },
            { role: "user", text: "Empecemos por la interfaz. Ya tengo el diseño listo.", time: "10:23" },
            { role: "nova", text: "Perfecto, empecemos por la interfaz. Te propongo definir primero las pantallas principales: Inicio, Memoria, Proyectos y Dashboard.", time: "10:24" }
        ],
        "c2": [
            { role: "user", text: "¿Qué te parece mostrar una demo en el lanzamiento?", time: "18:02" },
            { role: "nova", text: "Podemos preparar una demo corta que muestre el orbe en sus cinco estados y una conversación real.", time: "18:03" }
        ],
        "c3": [
            { role: "nova", text: "Estos son los puntos principales de la reunión: prioridades del trimestre, responsables y próximas fechas.", time: "16:40" }
        ],
        "c4": [],
        "c5": []
    })
    // sugerencias que se muestran en un chat vacío
    readonly property var chatSuggestions: [
        "Resume mi día de hoy",
        "Ayúdame a planear un proyecto",
        "Busca algo en mi memoria"
    ]
}
