import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: page
    property string orbMode: "idle"
    property bool widgetOn: false
    signal modeSelected(string mode)
    signal widgetToggled(bool on)

    property var learning: ({ available: false, enabled: false, pending: [], learned: 0 })
    property var plugins: []
    property string pluginMsg: ""
    property string nameMsg: ""

    function refresh() {
        learning = novaSettings.learningState()
        plugins = novaSettings.plugins()
    }
    function pluginAction(kind, id) {
        var r = kind === "activate" ? novaSettings.activatePlugin(id)
              : kind === "deactivate" ? novaSettings.deactivatePlugin(id)
              : novaSettings.revokePlugin(id)
        pluginMsg = r.ok ? "" : r.error
        refresh()
    }
    function saveName() {
        nameMsg = novaBridge.set_user_name(nameField.text) ? "Guardado." : "Escribe un nombre (máx. 40)."
    }

    Component.onCompleted: { refresh(); nameField.text = novaBridge.userName }
    onVisibleChanged: if (visible) refresh()
    Connections { target: novaSettings; function onChanged() { page.refresh() } }

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
    NText { x: 30; y: 74; text: "Perfil, identidad, voz, aprendizaje, plugins y orbe."; color: Theme.accentSoft; font.pixelSize: 12 }

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


            Card {
                width: parent.width
                height: 80
                Column {
                    x: 20; anchors.verticalCenter: parent.verticalCenter; spacing: 4
                    NText { text: "Orbe permanente"; font.pixelSize: 14; font.bold: true }
                    NText { text: "Misma animación y lógica, menor escala. Flota sobre el escritorio."; font.pixelSize: 10; color: Theme.textSecondary }
                }
                Switch {
                    anchors { right: parent.right; rightMargin: 20; verticalCenter: parent.verticalCenter }
                    checked: page.widgetOn
                    onToggled: page.widgetToggled(checked)
                }
            }

            Card {
                width: parent.width
                height: profCol.implicitHeight + 36
                Column {
                    id: profCol
                    x: 20; y: 18; width: parent.width - 40; spacing: 14
                    NText { text: "Perfil e identidad"; font.pixelSize: 14; font.bold: true }
                    Row {
                        spacing: 8
                        NText { anchors.verticalCenter: parent.verticalCenter; width: 90; text: "Tu nombre"; font.pixelSize: 12; color: Theme.textSecondary }
                        Rectangle {
                            width: 240; height: 36; radius: 10
                            color: "#0b1a52"; border.color: "#4a6dff"
                            TextField {
                                id: nameField
                                anchors { fill: parent; leftMargin: 6; rightMargin: 6 }
                                color: "white"; font.family: Theme.fontFamily; font.pixelSize: 13
                                maximumLength: 40
                                background: null
                                onAccepted: page.saveName()
                            }
                        }
                        Chip { label: "Guardar"; onClicked: page.saveName() }
                        NText { anchors.verticalCenter: parent.verticalCenter; text: page.nameMsg; font.pixelSize: 11; color: Theme.accentSoft }
                    }
                    Row {
                        spacing: 8
                        NText { anchors.verticalCenter: parent.verticalCenter; width: 90; text: "Personalidad"; font.pixelSize: 12; color: Theme.textSecondary }
                        Chip { label: "Atlas · masculino"; active: novaBridge.activeIdentity === "atlas"; onClicked: novaBridge.set_assistant_identity("atlas") }
                        Chip { label: "Asti · femenino"; active: novaBridge.activeIdentity === "asti"; onClicked: novaBridge.set_assistant_identity("asti") }
                    }
                    NText { width: parent.width; text: "Cambiar la personalidad también cambia la voz y conserva memoria y contexto."; font.pixelSize: 10; color: Theme.textSecondary; wrapMode: Text.Wrap }
                }
            }

            Card {
                width: parent.width
                height: learnCol.implicitHeight + 36
                Column {
                    id: learnCol
                    x: 20; y: 18; width: parent.width - 40; spacing: 12
                    RowLayout {
                        width: parent.width
                        Column {
                            Layout.fillWidth: true; spacing: 4
                            NText { text: "Aprendizaje"; font.pixelSize: 14; font.bold: true }
                            NText { text: "NOVA solo propone; nada se guarda sin tu confirmación. Aprendidos: " + page.learning.learned; font.pixelSize: 10; color: Theme.textSecondary }
                        }
                        Switch {
                            enabled: page.learning.available
                            checked: page.learning.enabled
                            onToggled: novaSettings.setLearning(checked)
                        }
                    }
                    NText { visible: page.learning.pending.length === 0; text: "Sin propuestas pendientes."; font.pixelSize: 11; color: "#6f8fe0" }
                    Repeater {
                        model: page.learning.pending
                        Rectangle {
                            id: lr
                            required property var modelData
                            width: parent.width; height: lrow.implicitHeight + 20; radius: 10
                            color: Qt.rgba(0.1, 0.18, 0.5, 0.25); border.color: "#1f3f9a"
                            RowLayout {
                                id: lrow
                                x: 14; y: 10; width: parent.width - 28; spacing: 10
                                Column {
                                    Layout.fillWidth: true; spacing: 3
                                    NText { width: parent.width; text: lr.modelData.content; font.pixelSize: 12; wrapMode: Text.Wrap }
                                    NText { text: lr.modelData.category + " · evidencia " + lr.modelData.evidence; font.pixelSize: 10; color: Theme.textSecondary }
                                }
                                Chip { label: "Confirmar"; onClicked: novaSettings.resolveCandidate(lr.modelData.id, true) }
                                Chip { label: "Rechazar"; onClicked: novaSettings.resolveCandidate(lr.modelData.id, false) }
                            }
                        }
                    }
                }
            }

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
                        NText { anchors.verticalCenter: parent.verticalCenter; width: 90; text: "Voz"; font.pixelSize: 12; color: Theme.textSecondary }
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
            Card {
                width: parent.width
                height: plugCol.implicitHeight + 36
                Column {
                    id: plugCol
                    x: 20; y: 18; width: parent.width - 40; spacing: 12
                    RowLayout {
                        width: parent.width
                        Column {
                            Layout.fillWidth: true; spacing: 4
                            NText { text: "Plugins y permisos"; font.pixelSize: 14; font.bold: true }
                            NText { text: "Un plugin solo corre con los permisos que concedes. Revocar es inmediato."; font.pixelSize: 10; color: Theme.textSecondary }
                        }
                        Chip { label: "Recargar"; onClicked: { page.pluginMsg = ""; novaSettings.reloadPlugins() } }
                    }
                    NText { visible: page.plugins.length === 0; text: "No hay plugins instalados."; font.pixelSize: 11; color: "#6f8fe0" }
                    NText { visible: page.pluginMsg !== ""; width: parent.width; text: page.pluginMsg; color: "#ff5a78"; font.pixelSize: 12; wrapMode: Text.Wrap }
                    Repeater {
                        model: page.plugins
                        Rectangle {
                            id: pr
                            required property var modelData
                            width: parent.width; height: pcol.implicitHeight + 24; radius: 10
                            color: Qt.rgba(0.1, 0.18, 0.5, 0.25); border.color: pr.modelData.enabled ? "#2fe0a0" : "#1f3f9a"
                            Column {
                                id: pcol
                                x: 14; y: 12; width: parent.width - 28; spacing: 6
                                RowLayout {
                                    width: parent.width
                                    NText { Layout.fillWidth: true; text: pr.modelData.name + (pr.modelData.version !== "" ? "  v" + pr.modelData.version : "") + (pr.modelData.author !== "" ? " · " + pr.modelData.author : ""); font.pixelSize: 13; font.bold: true }
                                    NText { text: pr.modelData.enabled ? "Activo" : "Inactivo"; font.pixelSize: 11; color: pr.modelData.enabled ? "#2fe0a0" : "#8fb0ff" }
                                }
                                NText { visible: pr.modelData.description !== ""; width: parent.width; text: pr.modelData.description; font.pixelSize: 10; color: Theme.textSecondary; wrapMode: Text.Wrap }
                                NText { visible: pr.modelData.permissions.length > 0; width: parent.width; text: "Permisos: " + pr.modelData.permissions.join(", "); font.pixelSize: 10; color: "#9db4f0"; wrapMode: Text.Wrap }
                                NText { visible: pr.modelData.network.length > 0; width: parent.width; text: "Red: " + pr.modelData.network.join(", "); font.pixelSize: 10; color: "#9db4f0"; wrapMode: Text.Wrap }
                                NText { visible: pr.modelData.error !== ""; width: parent.width; text: pr.modelData.error; font.pixelSize: 10; color: "#ff5a78"; wrapMode: Text.Wrap }
                                Row {
                                    spacing: 8
                                    Chip { visible: !pr.modelData.enabled && pr.modelData.error === ""; label: pr.modelData.granted ? "Activar" : "Conceder permisos y activar"; onClicked: page.pluginAction("activate", pr.modelData.id) }
                                    Chip { visible: pr.modelData.enabled; label: "Desactivar"; onClicked: page.pluginAction("deactivate", pr.modelData.id) }
                                    Chip { visible: pr.modelData.granted && pr.modelData.permissions.length > 0; label: "Revocar permisos"; onClicked: page.pluginAction("revoke", pr.modelData.id) }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
