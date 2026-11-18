import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// Conversación: lista de chats (crear / renombrar / eliminar) + chat con fondo espacial.
//
// La interfaz ya funciona con datos locales de ejemplo (AppData.chats / AppData.messages).
// Para conectarla a tu lógica:
//   · escucha las señales  newChatRequested / renameChatRequested / deleteChatRequested / messageSent / chatSelected
//   · llama a  addMessage("nova", texto)  y  typing = true/false  cuando respondas
//   · pon  demoMode: false  para desactivar las respuestas de ejemplo
Rectangle {
    id: page
    color: "#050b22"

    property string orbMode: "idle"
    property string currentId: ""
    property string editingId: ""         // chat que se está renombrando
    property string confirmId: ""         // chat pendiente de confirmar eliminación
    property string filter: ""
    property bool typing: false           // puntos «escribiendo…» (antes del primer fragmento)
    property bool revealNext: false       // la próxima respuesta es local: se escribe poco a poco
    property string revealFull: ""
    property string notice: ""

    readonly property var assistText: ({ idle: "En línea", listening: "Escuchando...", processing: "Pensando...", responding: "Respondiendo...", error: "Requiere atención" })

    function icon(n, v) { return Qt.resolvedUrl("../assets/icons/" + n + "_" + (v || "c") + ".svg") }
    function indexOfChat(cid) {
        for (var i = 0; i < chatsModel.count; i++) if (chatsModel.get(i).cid === cid) return i
        return -1
    }
    function chatTitle(cid) { var i = indexOfChat(cid); return i >= 0 ? chatsModel.get(i).title : "" }
    function notify(t) { notice = t; noticeTimer.restart() }

    // ---- lista de chats (desde la base de datos) ----
    function syncChats() {
        var list = novaBridge.chatList
        var same = list.length === chatsModel.count
        for (var i = 0; same && i < list.length; i++)
            if (chatsModel.get(i).cid !== list[i].id) same = false
        if (same) {
            for (var j = 0; j < list.length; j++) {
                chatsModel.setProperty(j, "title", list[j].title)
                chatsModel.setProperty(j, "preview", list[j].preview)
                chatsModel.setProperty(j, "time", list[j].time)
            }
        } else {
            chatsModel.clear()
            for (var k = 0; k < list.length; k++)
                chatsModel.append({ cid: list[k].id, title: list[k].title, preview: list[k].preview, time: list[k].time })
        }
    }

    // ---- mensajes del chat activo ----
    function reloadMessages() {
        revealTimer.stop()
        msgModel.clear()
        var list = novaBridge.chatMessages
        for (var i = 0; i < list.length; i++)
            msgModel.append({ role: list[i].role === "assistant" ? "nova" : list[i].role,
                              text: list[i].content, time: list[i].time, streaming: list[i].streaming })
        currentId = novaBridge.activeConversationId
        var last = list.length ? list[list.length - 1] : null
        typing = novaBridge.is_busy(currentId) && !(last && last.streaming)
        if (revealNext && last && last.role === "assistant" && !last.streaming) {
            revealFull = last.content
            msgModel.setProperty(msgModel.count - 1, "text", "")
            revealTimer.start()
        }
        revealNext = false
    }

    function selectChat(cid) {
        editingId = ""
        if (cid !== novaBridge.activeConversationId) novaBridge.load_conversation(cid)
        else reloadMessages()
    }
    function newChat() { novaBridge.new_conversation() }
    function commitRename(cid, text) {
        var t = text.trim()
        if (t.length > 0) novaBridge.rename_conversation(cid, t)
        editingId = ""
    }
    function deleteChat(cid) {
        confirmId = ""
        if (!novaBridge.delete_conversation(cid)) notify("NOVA está respondiendo en ese chat; espera un momento.")
    }
    function send(text) {
        var t = text.trim()
        if (t === "" || currentId === "") return
        novaBridge.send_message(t)
    }

    ListModel { id: chatsModel }
    ListModel { id: msgModel }

    Component.onCompleted: { syncChats(); reloadMessages() }

    Connections {
        target: novaBridge
        function onConversationsChanged() { page.syncChats() }
        function onConversationChanged() { page.reloadMessages() }
        function onLocalReply() { page.revealNext = true }
        function onStreamChunk(cid, delta) {
            if (cid !== page.currentId) return
            page.typing = false
            var last = msgModel.count - 1
            if (last >= 0 && msgModel.get(last).streaming)
                msgModel.setProperty(last, "text", msgModel.get(last).text + delta)
            else
                msgModel.append({ role: "nova", text: delta, time: "", streaming: true })
        }
        function onRequestFinished(cid) { if (cid === page.currentId) page.typing = false }
    }

    // respuestas locales (órdenes): se escriben poco a poco como las del modelo
    Timer {
        id: revealTimer
        interval: 16; repeat: true
        onTriggered: {
            var last = msgModel.count - 1
            if (last < 0) { stop(); return }
            var next = Math.min(page.revealFull.length, msgModel.get(last).text.length + 3)
            msgModel.setProperty(last, "text", page.revealFull.substring(0, next))
            if (next >= page.revealFull.length) stop()
        }
    }
    Timer { id: noticeTimer; interval: 3500; onTriggered: page.notice = "" }

    // =====================================================================
    //  Panel izquierdo: lista de chats
    // =====================================================================
    Rectangle {
        id: listPanel
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
        width: Math.max(260, Math.min(330, page.width * 0.27))
        color: "#060b25"
        Rectangle { anchors.right: parent.right; width: 1; height: parent.height; color: "#14296e" }

        ColumnLayout {
            anchors { fill: parent; leftMargin: 16; rightMargin: 16; topMargin: 40; bottomMargin: 16 }
            spacing: 12

            NText { text: "Conversaciones"; font.pixelSize: 20 }

            // Nuevo chat
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 42
                radius: 12
                border.color: "#5b7bff"
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: "#2447e6" }
                    GradientStop { position: 1; color: "#3b63ff" }
                }
                Row {
                    anchors.centerIn: parent
                    spacing: 8
                    Image { anchors.verticalCenter: parent.verticalCenter; width: 16; height: 16; sourceSize: Qt.size(32, 32); source: page.icon("plus", "w") }
                    NText { anchors.verticalCenter: parent.verticalCenter; text: "Nuevo chat"; font.pixelSize: 13 }
                }
                TapHandler { onTapped: page.newChat() }
            }

            // Búsqueda
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 36
                radius: 18
                color: Qt.rgba(0.07, 0.13, 0.34, 0.55); border.color: "#1f3f9a"
                Image { x: 13; anchors.verticalCenter: parent.verticalCenter; width: 15; height: 15; sourceSize: Qt.size(30, 30); source: page.icon("search", "d") }
                TextField {
                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; leftMargin: 36; rightMargin: 12 }
                    placeholderText: "Buscar chats..."
                    placeholderTextColor: "#6f8fe0"
                    color: "white"
                    font.family: Theme.fontFamily
                    font.pixelSize: 12
                    background: null
                    onTextChanged: page.filter = text.toLowerCase()
                }
            }

            NText { text: "Recientes"; font.pixelSize: 11; color: "#6f8fe0"; Layout.topMargin: 4 }

            ListView {
                id: chatList
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: chatsModel
                spacing: 6
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                delegate: Rectangle {
                    id: item
                    required property int index
                    required property string cid
                    required property string title
                    required property string preview
                    required property string time
                    readonly property bool selected: page.currentId === cid
                    readonly property bool editing: page.editingId === cid
                    readonly property bool matches: page.filter === "" || title.toLowerCase().indexOf(page.filter) >= 0
                    readonly property bool showActions: (hh.hovered || selected) && !editing

                    width: ListView.view.width
                    height: matches ? 64 : 0
                    visible: matches
                    radius: 12
                    color: selected ? Qt.rgba(0.14, 0.26, 0.78, 0.35) : (hh.hovered ? Qt.rgba(0.1, 0.18, 0.5, 0.25) : "transparent")
                    border.width: selected ? 1 : 0
                    border.color: "#4a6dff"

                    HoverHandler { id: hh }
                    TapHandler { onTapped: page.selectChat(item.cid) }

                    Rectangle {
                        x: 12; anchors.verticalCenter: parent.verticalCenter
                        width: 38; height: 38; radius: 19
                        color: Qt.rgba(0.08, 0.16, 0.45, 0.8); border.color: "#2a4fc0"
                        Image { anchors.centerIn: parent; width: 18; height: 18; sourceSize: Qt.size(36, 36); source: page.icon("chat", "c") }
                    }

                    Column {
                        x: 60; anchors.verticalCenter: parent.verticalCenter
                        width: item.width - 60 - (item.showActions ? 74 : 54)
                        spacing: 4
                        NText { visible: !item.editing; width: parent.width; text: item.title; font.pixelSize: 13; font.bold: item.selected; elide: Text.ElideRight }
                        TextField {
                            id: renameField
                            visible: item.editing
                            width: parent.width + 40
                            height: 28
                            text: item.title
                            color: "white"
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            leftPadding: 8; rightPadding: 8; topPadding: 2; bottomPadding: 2
                            background: Rectangle { radius: 8; color: "#0b1a52"; border.color: "#4a6dff" }
                            onVisibleChanged: if (visible) { forceActiveFocus(); selectAll() }
                            onAccepted: page.commitRename(item.cid, text)
                            Keys.onEscapePressed: page.editingId = ""
                        }
                        NText { visible: !item.editing; width: parent.width; text: item.preview; font.pixelSize: 11; color: "#6f8fe0"; elide: Text.ElideRight }
                    }

                    NText {
                        visible: !item.showActions && !item.editing
                        anchors { right: parent.right; rightMargin: 12; top: parent.top; topMargin: 14 }
                        text: item.time; font.pixelSize: 10; color: "#5d7bc0"
                    }

                    // Botones de editar / eliminar
                    Row {
                        Rectangle {   // detener la voz
                            visible: page.orbMode === "responding" && novaBridge.voiceEnabled
                            width: 36; height: 36; radius: 10
                            color: hStop.hovered ? Qt.rgba(0.8, 0.15, 0.3, 0.5) : Qt.rgba(0.07, 0.13, 0.34, 0.6); border.color: "#1f3f9a"
                            HoverHandler { id: hStop }
                            Image { anchors.centerIn: parent; width: 17; height: 17; sourceSize: Qt.size(34, 34); source: page.icon("speaker", "c") }
                            TapHandler { onTapped: novaBridge.stop_speaking() }
                        }
                        visible: item.showActions
                        anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                        spacing: 4
                        Rectangle {
                            width: 28; height: 28; radius: 8
                            color: editHover.hovered ? Qt.rgba(0.2, 0.3, 0.8, 0.5) : Qt.rgba(0.1, 0.18, 0.5, 0.45)
                            HoverHandler { id: editHover }
                            Image { anchors.centerIn: parent; width: 15; height: 15; sourceSize: Qt.size(30, 30); source: page.icon("edit", "c") }
                            TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: { page.selectChat(item.cid); page.editingId = item.cid } }
                        }
                        Rectangle {
                            width: 28; height: 28; radius: 8
                            color: delHover.hovered ? Qt.rgba(0.8, 0.15, 0.3, 0.5) : Qt.rgba(0.1, 0.18, 0.5, 0.45)
                            HoverHandler { id: delHover }
                            Image { anchors.centerIn: parent; width: 15; height: 15; sourceSize: Qt.size(30, 30); source: page.icon("trash", delHover.hovered ? "r" : "c") }
                            TapHandler { gesturePolicy: TapHandler.ReleaseWithinBounds; onTapped: page.confirmId = item.cid }
                        }
                    }
                }
            }
        }
    }

    // =====================================================================
    //  Área del chat
    // =====================================================================
    Item {
        id: area
        anchors { left: listPanel.right; right: parent.right; top: parent.top; bottom: parent.bottom }
        clip: true

        // Fondo espacial
        Rectangle { anchors.fill: parent; color: "#050826" }
        Image {
            anchors.fill: parent
            source: Qt.resolvedUrl("../assets/bg_chat.jpg")
            fillMode: Image.PreserveAspectCrop
            smooth: true
        }
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: Qt.rgba(0.01, 0.02, 0.10, 0.45) }
                GradientStop { position: 0.55; color: Qt.rgba(0.01, 0.02, 0.10, 0.18) }
                GradientStop { position: 1.0; color: Qt.rgba(0.01, 0.02, 0.10, 0.40) }
            }
        }

        // ---- Cabecera ----
        Rectangle {
            id: header
            anchors { top: parent.top; left: parent.left; right: parent.right }
            height: 80
            color: Qt.rgba(0.02, 0.04, 0.16, 0.55)
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: "#14296e" }

            Orb { x: 22; anchors.verticalCenter: parent.verticalCenter; size: 54; mode: page.orbMode }
            Column {
                x: 92; anchors.verticalCenter: parent.verticalCenter
                spacing: 3
                NText { text: page.currentId === "" ? "Sin conversación" : page.chatTitle(page.currentId); font.pixelSize: 17 }
                Row {
                    spacing: 6
                    Rectangle { anchors.verticalCenter: parent.verticalCenter; width: 7; height: 7; radius: 3.5; color: page.orbMode === "error" ? "#ff5a78" : "#2fe0a0" }
                    NText {
                        text: page.notice !== "" ? page.notice : (page.typing ? "NOVA está escribiendo..." : (page.assistText[page.orbMode] || "En línea"))
                        font.pixelSize: 11
                        color: page.notice !== "" ? "#ffb347" : "#8fb0ff"
                    }
                }
            }
            Row {
                visible: page.currentId !== ""
                anchors { right: parent.right; rightMargin: 118; verticalCenter: parent.verticalCenter }
                spacing: 8
                Rectangle {
                    width: 36; height: 36; radius: 10
                    color: hEdit.hovered ? Qt.rgba(0.2, 0.3, 0.8, 0.5) : Qt.rgba(0.07, 0.13, 0.34, 0.6); border.color: "#1f3f9a"
                    HoverHandler { id: hEdit }
                    Image { anchors.centerIn: parent; width: 17; height: 17; sourceSize: Qt.size(34, 34); source: page.icon("edit", "c") }
                    TapHandler { onTapped: page.editingId = page.currentId }
                }
                Rectangle {
                    width: 36; height: 36; radius: 10
                    color: hDel.hovered ? Qt.rgba(0.8, 0.15, 0.3, 0.5) : Qt.rgba(0.07, 0.13, 0.34, 0.6); border.color: "#1f3f9a"
                    HoverHandler { id: hDel }
                    Image { anchors.centerIn: parent; width: 17; height: 17; sourceSize: Qt.size(34, 34); source: page.icon("trash", hDel.hovered ? "r" : "c") }
                    TapHandler { onTapped: page.confirmId = page.currentId }
                }
            }
        }

        // ---- Mensajes ----
        ListView {
            id: msgList
            readonly property real side: Math.max(24, (area.width - 900) / 2)
            anchors { top: header.bottom; bottom: inputWrap.top; left: parent.left; right: parent.right; leftMargin: side; rightMargin: side; topMargin: 16; bottomMargin: 6 }
            model: msgModel
            spacing: 18
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            visible: page.currentId !== "" && (msgModel.count > 0 || page.typing)
            property bool follow: true
            onCountChanged: { follow = true; Qt.callLater(function () { msgList.positionViewAtEnd() }) }
            onContentHeightChanged: if (follow) Qt.callLater(function () { msgList.positionViewAtEnd() })
            onMovementEnded: follow = atYEnd

            delegate: Item {
                id: md
                required property string role
                required property string text
                required property string time
                required property bool streaming
                readonly property bool mine: role === "user"
                readonly property bool failed: role === "error"
                readonly property string shown: text + (streaming ? " ▍" : "")
                readonly property real maxW: Math.min(ListView.view.width * 0.66, 560)
                readonly property real bw: Math.min(tm.width, maxW) + 34

                width: ListView.view.width
                height: col.height

                TextMetrics { id: tm; font.family: Theme.fontFamily; font.pixelSize: 14; text: md.shown }

                Item {
                    visible: !md.mine
                    width: 40; height: 40
                    Orb { anchors.centerIn: parent; size: 40; mode: "idle" }
                }
                Column {
                    id: col
                    spacing: 5
                    x: md.mine ? md.width - width : 52
                    Rectangle {
                        id: bubble
                        width: md.bw
                        height: txt.implicitHeight + 26
                        radius: 16
                        border.width: 1
                        border.color: md.mine ? "#6a8bff" : (md.failed ? "#ff5a78" : "#24419f")
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0; color: md.mine ? "#2447e6" : (md.failed ? "#4a0f22" : Qt.rgba(0.04, 0.08, 0.26, 0.86)) }
                            GradientStop { position: 1; color: md.mine ? "#3a62ff" : (md.failed ? "#5a1328" : Qt.rgba(0.05, 0.10, 0.30, 0.86)) }
                        }
                        NText {
                            id: txt
                            x: 17; y: 13
                            width: bubble.width - 34
                            text: md.shown
                            textFormat: (md.mine || md.failed) ? Text.PlainText : Text.MarkdownText
                            wrapMode: Text.Wrap
                            font.pixelSize: 14
                            lineHeight: 1.15
                            color: md.mine ? "white" : "#e4ebff"
                        }
                    }
                    NText {
                        width: bubble.width
                        text: md.time
                        font.pixelSize: 10
                        color: "#7f9bd8"
                        horizontalAlignment: md.mine ? Text.AlignRight : Text.AlignLeft
                    }
                }
            }

            // indicador "escribiendo…"
            footer: Item {
                width: msgList.width
                height: page.typing ? 56 : 0
                visible: page.typing
                Item {
                    y: 12; width: 40; height: 40
                    Orb { anchors.centerIn: parent; size: 40; mode: "processing" }
                }
                Rectangle {
                    x: 52; y: 12; width: 76; height: 38; radius: 16
                    color: Qt.rgba(0.04, 0.08, 0.26, 0.86); border.color: "#24419f"
                    Row {
                        anchors.centerIn: parent
                        spacing: 7
                        Repeater {
                            model: 3
                            Rectangle {
                                id: dot
                                required property int index
                                width: 8; height: 8; radius: 4; color: "#8fb0ff"
                                SequentialAnimation on opacity {
                                    running: page.typing
                                    loops: Animation.Infinite
                                    PauseAnimation { duration: dot.index * 160 }
                                    NumberAnimation { from: 0.25; to: 1.0; duration: 300 }
                                    NumberAnimation { from: 1.0; to: 0.25; duration: 300 }
                                    PauseAnimation { duration: (2 - dot.index) * 160 }
                                }
                            }
                        }
                    }
                }
            }
        }

        // ---- Chat vacío ----
        Column {
            visible: page.currentId !== "" && msgModel.count === 0 && !page.typing
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -30
            spacing: 10
            Item {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 230; height: 200
                Orb { anchors.centerIn: parent; size: 230; mode: page.orbMode }
            }
            NText { anchors.horizontalCenter: parent.horizontalCenter; text: "¿En qué puedo ayudarte hoy?"; font.pixelSize: 22 }
            NText { anchors.horizontalCenter: parent.horizontalCenter; text: "Escribe un mensaje o elige una sugerencia."; font.pixelSize: 13; color: "#9db4f0" }
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 8
                topPadding: 12
                Repeater {
                    model: AppData.chatSuggestions
                    Chip {
                        required property string modelData
                        label: modelData
                        onClicked: { input.text = modelData; input.forceActiveFocus() }
                    }
                }
            }
        }

        // ---- Sin chats ----
        Column {
            visible: page.currentId === ""
            anchors.centerIn: parent
            spacing: 14
            NText { anchors.horizontalCenter: parent.horizontalCenter; text: "No hay conversaciones"; font.pixelSize: 20 }
            NText { anchors.horizontalCenter: parent.horizontalCenter; text: "Crea un nuevo chat para empezar."; font.pixelSize: 13; color: "#9db4f0" }
        }

        // ---- Barra de escritura ----
        Item {
            id: inputWrap
            anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            height: 92
            visible: page.currentId !== ""

            Rectangle {
                width: Math.min(area.width - 48, 900)
                height: 54
                anchors.centerIn: parent
                radius: 27
                border.width: 1.5
                border.color: "#4a6dff"
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: Qt.rgba(0.08, 0.14, 0.40, 0.88) }
                    GradientStop { position: 1; color: Qt.rgba(0.06, 0.10, 0.32, 0.88) }
                }
                Rectangle { anchors.fill: parent; anchors.margins: -3; radius: 30; color: "transparent"; border.width: 3; border.color: Qt.rgba(0.3, 0.45, 1, 0.14); z: -1 }

                Image { id: clipIcon; x: 20; anchors.verticalCenter: parent.verticalCenter; width: 20; height: 20; sourceSize: Qt.size(40, 40); source: page.icon("clip", "d") }
                TextField {
                    id: input
                    anchors { left: clipIcon.right; right: micIcon.left; verticalCenter: parent.verticalCenter; leftMargin: 14; rightMargin: 12 }
                    placeholderText: "Escribe un mensaje a NOVA..."
                    placeholderTextColor: "#8fb0f5"
                    color: "white"
                    font.family: Theme.fontFamily
                    font.pixelSize: 14
                    background: null
                    onAccepted: { page.send(text); text = "" }
                }
                Image {
                    id: micIcon
                    anchors { right: sendBtn.left; rightMargin: 14; verticalCenter: parent.verticalCenter }
                    width: 20; height: 20; sourceSize: Qt.size(40, 40)
                    source: page.icon("mic", page.orbMode === "listening" ? "w" : "c")
                    TapHandler { onTapped: novaBridge.toggle_voice_input() }
                }
                Rectangle {
                    id: sendBtn
                    anchors { right: parent.right; rightMargin: 8; verticalCenter: parent.verticalCenter }
                    width: 38; height: 38; radius: 19
                    opacity: input.text.trim() !== "" ? 1.0 : 0.5
                    Behavior on opacity { NumberAnimation { duration: 120 } }
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: "#2447e6" }
                        GradientStop { position: 1; color: "#3b7bff" }
                    }
                    Image { anchors.centerIn: parent; width: 18; height: 18; sourceSize: Qt.size(36, 36); source: page.icon("send", "w") }
                    TapHandler { onTapped: { page.send(input.text); input.text = "" } }
                }
            }
        }
    }

    // =====================================================================
    //  Confirmar eliminación
    // =====================================================================
    Rectangle {
        anchors.fill: parent
        z: 200
        visible: page.confirmId !== ""
        color: Qt.rgba(0.0, 0.01, 0.06, 0.62)
        MouseArea { anchors.fill: parent; onClicked: page.confirmId = "" }

        Rectangle {
            anchors.centerIn: parent
            width: 380; height: 190; radius: 16
            color: "#08123a"; border.color: "#2a4fc0"
            MouseArea { anchors.fill: parent }       // evita cerrar al pulsar dentro
            Column {
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 24 }
                spacing: 10
                NText { text: "¿Eliminar esta conversación?"; font.pixelSize: 17 }
                NText {
                    width: parent.width
                    text: "«" + page.chatTitle(page.confirmId) + "» se eliminará con todos sus mensajes."
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
                    TapHandler { onTapped: page.confirmId = "" }
                }
                Rectangle {
                    width: 110; height: 38; radius: 10
                    color: "#b3203f"; border.color: "#ff5a78"
                    NText { anchors.centerIn: parent; text: "Eliminar"; font.pixelSize: 12 }
                    TapHandler { onTapped: page.deleteChat(page.confirmId) }
                }
            }
        }
    }
}
