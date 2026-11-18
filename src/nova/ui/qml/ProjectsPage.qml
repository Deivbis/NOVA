import QtQuick
import QtQuick.Layouts

// Proyectos — según la referencia 03 (Proyectos)
Rectangle {
    id: page
    color: "#050b22"
    property int sel: 0

    function icon(n, v) { return Qt.resolvedUrl("../assets/icons/" + n + "_" + (v || "c") + ".svg") }

    readonly property var projects: AppData.projects
    readonly property var stColors: ({
        "En progreso": { bg: "#0d3a8c", fg: "#4aa8ff" },
        "En pausa":    { bg: "#2a2a78", fg: "#a99bff" },
        "Completado":  { bg: "#0c4a4c", fg: "#2fe0a0" }
    })

    NText { x: 32; y: 38; text: "Proyectos"; font.pixelSize: 26 }
    NText { x: 32; y: 76; text: "Organiza, avanza, crea."; color: "#2f8bff"; font.pixelSize: 13 }

    Row {
        anchors { top: parent.top; right: parent.right; topMargin: 56; rightMargin: 32 }
        spacing: 10
        Rectangle {
            width: 150; height: 36; radius: 18
            border.color: "#5b7bff"
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: "#2447e6" }
                GradientStop { position: 1; color: "#3b63ff" }
            }
            Row {
                anchors.centerIn: parent; spacing: 8
                Image { anchors.verticalCenter: parent.verticalCenter; width: 14; height: 14; sourceSize: Qt.size(28, 28); source: page.icon("plus", "w") }
                NText { anchors.verticalCenter: parent.verticalCenter; text: "Nuevo proyecto"; font.pixelSize: 12 }
            }
        }
        Rectangle {
            width: 200; height: 36; radius: 18
            color: Qt.rgba(0.07, 0.13, 0.34, 0.55); border.color: "#1f3f9a"
            Image { x: 13; anchors.verticalCenter: parent.verticalCenter; width: 15; height: 15; sourceSize: Qt.size(30, 30); source: page.icon("search", "d") }
            NText { x: 36; anchors.verticalCenter: parent.verticalCenter; text: "Buscar proyectos..."; font.pixelSize: 11; color: "#6f8fe0" }
        }
        Rectangle {
            width: 36; height: 36; radius: 10
            color: Qt.rgba(0.07, 0.13, 0.34, 0.55); border.color: "#1f3f9a"
            Image { anchors.centerIn: parent; width: 16; height: 16; sourceSize: Qt.size(32, 32); source: page.icon("filter", "c") }
        }
    }

    GridLayout {
        anchors { fill: parent; topMargin: 112; leftMargin: 32; rightMargin: 32; bottomMargin: 30 }
        columns: 3
        rowSpacing: 16
        columnSpacing: 16

        Repeater {
            model: page.projects
            Card {
                id: card
                required property var modelData
                required property int index
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                Layout.preferredHeight: 1
                radius: 14
                highlighted: page.sel === index
                onClicked: page.sel = index

                Image {
                    id: ban
                    x: 8; y: 8
                    width: parent.width - 16
                    height: width / 2.88
                    source: Qt.resolvedUrl("../assets/banners/proj_" + (card.index + 1) + ".png")
                    smooth: true
                }
                Image {
                    anchors { top: ban.top; right: ban.right; topMargin: 9; rightMargin: 9 }
                    width: 16; height: 16; sourceSize: Qt.size(32, 32)
                    source: page.icon("morev", "w")
                }

                Column {
                    anchors { left: parent.left; right: parent.right; top: ban.bottom; leftMargin: 16; rightMargin: 16; topMargin: 12 }
                    spacing: 6
                    Row {
                        spacing: 8
                        Rectangle {
                            width: 20; height: 20; radius: 6
                            color: "#2a2a8a"; border.color: "#5b5cff"
                            Image { anchors.centerIn: parent; width: 12; height: 12; sourceSize: Qt.size(24, 24); source: page.icon("proj", "c") }
                        }
                        NText { anchors.verticalCenter: parent.verticalCenter; text: card.modelData.t; font.pixelSize: 13; font.bold: true }
                    }
                    NText { width: parent.width; text: card.modelData.d; font.pixelSize: 11; color: "#6f8fe0"; elide: Text.ElideRight }
                    Rectangle {
                        width: stLbl.implicitWidth + 18; height: 20; radius: 10
                        color: page.stColors[card.modelData.st].bg
                        NText { id: stLbl; anchors.centerIn: parent; text: card.modelData.st; font.pixelSize: 9; color: page.stColors[card.modelData.st].fg }
                    }
                }

                Item {
                    anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 16; rightMargin: 16; bottomMargin: 14 }
                    height: 16
                    NovaBar {
                        anchors { left: parent.left; right: pct.left; rightMargin: 10; verticalCenter: parent.verticalCenter }
                        value: card.modelData.p / 100
                        c1: card.modelData.p === 100 ? "#7a4dff" : "#2a6bff"
                        c2: card.modelData.p === 100 ? "#a96bff" : "#35d6ff"
                    }
                    NText { id: pct; anchors { right: parent.right; verticalCenter: parent.verticalCenter } text: card.modelData.p + "%"; font.pixelSize: 10; color: "#8fb0ff" }
                }
            }
        }
    }
}
