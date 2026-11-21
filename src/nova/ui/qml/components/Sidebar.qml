import QtQuick

Rectangle {
    id: bar
    property int current: 0
    property string orbMode: "idle"
    color: "#060b25"

    readonly property var items: [
        { icon: "home",   label: "Inicio" },
        { icon: "chat",   label: "Conversación" },
        { icon: "memory", label: "Memoria" },
        { icon: "folder", label: "Proyectos" },
        { icon: "chart",  label: "Dashboard" },
        { icon: "gear",   label: "Configuración" }
    ]

    Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: "#1b2d6e" }

    Row {
        x: 12; y: 14
        spacing: 4
        Orb { size: 50; mode: "idle" }
        NText { anchors.verticalCenter: parent.verticalCenter; text: "NOVA"; font.pixelSize: 19; font.letterSpacing: 1.5 }
    }

    Column {
        y: 92
        x: 12
        width: parent.width - 24
        spacing: 6
        Repeater {
            model: bar.items
            Rectangle {
                id: nav
                required property int index
                required property var modelData
                property bool active: bar.current === index
                width: parent.width
                height: 42
                radius: 10
                border.width: active ? 1 : 0
                border.color: "#7f9bff"
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: nav.active ? "#2447e6" : (navHover.hovered ? "#101d4c" : "transparent") }
                    GradientStop { position: 1; color: nav.active ? "#3b63ff" : (navHover.hovered ? "#0c1740" : "transparent") }
                }
                HoverHandler { id: navHover }
                TapHandler { onTapped: bar.current = nav.index }
                Image {
                    x: 14; anchors.verticalCenter: parent.verticalCenter
                    width: 20; height: 20
                    sourceSize: Qt.size(40, 40)
                    source: Qt.resolvedUrl("../../assets/icons/" + nav.modelData.icon + (nav.active ? "_w" : "_d") + ".svg")
                }
                NText {
                    x: 46; anchors.verticalCenter: parent.verticalCenter
                    text: nav.modelData.label
                    font.pixelSize: 14
                    color: nav.active ? "white" : "#b9c8f5"
                }
            }
        }
    }

    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 12 }
        height: 54
        radius: 12
        color: "#0a1438"
        border.color: "#1b2d6e"
        Row {
            anchors.verticalCenter: parent.verticalCenter
            x: 8
            spacing: 4
            Orb { size: 46; mode: bar.orbMode }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                NText { text: "NOVA"; font.pixelSize: 13; font.bold: true }
                NText { text: "Tu asistente personal"; font.pixelSize: 10; color: "#9db4f0" }
            }
        }
    }
}
