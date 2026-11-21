import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Proyectos — según la referencia 03 (Proyectos)
Rectangle {
    id: page
    color: "#050b22"
    property int sel: 0
    property string query: ""
    property string statusFilter: ""
    property var projects: []
    property bool dialogOpen: false
    property string editId: ""
    property string dialogError: ""
    property string dialogStatus: "active"
    property int dialogProgress: 0
    property bool deleteArmed: false

    readonly property var stLabels: ({ active: "En progreso", paused: "En pausa", done: "Completado" })
    readonly property var stColors: ({
        active: { bg: "#0d3a8c", fg: "#4aa8ff" },
        paused: { bg: "#2a2a78", fg: "#a99bff" },
        done:   { bg: "#0c4a4c", fg: "#2fe0a0" }
    })
    readonly property var filterCycle: ["", "active", "paused", "done"]

    function icon(n, v) { return Qt.resolvedUrl("../../assets/icons/" + n + "_" + (v || "c") + ".svg") }

    function refresh() { projects = novaProjects.items(query, statusFilter) }
    function openDialog(pid) {
        editId = pid; dialogError = ""; deleteArmed = false
        nameField.text = ""; descText.text = ""; dialogStatus = "active"; dialogProgress = 0
        for (var i = 0; i < projects.length; i++) {
            if (projects[i].id === pid) {
                nameField.text = projects[i].name; descText.text = projects[i].description
                dialogStatus = projects[i].status; dialogProgress = projects[i].progress
            }
        }
        dialogOpen = true
        nameField.forceActiveFocus()
    }
    function closeDialog() { dialogOpen = false; editId = ""; deleteArmed = false }
    function saveDialog() {
        var r = editId === "" ? novaProjects.create(nameField.text, descText.text)
                              : novaProjects.update(editId, nameField.text, descText.text, dialogStatus, dialogProgress)
        if (!r.ok) { dialogError = r.error; return }
        closeDialog()
    }
    function removeProject() {
        var r = novaProjects.delete(editId)
        if (!r.ok) { dialogError = r.error; return }
        closeDialog()
    }

    Component.onCompleted: refresh()
    onVisibleChanged: if (visible) refresh()
    Connections { target: novaProjects; function onChanged() { page.refresh() } }

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

            TapHandler { onTapped: page.openDialog("") }
        }
        Rectangle {
            width: 200; height: 36; radius: 18
            color: Qt.rgba(0.07, 0.13, 0.34, 0.55);
            Image { x: 13; anchors.verticalCenter: parent.verticalCenter; width: 15; height: 15; sourceSize: Qt.size(30, 30); source: page.icon("search", "d") }
            TextField {
                x: 36; width: parent.width - 46; height: parent.height
                color: "white"; font.family: Theme.fontFamily; font.pixelSize: 11
                placeholderText: "Buscar proyectos..."; placeholderTextColor: "#6f8fe0"
                background: null
                onTextChanged: { page.query = text; page.refresh() }
            }
            border.color: page.statusFilter === "" ? "#1f3f9a" : "#4a6dff"
            TapHandler {
                onTapped: {
                    var i = page.filterCycle.indexOf(page.statusFilter)
                    page.statusFilter = page.filterCycle[(i + 1) % page.filterCycle.length]
                    page.refresh()
                }
            }
            ToolTip.visible: hh.hovered
            ToolTip.text: page.statusFilter === "" ? "Todos" : page.stLabels[page.statusFilter]
            HoverHandler { id: hh }
        }
        Rectangle {
            width: fRow.implicitWidth + 24; height: 36; radius: 18
            color: page.statusFilter === "" ? Qt.rgba(0.07, 0.13, 0.34, 0.55) : "#10277a"
            border.color: page.statusFilter === "" ? "#1f3f9a" : "#4a6dff"
            Row {
                id: fRow
                anchors.centerIn: parent; spacing: 8
                Image { anchors.verticalCenter: parent.verticalCenter; width: 16; height: 16; sourceSize: Qt.size(32, 32); source: page.icon("filter", "c") }
                NText { anchors.verticalCenter: parent.verticalCenter; text: page.statusFilter === "" ? "Todos" : page.stLabels[page.statusFilter]; font.pixelSize: 11 }
            }
            TapHandler {
                onTapped: {
                    var i = page.filterCycle.indexOf(page.statusFilter)
                    page.statusFilter = page.filterCycle[(i + 1) % page.filterCycle.length]
                    page.refresh()
                }
            }
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
                enabled: !page.dialogOpen
                highlighted: page.sel === index
                onClicked: { page.sel = index; page.openDialog(modelData.id) }

                Image {
                    id: ban
                    x: 8; y: 8
                    width: parent.width - 16
                    height: width / 2.88
                    source: Qt.resolvedUrl("../../assets/banners/proj_" + card.modelData.banner + ".png")
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
                        NText { anchors.verticalCenter: parent.verticalCenter; text: card.modelData.name; font.pixelSize: 13; font.bold: true }
                    }
                    NText { width: parent.width; text: card.modelData.description; font.pixelSize: 11; color: "#6f8fe0"; elide: Text.ElideRight }
                    Rectangle {
                        width: stLbl.implicitWidth + 18; height: 20; radius: 10
                        color: page.stColors[card.modelData.status].bg
                        NText { id: stLbl; anchors.centerIn: parent; text: page.stLabels[card.modelData.status]; font.pixelSize: 9; color: page.stColors[card.modelData.status].fg }
                    }
                }

                Item {
                    anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 16; rightMargin: 16; bottomMargin: 14 }
                    height: 16
                    NovaBar {
                        anchors {
                            left: parent.left
                            right: pct.left
                            rightMargin: 10
                            verticalCenter: parent.verticalCenter
                        }
                        value: card.modelData.progress / 100
                        c1: card.modelData.progress === 100 ? "#2fe0a0" : "#2a6bff"
                        c2: card.modelData.progress === 100 ? "#35d6a0" : "#35d6ff"
                    }
                    NText { id: pct; anchors { right: parent.right; verticalCenter: parent.verticalCenter } text: card.modelData.progress + "%"; font.pixelSize: 10; color: "#8fb0ff" }
                }
            }
        }
    }
    NText {
        visible: page.projects.length === 0
        anchors.centerIn: parent
        text: (page.query !== "" || page.statusFilter !== "") ? "Sin resultados." : "Aún no tienes proyectos. Crea el primero."
        color: "#6f8fe0"; font.pixelSize: 14
    }

    Rectangle {
        anchors.fill: parent
        z: 200
        visible: page.dialogOpen
        color: Qt.rgba(0.0, 0.01, 0.06, 0.62)
        MouseArea { anchors.fill: parent; onClicked: page.closeDialog() }

        Rectangle {
            anchors.centerIn: parent
            width: Math.min(560, page.width - 80)
            height: dlg.implicitHeight + 48
            radius: 16
            color: "#08123a"; border.color: "#2a4fc0"
            MouseArea { anchors.fill: parent }
            Column {
                id: dlg
                x: 24; y: 24
                width: parent.width - 48
                spacing: 14
                NText { text: page.editId === "" ? "Nuevo proyecto" : "Editar proyecto"; font.pixelSize: 17 }
                Rectangle {
                    width: parent.width; height: 40; radius: 10
                    color: "#0b1a52"; border.color: "#4a6dff"
                    TextField {
                        id: nameField
                        anchors { fill: parent; leftMargin: 6; rightMargin: 6 }
                        color: "white"; font.family: Theme.fontFamily; font.pixelSize: 13
                        placeholderText: "Nombre del proyecto"; placeholderTextColor: "#6f8fe0"
                        maximumLength: novaProjects.maxName
                        background: null
                    }
                }
                Rectangle {
                    width: parent.width; height: 84; radius: 10
                    color: "#0b1a52"; border.color: "#4a6dff"
                    ScrollView {
                        anchors { fill: parent; margins: 6 }
                        TextArea {
                            id: descText
                            color: "white"; font.family: Theme.fontFamily; font.pixelSize: 13
                            wrapMode: TextEdit.Wrap
                            placeholderText: "Descripción (opcional)"; placeholderTextColor: "#6f8fe0"
                            background: null
                            onTextChanged: if (length > novaProjects.maxDescription) remove(novaProjects.maxDescription, length)
                        }
                    }
                }
                Row {
                    spacing: 6
                    Repeater {
                        model: ["active", "paused", "done"]
                        Chip {
                            required property string modelData
                            label: page.stLabels[modelData]
                            active: page.dialogStatus === modelData
                            onClicked: { page.dialogStatus = modelData; if (modelData === "done") page.dialogProgress = 100 }
                        }
                    }
                }
                Row {
                    width: parent.width; spacing: 10
                    Slider {
                        id: prog
                        width: parent.width - 50; from: 0; to: 100; stepSize: 5
                        enabled: page.dialogStatus !== "done"
                        value: page.dialogProgress
                        onMoved: page.dialogProgress = Math.round(value)
                    }
                    NText { anchors.verticalCenter: parent.verticalCenter; text: page.dialogProgress + "%"; font.pixelSize: 12; color: "#8fb0ff" }
                }
                NText { visible: page.dialogError !== ""; width: parent.width; text: page.dialogError; color: "#ff5a78"; font.pixelSize: 12; wrapMode: Text.Wrap }
                Item {
                    width: parent.width; height: 38
                    Rectangle {
                        visible: page.editId !== ""
                        width: 130; height: 38; radius: 10
                        color: page.deleteArmed ? "#7a1030" : Qt.rgba(0.1, 0.18, 0.5, 0.55)
                        border.color: "#ff5a78"
                        NText { anchors.centerIn: parent; text: page.deleteArmed ? "¿Seguro? Borrar" : "Eliminar"; font.pixelSize: 12; color: "#ff8aa0" }
                        TapHandler { onTapped: page.deleteArmed ? page.removeProject() : page.deleteArmed = true }
                    }
                    Row {
                        anchors.right: parent.right; spacing: 10
                        Rectangle {
                            width: 110; height: 38; radius: 10
                            color: Qt.rgba(0.1, 0.18, 0.5, 0.55); border.color: "#2a4fc0"
                            NText { anchors.centerIn: parent; text: "Cancelar"; font.pixelSize: 12 }
                            TapHandler { onTapped: page.closeDialog() }
                        }
                        Rectangle {
                            width: 110; height: 38; radius: 10
                            color: "#10277a"; border.color: "#2f58d8"
                            opacity: nameField.text.trim() !== "" ? 1.0 : 0.5
                            NText { anchors.centerIn: parent; text: "Guardar"; font.pixelSize: 12 }
                            TapHandler { onTapped: if (nameField.text.trim() !== "") page.saveDialog() }
                        }
                    }
                }
            }
        }
    }
}
