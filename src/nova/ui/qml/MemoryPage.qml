import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Memoria — según la referencia 02 (Memoria)
Rectangle {
    id: page
    property string orbMode: "idle"
    property string filter: "Todo"
    color: "#050b22"

    function icon(n, v) { return Qt.resolvedUrl("../assets/icons/" + n + "_" + (v || "c") + ".svg") }

    readonly property var chips: [
        { t: "Todo", ic: "sparkle" }, { t: "Notas", ic: "note" }, { t: "Documentos", ic: "doc" },
        { t: "Conversaciones", ic: "chat" }, { t: "Ideas", ic: "bulb" }
    ]
    readonly property var categories: AppData.memoryCategories
    readonly property var recents: AppData.memoryRecents

    NText { x: 32; y: 38; text: "Memoria"; font.pixelSize: 26 }
    NText { x: 32; y: 76; text: "Tu conocimiento, siempre contigo."; color: "#2f8bff"; font.pixelSize: 13 }

    // Búsqueda y filtro
    Row {
        anchors { top: parent.top; right: parent.right; topMargin: 66; rightMargin: 32 }
        spacing: 10
        Rectangle {
            width: 240; height: 36; radius: 18
            color: Qt.rgba(0.07, 0.13, 0.34, 0.55); border.color: "#1f3f9a"
            Image { x: 13; anchors.verticalCenter: parent.verticalCenter; width: 15; height: 15; sourceSize: Qt.size(30, 30); source: page.icon("search", "d") }
            NText { x: 36; anchors.verticalCenter: parent.verticalCenter; text: "Buscar en la memoria..."; font.pixelSize: 11; color: "#6f8fe0" }
        }
        Rectangle {
            width: 36; height: 36; radius: 10
            color: Qt.rgba(0.07, 0.13, 0.34, 0.55); border.color: "#1f3f9a"
            Image { anchors.centerIn: parent; width: 16; height: 16; sourceSize: Qt.size(32, 32); source: page.icon("filter", "c") }
        }
    }

    // Chips
    Row {
        x: 32; y: 112
        spacing: 8
        Repeater {
            model: page.chips
            Chip { required property var modelData; label: modelData.t; icon: modelData.ic; active: page.filter === modelData.t; onClicked: page.filter = modelData.t }
        }
    }

    RowLayout {
        anchors { fill: parent; topMargin: 162; leftMargin: 32; rightMargin: 32; bottomMargin: 30 }
        spacing: 18

        // Columna izquierda
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 14

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: false
                Layout.preferredHeight: Math.max(180, Math.min(280, page.height * 0.33))
                Layout.maximumHeight: Layout.preferredHeight
                spacing: 14

                Card {
                    Layout.preferredWidth: 250
                    Layout.fillHeight: true
                    radius: 14
                    Gauge {
                        anchors.centerIn: parent
                        width: Math.min(parent.height - 34, 160); height: width
                        value: 0.95; thickness: 10; c1: "#3d8bff"; c2: "#8a5cff"
                        Column {
                            anchors.centerIn: parent
                            spacing: 2
                            NText { anchors.horizontalCenter: parent.horizontalCenter; text: "95%"; font.pixelSize: 28 }
                            NText { anchors.horizontalCenter: parent.horizontalCenter; text: "Capacidad utilizada"; font.pixelSize: 8; color: "#6f8fe0" }
                            NText { anchors.horizontalCenter: parent.horizontalCenter; text: "4.75 GB / 5 GB"; font.pixelSize: 8; color: "#6f8fe0" }
                        }
                    }
                }

                GridLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    columns: 2
                    rowSpacing: 14
                    columnSpacing: 14
                    Repeater {
                        model: page.categories
                        Card {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.preferredWidth: 1
                            radius: 14
                            Rectangle {
                                x: 16; anchors.verticalCenter: parent.verticalCenter
                                width: 44; height: 44; radius: 22
                                color: Qt.rgba(0.08, 0.16, 0.45, 0.8); border.color: "#2a4fc0"
                                Image { anchors.centerIn: parent; width: 22; height: 22; sourceSize: Qt.size(44, 44); source: page.icon(modelData.ic, "c") }
                            }
                            Column {
                                x: 74; anchors.verticalCenter: parent.verticalCenter; spacing: 4
                                NText { text: modelData.t; font.pixelSize: 13 }
                                NText { text: modelData.n; font.pixelSize: 10; color: "#2f8bff" }
                            }
                        }
                    }
                }
            }

            NText { text: "Recientes"; font.pixelSize: 15; Layout.topMargin: 8 }

            Card {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 3 * 62 + 24
                radius: 14
                Column {
                    anchors { fill: parent; margins: 12 }
                    Repeater {
                        model: page.recents
                        Item {
                            required property var modelData
                            required property int index
                            width: parent.width
                            height: parent.height / 3
                            Rectangle { visible: index > 0; width: parent.width; height: 1; color: "#12296a" }
                            Rectangle {
                                x: 4; anchors.verticalCenter: parent.verticalCenter
                                width: 36; height: 36; radius: 10
                                color: "#3a2fa6"; border.color: "#6a5cff"
                                Image { anchors.centerIn: parent; width: 18; height: 18; sourceSize: Qt.size(36, 36); source: page.icon(modelData.ic, "w") }
                            }
                            Column {
                                x: 56; anchors.verticalCenter: parent.verticalCenter; spacing: 3
                                NText { text: modelData.t; font.pixelSize: 13 }
                                NText { text: modelData.s; font.pixelSize: 10; color: "#2f8bff" }
                            }
                            Rectangle {
                                anchors { right: parent.right; rightMargin: 6; verticalCenter: parent.verticalCenter }
                                width: 32; height: 32; radius: 16
                                color: Qt.rgba(0.1, 0.18, 0.5, 0.55)
                                Image { anchors.centerIn: parent; width: 16; height: 16; sourceSize: Qt.size(32, 32); source: page.icon("more", "c") }
                            }
                        }
                    }
                }
            }
        }

        // Vista rápida
        Card {
            Layout.preferredWidth: Math.max(230, Math.min(290, page.width * 0.19))
            Layout.fillHeight: true
            radius: 14
            NText { x: 22; y: 20; text: "Vista rápida"; font.pixelSize: 15 }
            Rectangle {
                id: halo
                anchors.horizontalCenter: parent.horizontalCenter
                y: 64; width: 136; height: 136; radius: 68
                color: "transparent"; border.color: "#1f4fc0"; border.width: 1
                Orb { anchors.centerIn: parent; size: 150; mode: page.orbMode }
            }
            NText {
                anchors { left: parent.left; right: parent.right; leftMargin: 26; rightMargin: 26 }
                y: halo.y + 164
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: "Tu memoria es el puente entre tus ideas y lo que puedes lograr."
                font.pixelSize: 12; color: "#7fa0f0"
            }
            Rectangle {
                anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 28 }
                width: parent.width - 56; height: 38; radius: 10
                color: "#10277a"; border.color: "#2f58d8"
                NText { anchors.centerIn: parent; text: "Gestionar memoria"; font.pixelSize: 12 }
            }
        }
    }
}
