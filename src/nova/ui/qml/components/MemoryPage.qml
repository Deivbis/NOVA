import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Memoria — según la referencia 02 (Memoria). Datos reales vía novaMemory (SQLite).
Rectangle {
    id: page
    property string orbMode: "idle"
    property string filter: "Todo"          // Todo | <categoría> | Aprendido | Olvidados
    property string query: ""
    property bool newestFirst: true
    property string selectedId: ""
    property var selected: null
    property var overview: ({ total: 0, learned: 0, forgotten: 0, categories: [] })
    property string notice: ""
    property bool dialogOpen: false         // diálogo crear / editar
    property string editId: ""
    property string dialogCategory: ""
    property string dialogError: ""
    property string purgeId: ""             // recuerdo pendiente de borrado definitivo
    color: "#050b22"

    function icon(n, v) { return Qt.resolvedUrl("../../assets/icons/" + n + "_" + (v || "c") + ".svg") }

    readonly property var catIcons: ({
        "Programación": "cpu", "Juegos": "sparkle", "Música": "speaker", "Trabajo": "folder",
        "Estudios": "doc", "Salud": "check", "Rutinas": "clock", "Familia": "home",
        "Amigos": "chat", "Proyectos": "proj", "General": "note"
    })

    function notify(t) { notice = t; noticeTimer.restart() }

    // ---- datos ----
    function rebuildChips() {
        chipsModel.clear()
        chipsModel.append({ t: "Todo", ic: "sparkle" })
        var cats = overview.categories
        for (var i = 0; i < cats.length; i++)
            chipsModel.append({ t: cats[i].name, ic: catIcons[cats[i].name] || "note" })
        if (overview.learned > 0) chipsModel.append({ t: "Aprendido", ic: "bulb" })
        if (overview.forgotten > 0) chipsModel.append({ t: "Olvidados", ic: "trash" })
    }
    function refresh() {
        overview = novaMemory.overview()
        rebuildChips()
        var valid = false
        for (var c = 0; c < chipsModel.count; c++) if (chipsModel.get(c).t === filter) valid = true
        if (!valid) filter = "Todo"

        var view = filter === "Olvidados" ? "forgotten" : (filter === "Aprendido" ? "learned" : "active")
        var cat = (filter === "Todo" || filter === "Olvidados" || filter === "Aprendido") ? "" : filter
        var list = novaMemory.search(query, cat, view, newestFirst)
        memModel.clear()
        for (var i = 0; i < list.length; i++)
            memModel.append({ mid: list[i].id, content: list[i].content, category: list[i].category,
                              source: list[i].source, sourceLabel: list[i].sourceLabel, active: list[i].active,
                              time: list[i].time, created: list[i].created, updated: list[i].updated })
        if (selectedId !== "") select(selectedId)
    }
    function select(mid) {
        selectedId = mid
        selected = null
        for (var i = 0; i < memModel.count; i++) {
            var o = memModel.get(i)
            if (o.mid === mid) {
                selected = { mid: o.mid, content: o.content, category: o.category, source: o.source,
                             sourceLabel: o.sourceLabel, active: o.active, created: o.created, updated: o.updated }
                return
            }
        }
        selectedId = ""
    }
    function clearSelection() { selectedId = ""; selected = null }

    // ---- acciones sobre el recuerdo seleccionado ----
    function actionsFor(s) {
        if (!s) return []
        return s.active ? [ { t: "Editar", k: "edit" }, { t: "Olvidar", k: "forget" } ]
                        : [ { t: "Reactivar", k: "reactivate" }, { t: "Borrar", k: "purge" } ]
    }
    function act(k) {
        if (!selected) return
        if (k === "edit") { openDialog(selected.mid); return }
        if (k === "purge") { purgeId = selected.mid; return }
        var r = k === "forget" ? novaMemory.forget(selected.mid) : novaMemory.reactivate(selected.mid)
        if (!r.ok) notify(r.error)
        else notify(k === "forget" ? "Olvidado. Puedes reactivarlo en «Olvidados»." : "Recuerdo reactivado.")
    }
    function confirmPurge() {
        var r = novaMemory.purge(purgeId)
        purgeId = ""
        notify(r.ok ? "Recuerdo borrado definitivamente." : r.error)
    }

    // ---- diálogo crear / editar ----
    function openDialog(mid) {
        editId = mid
        dialogError = ""
        dialogCategory = ""
        memText.text = ""
        if (mid !== "") {
            for (var i = 0; i < memModel.count; i++) {
                var o = memModel.get(i)
                if (o.mid === mid) { memText.text = o.content; dialogCategory = o.category }
            }
        }
        dialogOpen = true
        memText.forceActiveFocus()
    }
    function closeDialog() { dialogOpen = false; editId = "" }
    function saveDialog() {
        var wasEdit = editId !== ""
        var r = wasEdit ? novaMemory.update(editId, memText.text, dialogCategory)
                        : novaMemory.add(memText.text, dialogCategory)
        if (!r.ok) { dialogError = r.error; return }
        closeDialog()
        if (!wasEdit) { searchField.text = ""; filter = "Todo" }
        refresh()
        select(r.id)
        notify(wasEdit ? "Recuerdo actualizado." : "Recuerdo guardado.")
    }

    ListModel { id: chipsModel }
    ListModel { id: memModel }

    Component.onCompleted: refresh()
    onVisibleChanged: if (visible) refresh()

    Connections {
        target: novaBridge
        function onConversationChanged() { if (page.visible) page.refresh() }   // órdenes por chat o voz
    }
    Connections {
        target: novaMemory
        function onChanged() { if (page.visible) page.refresh() }
    }
    Timer { id: noticeTimer; interval: 3500; onTriggered: page.notice = "" }

    NText { x: 32; y: 38; text: "Memoria"; font.pixelSize: 26 }
    NText {
        x: 32; y: 76
        text: page.notice !== "" ? page.notice : "Tu conocimiento, siempre contigo."
        color: page.notice !== "" ? "#ffb347" : "#2f8bff"
        font.pixelSize: 13
    }

    // Búsqueda y orden
    Row {
        anchors { top: parent.top; right: parent.right; topMargin: 66; rightMargin: 32 }
        spacing: 10
        Rectangle {
            width: 240; height: 36; radius: 18
            color: Qt.rgba(0.07, 0.13, 0.34, 0.55); border.color: "#1f3f9a"
            Image { x: 13; anchors.verticalCenter: parent.verticalCenter; width: 15; height: 15; sourceSize: Qt.size(30, 30); source: page.icon("search", "d") }
            TextField {
                id: searchField
                anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; leftMargin: 36; rightMargin: 12 }
                placeholderText: "Buscar en la memoria..."
                placeholderTextColor: "#6f8fe0"
                color: "white"
                font.family: Theme.fontFamily
                font.pixelSize: 11
                background: null
                onTextChanged: { page.query = text; page.refresh() }
            }
        }
        Rectangle {
            width: 36; height: 36; radius: 10
            color: page.newestFirst ? Qt.rgba(0.07, 0.13, 0.34, 0.55) : "#1f4fd8"
            border.color: page.newestFirst ? "#1f3f9a" : "#4a7bff"
            Image { anchors.centerIn: parent; width: 16; height: 16; sourceSize: Qt.size(32, 32); source: page.icon("filter", page.newestFirst ? "c" : "w") }
            TapHandler {
                onTapped: {
                    page.newestFirst = !page.newestFirst
                    page.notify(page.newestFirst ? "Orden: más recientes primero." : "Orden: más antiguos primero.")
                    page.refresh()
                }
            }
        }
    }

    // Chips de filtro (categorías con recuerdos)
    Flickable {
        x: 32; y: 112
        width: parent.width - 64; height: 28
        contentWidth: chipRow.width
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        Row {
            id: chipRow
            spacing: 8
            Repeater {
                model: chipsModel
                Chip {
                    required property string t
                    required property string ic
                    label: t; icon: ic
                    active: page.filter === t
                    onClicked: { page.filter = t; page.refresh() }
                }
            }
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
                        value: page.overview.total > 0 ? page.overview.learned / page.overview.total : 0
                        thickness: 10; c1: "#3d8bff"; c2: "#8a5cff"
                        Column {
                            anchors.centerIn: parent
                            spacing: 2
                            NText { anchors.horizontalCenter: parent.horizontalCenter; text: page.overview.total; font.pixelSize: 28 }
                            NText { anchors.horizontalCenter: parent.horizontalCenter; text: "Recuerdos activos"; font.pixelSize: 8; color: "#6f8fe0" }
                            NText { anchors.horizontalCenter: parent.horizontalCenter; text: page.overview.learned + " aprendidos por NOVA"; font.pixelSize: 8; color: "#6f8fe0" }
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
                        model: page.overview.categories.slice(0, 4)
                        Card {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.preferredWidth: 1
                            radius: 14
                            highlighted: page.filter === modelData.name
                            onClicked: { page.filter = modelData.name; page.refresh() }
                            Rectangle {
                                x: 16; anchors.verticalCenter: parent.verticalCenter
                                width: 44; height: 44; radius: 22
                                color: Qt.rgba(0.08, 0.16, 0.45, 0.8); border.color: "#2a4fc0"
                                Image { anchors.centerIn: parent; width: 22; height: 22; sourceSize: Qt.size(44, 44); source: page.icon(page.catIcons[modelData.name] || "note", "c") }
                            }
                            Column {
                                x: 74; anchors.verticalCenter: parent.verticalCenter; spacing: 4
                                NText { text: modelData.name; font.pixelSize: 13 }
                                NText { text: modelData.count + (modelData.count === 1 ? " recuerdo" : " recuerdos"); font.pixelSize: 10; color: "#2f8bff" }
                            }
                        }
                    }
                }
            }

            NText {
                text: page.filter === "Todo" && page.query === "" ? "Recientes" : "Resultados (" + memModel.count + ")"
                font.pixelSize: 15; Layout.topMargin: 8
            }

            Card {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 3 * 62 + 24
                radius: 14

                ListView {
                    id: memList
                    anchors { fill: parent; margins: 12 }
                    model: memModel
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.vertical: ScrollBar { }

                    delegate: Item {
                        id: row
                        required property int index
                        required property string mid
                        required property string content
                        required property string category
                        required property string source
                        required property bool active
                        required property string time
                        readonly property bool picked: page.selectedId === mid

                        width: ListView.view.width
                        height: 62

                        Rectangle { visible: row.index > 0; width: parent.width; height: 1; color: "#12296a" }
                        Rectangle { anchors.fill: parent; anchors.margins: 2; radius: 10; visible: row.picked; color: Qt.rgba(0.14, 0.26, 0.78, 0.22); border.color: "#4a6dff" }
                        TapHandler { onTapped: page.select(row.mid) }

                        Rectangle {
                            x: 8; anchors.verticalCenter: parent.verticalCenter
                            width: 36; height: 36; radius: 10
                            color: row.active ? "#3a2fa6" : "#27305a"; border.color: row.active ? "#6a5cff" : "#3a4a8a"
                            Image { anchors.centerIn: parent; width: 18; height: 18; sourceSize: Qt.size(36, 36); source: page.icon(page.catIcons[row.category] || "note", "w") }
                        }
                        Column {
                            x: 60; anchors.verticalCenter: parent.verticalCenter
                            width: row.width - 60 - 48
                            spacing: 3
                            NText { width: parent.width; text: row.content; font.pixelSize: 13; elide: Text.ElideRight; opacity: row.active ? 1.0 : 0.6 }
                            NText {
                                width: parent.width
                                text: row.category + " · " + row.time + (row.source === "learned" ? " · aprendido" : "") + (row.active ? "" : " · olvidado")
                                font.pixelSize: 10; color: "#2f8bff"; elide: Text.ElideRight
                            }
                        }
                        Rectangle {
                            anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                            width: 32; height: 32; radius: 16
                            color: Qt.rgba(0.1, 0.18, 0.5, 0.55)
                            Image { anchors.centerIn: parent; width: 16; height: 16; sourceSize: Qt.size(32, 32); source: page.icon("more", "c") }
                            TapHandler { onTapped: page.select(row.mid) }
                        }
                    }
                }

                Column {
                    visible: memModel.count === 0
                    anchors.centerIn: parent
                    spacing: 6
                    NText { anchors.horizontalCenter: parent.horizontalCenter; text: page.query !== "" ? "Sin resultados." : "No hay recuerdos aquí todavía."; font.pixelSize: 14 }
                    NText { anchors.horizontalCenter: parent.horizontalCenter; text: "Di «recuerda que…» o pulsa Nuevo recuerdo."; font.pixelSize: 11; color: "#6f8fe0" }
                }
            }
        }

        // Vista rápida
        Card {
            Layout.preferredWidth: Math.max(230, Math.min(290, page.width * 0.19))
            Layout.fillHeight: true
            radius: 14
            NText { x: 22; y: 20; text: "Vista rápida"; font.pixelSize: 15 }

            Rectangle {   // cerrar el detalle
                visible: page.selected !== null
                anchors { top: parent.top; right: parent.right; topMargin: 16; rightMargin: 16 }
                width: 28; height: 28; radius: 14
                color: Qt.rgba(0.1, 0.18, 0.5, 0.55)
                Image { anchors.centerIn: parent; width: 14; height: 14; sourceSize: Qt.size(28, 28); source: page.icon("close", "c") }
                TapHandler { onTapped: page.clearSelection() }
            }

            // Sin selección: el orbe y la frase del diseño
            Item {
                visible: page.selected === null
                anchors.fill: parent
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
            }

            // Con selección: detalle del recuerdo
            Item {
                visible: page.selected !== null
                anchors { fill: parent; topMargin: 58; leftMargin: 22; rightMargin: 22; bottomMargin: 128 }
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 10
                    Row {
                        spacing: 8
                        Rectangle {
                            width: catLbl.implicitWidth + 22; height: 24; radius: 12
                            color: "#1f4fd8"; border.color: "#4a7bff"
                            NText { id: catLbl; anchors.centerIn: parent; text: page.selected ? page.selected.category : ""; font.pixelSize: 11 }
                        }
                        Rectangle {
                            visible: page.selected !== null && !page.selected.active
                            width: oldLbl.implicitWidth + 22; height: 24; radius: 12
                            color: "#5a3a10"; border.color: "#ffb347"
                            NText { id: oldLbl; anchors.centerIn: parent; text: "Olvidado"; font.pixelSize: 11 }
                        }
                    }
                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentHeight: detailText.height
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        NText {
                            id: detailText
                            width: parent.width
                            text: page.selected ? page.selected.content : ""
                            wrapMode: Text.Wrap
                            font.pixelSize: 13
                            lineHeight: 1.15
                        }
                    }
                    NText { text: page.selected ? page.selected.sourceLabel : ""; font.pixelSize: 10; color: "#7fa0f0" }
                    NText { text: page.selected ? "Creado: " + page.selected.created : ""; font.pixelSize: 10; color: "#6f8fe0" }
                    NText { text: page.selected ? "Modificado: " + page.selected.updated : ""; font.pixelSize: 10; color: "#6f8fe0" }
                }
            }

            RowLayout {   // acciones del detalle
                visible: page.selected !== null
                anchors { left: parent.left; right: parent.right; bottom: parent.bottom; leftMargin: 22; rightMargin: 22; bottomMargin: 78 }
                spacing: 8
                Repeater {
                    model: page.actionsFor(page.selected)
                    Rectangle {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 34
                        radius: 10
                        color: modelData.k === "purge" ? "#b3203f" : Qt.rgba(0.1, 0.18, 0.5, 0.55)
                        border.color: modelData.k === "purge" ? "#ff5a78" : "#2a4fc0"
                        NText { anchors.centerIn: parent; text: modelData.t; font.pixelSize: 12 }
                        TapHandler { onTapped: page.act(modelData.k) }
                    }
                }
            }

            Rectangle {
                anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 28 }
                width: parent.width - 56; height: 38; radius: 10
                color: "#10277a"; border.color: "#2f58d8"
                NText { anchors.centerIn: parent; text: "Nuevo recuerdo"; font.pixelSize: 12 }
                TapHandler { onTapped: page.openDialog("") }
            }
        }
    }

    // =====================================================================
    //  Diálogo: nuevo / editar recuerdo
    // =====================================================================
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
            MouseArea { anchors.fill: parent }       // evita cerrar al pulsar dentro
            Column {
                id: dlg
                x: 24; y: 24
                width: parent.width - 48
                spacing: 14
                NText { text: page.editId === "" ? "Nuevo recuerdo" : "Editar recuerdo"; font.pixelSize: 17 }
                Rectangle {
                    width: parent.width; height: 110; radius: 10
                    color: "#0b1a52"; border.color: "#4a6dff"
                    ScrollView {
                        anchors { fill: parent; margins: 6 }
                        TextArea {
                            id: memText
                            color: "white"
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            wrapMode: TextEdit.Wrap
                            placeholderText: "Escribe lo que NOVA debe recordar..."
                            placeholderTextColor: "#6f8fe0"
                            background: null
                            onTextChanged: if (length > novaMemory.maxChars) remove(novaMemory.maxChars, length)
                        }
                    }
                }
                NText { width: parent.width; horizontalAlignment: Text.AlignRight; text: memText.length + " / " + novaMemory.maxChars; font.pixelSize: 10; color: "#6f8fe0" }
                NText { text: "Categoría"; font.pixelSize: 12; color: "#9db4f0" }
                Flow {
                    width: parent.width
                    spacing: 6
                    Chip { label: page.editId === "" ? "Automática" : "Mantener"; active: page.dialogCategory === ""; onClicked: page.dialogCategory = "" }
                    Repeater {
                        model: novaMemory.categories
                        Chip {
                            required property string modelData
                            label: modelData
                            active: page.dialogCategory === modelData
                            onClicked: page.dialogCategory = modelData
                        }
                    }
                }
                NText { visible: page.dialogError !== ""; width: parent.width; text: page.dialogError; color: "#ff5a78"; font.pixelSize: 12; wrapMode: Text.Wrap }
                Row {
                    anchors.right: parent.right
                    spacing: 10
                    Rectangle {
                        width: 110; height: 38; radius: 10
                        color: Qt.rgba(0.1, 0.18, 0.5, 0.55); border.color: "#2a4fc0"
                        NText { anchors.centerIn: parent; text: "Cancelar"; font.pixelSize: 12 }
                        TapHandler { onTapped: page.closeDialog() }
                    }
                    Rectangle {
                        width: 110; height: 38; radius: 10
                        color: "#10277a"; border.color: "#2f58d8"
                        opacity: memText.text.trim() !== "" ? 1.0 : 0.5
                        NText { anchors.centerIn: parent; text: "Guardar"; font.pixelSize: 12 }
                        TapHandler { onTapped: if (memText.text.trim() !== "") page.saveDialog() }
                    }
                }
            }
        }
    }

    // =====================================================================
    //  Confirmar borrado definitivo
    // =====================================================================
    Rectangle {
        anchors.fill: parent
        z: 210
        visible: page.purgeId !== ""
        color: Qt.rgba(0.0, 0.01, 0.06, 0.62)
        MouseArea { anchors.fill: parent; onClicked: page.purgeId = "" }

        Rectangle {
            anchors.centerIn: parent
            width: 380; height: 190; radius: 16
            color: "#08123a"; border.color: "#2a4fc0"
            MouseArea { anchors.fill: parent }
            Column {
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
                spacing: 10
                NText { text: "¿Borrar definitivamente?"; font.pixelSize: 17 }
                NText {
                    width: parent.width
                    text: "Este recuerdo se borrará para siempre y no se podrá recuperar."
                    wrapMode: Text.Wrap; font.pixelSize: 12; color: "#9db4f0"
                }
            }
            Row {
                anchors { right: parent.right; bottom: parent.bottom; margins: 20 }
                spacing: 10
                Rectangle {
                    width: 110; height: 38; radius: 10
                    color: Qt.rgba(0.1, 0.18, 0.5, 0.55); border.color: "#2a4fc0"
                    NText { anchors.centerIn: parent; text: "Cancelar"; font.pixelSize: 12 }
                    TapHandler { onTapped: page.purgeId = "" }
                }
                Rectangle {
                    width: 110; height: 38; radius: 10
                    color: "#b3203f"; border.color: "#ff5a78"
                    NText { anchors.centerIn: parent; text: "Borrar"; font.pixelSize: 12 }
                    TapHandler { onTapped: page.confirmPurge() }
                }
            }
        }
    }
}
