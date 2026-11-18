import QtQuick
import QtQuick.Window

Window {
    id: root
    objectName: "PermanentOrb"

    readonly property int orbSize: 90
    readonly property int box: Math.round(orbSize * Theme.orbScale) + 6

    width: box
    height: box
    visible: novaBridge.permanentOrbEnabled
    color: "transparent"
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowDoesNotAcceptFocus | Qt.Tool
    x: Screen.width - width - 28
    y: Screen.height - height - 80

    Orb { anchors.centerIn: parent; size: root.orbSize; mode: novaBridge.orbState }
}