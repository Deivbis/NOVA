import QtQuick
Rectangle {
    id: b
    property real value: 0.5
    property color c1: "#2a6bff"
    property color c2: "#35d6ff"
    height: 6
    radius: height / 2
    color: Qt.rgba(0.2, 0.3, 0.7, 0.25)
    Rectangle {
        width: parent.width * Math.max(0, Math.min(1, b.value))
        height: parent.height
        radius: height / 2
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: b.c1 }
            GradientStop { position: 1; color: b.c2 }
        }
        Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
    }
}
