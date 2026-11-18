import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: page
    property string orbMode: "idle"
    property bool widgetOn: false
    signal modeSelected(string mode)
    signal widgetToggled(bool on)

    gradient: Gradient {
        GradientStop { position: 0; color: "#0a1235" }
        GradientStop { position: 1; color: "#050a1f" }
    }

    readonly property var states: [
        { m: "idle", t: "IDLE", d1: "Presencia tranquila.", d2: "Siempre ahí.", c: "#7aa2ff" },
        { m: "listening", t: "LISTENING", d1: "Te escucha.", d2: "Se activa el entorno.", c: "#19e0b8" },
        { m: "processing", t: "PROCESSING", d1: "Analiza y piensa.", d2: "Conecta la información.", c: "#ffb347" },
        { m: "responding", t: "RESPONDING", d1: "Te habla.", d2: "La voz de NOVA.", c: "#5ab6ff" },
        { m: "error", t: "ERROR", d1: "Algo no está bien.", d2: "Te avisa.", c: "#ff5a78" }
    ]

    NText { x: 30; y: 40; text: "Configuración"; font.pixelSize: 24; font.bold: true }
    NText { x: 30; y: 74; text: "Voz, orbe y estados."; color: Theme.accentSoft; font.pixelSize: 12 }

    Flickable {
        id: flick
        anchors { fill: parent; topMargin: 110 }
        contentWidth: width
        contentHeight: content.height + 30
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { }

        Column {
            id: content
            x: 30
            width: flick.width - 60
            spacing: 16

            // ---- Estados del orbe (vista previa de 4 s) ----
            Card {
                width: parent.width
                height: 280
                RowLayout {
                    anchors { fill: parent; margins: 16 }
                    spacing: 10
                    Repeater {
                        model: page.states
                        Item {
                            required property var modelData
                            Layout.fillWidth: true; Layout.fillHeight: true
                            Layout.preferredWidth: 1
                            Rectangle {
                                anchors.fill: parent; radius: 12
                                color: page.orbMode === modelData.m ? Qt.rgba(0.2, 0.3, 0.8, 0.18) : "transparent"
                                border.color: page.orbMode === modelData.m ? Theme.strokeStrong : "transparent"
                            }
                            TapHandler { onTapped: page.modeSelected(modelData.m) }
                            Orb { anchors.horizontalCenter: parent.horizontalCenter; y: 6; size: 210; mode: modelData.m }
                            Column {
                                anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 18 }
                                spacing: 3
                                NText { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.t; color: modelData.c; font.pixelSize: 13; font.bold: true }
                                NText { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.d1; font.pixelSize: 10; color: Theme.textSecondary }
                                NText { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.d2; font.pixelSize: 10; color: Theme.textSecondary }
                            }
                        }
                    }
                }
            }

            // ---- Orbe permanente ----
            Card {
                width: parent.width
                height: 80
                Column {
                    x: 20; anchors.verticalCenter: parent.verticalCenter; spacing: 4
                    NText { text: "Orbe permanente"; font.pixelSize: 14; font.bold: true }
                    NText { text: "Flota sobre el escritorio y refleja el estado de NOVA."; font.pixelSize: 10; color: Theme.textSecondary }
                }
                Switch {
                    anchors { right: parent.right; rightMargin: 20; verticalCenter: parent.verticalCenter }
                    checked: page.widgetOn
                    onToggled: page.widgetToggled(checked)
                }
            }

            // ---- Voz ----
            Card {
                width: parent.width
                height: voiceCol.implicitHeight + 36
                Column {
                    id: voiceCol
                    x: 20; y: 18
                    width: parent.width - 40
                    spacing: 14

                    RowLayout {
                        width: parent.width
                        Column {
                            Layout.fillWidth: true
                            spacing: 4
                            NText { text: "Voz de NOVA"; font.pixelSize: 14; font.bold: true }
                            NText { text: novaBridge.voiceStatus; font.pixelSize: 10; color: Theme.textSecondary }
                        }
                        Switch { checked: novaBridge.voiceEnabled; onToggled: novaBridge.set_voice_enabled(checked) }
                    }

                    Row {
                        spacing: 8
                        NText { anchors.verticalCenter: parent.verticalCenter; width: 90; text: "Identidad"; font.pixelSize: 12; color: Theme.textSecondary }
                        Chip { label: "Atlas · voz masculina"; active: novaBridge.voiceIdentity === "atlas"; onClicked: novaBridge.set_voice_identity("atlas") }
                        Chip { label: "Asti · voz femenina"; active: novaBridge.voiceIdentity === "asti"; onClicked: novaBridge.set_voice_identity("asti") }
                    }

                    RowLayout {
                        width: parent.width
                        Column {
                            Layout.fillWidth: true
                            spacing: 4
                            NText { text: "Voz en línea (Edge)"; font.pixelSize: 13 }
                            NText { width: parent.width; text: "Más natural. Envía el texto de la respuesta a Microsoft. Si falla, usa Piper."; font.pixelSize: 10; color: Theme.textSecondary; wrapMode: Text.Wrap }
                        }
                        Switch { checked: novaBridge.voiceOnline; onToggled: novaBridge.set_online_voice(checked) }
                    }

                    Chip { label: "Probar voz"; onClicked: novaBridge.test_voice() }
                }
            }
        }
    }
}