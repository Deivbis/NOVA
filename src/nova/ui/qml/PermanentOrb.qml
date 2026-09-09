import QtQuick
import QtQuick.Window

import "components"

Window {
    id: root

    objectName: "PermanentOrb"

    width: 110
    height: 110

    visible: true

    color: "transparent"

    flags: Qt.FramelessWindowHint
         | Qt.WindowStaysOnTopHint
         | Qt.WindowDoesNotAcceptFocus
         | Qt.Tool

    x: Screen.width - width - 28
    y: Screen.height - height - 80

    NovaOrb {
        anchors.centerIn: parent

        orbState: novaBridge.orbState
        orbScale: 0.42
    }
}