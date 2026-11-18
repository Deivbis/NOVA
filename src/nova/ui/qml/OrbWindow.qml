import QtQuick
import QtQuick.Window

// Orbe permanente: solo el orbe, sin texto ni marco, siempre visible.
// Cambia `orbSize` para hacerlo más grande o más pequeño (la esfera mide ~62 % de ese valor).
// El área transparente deja pasar los clics (ver Backend.maskOrb).
Window {
    id: w
    property string orbMode: "idle"
    readonly property int orbSize: 90

    // la ventana abarca el orbe completo (incluye diamante, halo y ondas)
    readonly property int box: Math.round(orbSize * Theme.orbScale) + 6

    width: box
    height: box
    color: "transparent"
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    x: Screen.width - width - 40
    y: Screen.height - height - 90

    function applyMask() {
        if (!visible) return
        // elipse inscrita en la ventana: las esquinas vacías no capturan clics
        backend.maskOrb(w, 0, 0, width, height, 0, 0, 0, 0)
    }
    onVisibleChanged: Qt.callLater(applyMask)
    Component.onCompleted: Qt.callLater(applyMask)

    Orb {
        anchors.centerIn: parent
        size: w.orbSize
        mode: w.orbMode
    }
    DragHandler { onActiveChanged: if (active) w.startSystemMove() }
}
