pragma Singleton
import QtQuick

QtObject {
    // Fondos
    readonly property color bg0: "#050a1c"
    readonly property color bg1: "#0a1230"
    readonly property color panel: "#0b1636"

    // Bordes y acentos
    readonly property color stroke: "#1d3170"
    readonly property color strokeStrong: "#3d63ff"
    readonly property color accent: "#2f4fe0"
    readonly property color accentSoft: "#6a8bff"
    readonly property color violet: "#7b4dff"
    readonly property color cyan: "#35d6ff"

    // Texto
    readonly property color textPrimary: "#f2f5ff"
    readonly property color textSecondary: "#8fa3d6"
    readonly property color textMuted: "#5d6fa0"

    // Orbe: "orb_hd" (imágenes de alta calidad) u "orb" (basado en la referencia original).
    // La escala hace que la esfera mida lo mismo con cualquiera de los dos conjuntos.
    readonly property string orbSet: "orb_hd"
    readonly property real orbScale: orbSet === "orb_hd" ? 1.392 : 1.0

    // Tipografía y radios
    readonly property string fontFamily: "Segoe UI"
    readonly property string iconFont: "Segoe MDL2 Assets"
    readonly property int radiusSm: 8
    readonly property int radiusMd: 12
    readonly property int radiusLg: 18
}
