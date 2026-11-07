import QtQuick
import QtQuick.Controls

Item {
    id: root

    property var conversationModel: []

    Rectangle {
        anchors.fill: parent
        color: "#080A12"
    }

    // ============================================================
    // ENCABEZADO
    // ============================================================

    Text {
        id: title

        anchors.left: parent.left
        anchors.top: parent.top

        anchors.leftMargin: 42
        anchors.topMargin: 34

        text: "Conversación"

        color: "#F8FAFC"

        font.family: "Segoe UI"
        font.pixelSize: 30
        font.bold: true
    }

    Text {
        anchors.left: title.left
        anchors.top: title.bottom

        anchors.topMargin: 8

        text: root.conversationModel
            ? root.conversationModel.length + " mensajes"
            : "0 mensajes"

        color: "#6876A5"

        font.family: "Segoe UI"
        font.pixelSize: 13
    }

    // ============================================================
    // HISTORIAL DE CONVERSACIONES
    // ============================================================

    Rectangle {
        id: historyPanel

        anchors.left: parent.left
        anchors.top: title.bottom
        anchors.bottom: parent.bottom

        anchors.leftMargin: 42
        anchors.topMargin: 42
        anchors.bottomMargin: 24

        width: 220

        radius: 18

        color: "#0D1120"

        border.width: 1
        border.color: "#1D2745"

        // --------------------------------------------------------
        // TÍTULO
        // --------------------------------------------------------

        Text {
            id: historyTitle

            anchors.left: parent.left
            anchors.top: parent.top

            anchors.leftMargin: 18
            anchors.topMargin: 18

            text: "Historial"

            color: "#F8FAFC"

            font.family: "Segoe UI"
            font.pixelSize: 15
            font.bold: true
        }

        // --------------------------------------------------------
        // NUEVA CONVERSACIÓN
        // --------------------------------------------------------

        Rectangle {
            id: newConversationButton

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: historyTitle.bottom

            anchors.leftMargin: 14
            anchors.rightMargin: 14
            anchors.topMargin: 14

            height: 42

            radius: 12

            color: "#171D3A"

            border.width: 1
            border.color: "#303A78"

            Text {
                anchors.centerIn: parent

                text: "+  Nueva conversación"

                color: "#C7D2FE"

                font.family: "Segoe UI"
                font.pixelSize: 13
                font.bold: true
            }

            MouseArea {
                anchors.fill: parent

                cursorShape: Qt.PointingHandCursor

                onClicked: {
                    novaBridge.new_conversation()
                }
            }
        }

        // --------------------------------------------------------
        // LISTA DE CONVERSACIONES
        // --------------------------------------------------------

        ListView {
            id: conversationHistory

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: newConversationButton.bottom
            anchors.bottom: parent.bottom

            anchors.leftMargin: 10
            anchors.rightMargin: 10
            anchors.topMargin: 14
            anchors.bottomMargin: 12

            clip: true

            spacing: 6

            model: novaBridge.conversations

            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                id: conversationDelegate

                width: conversationHistory.width
                height: 58

                radius: 12

                property bool active:
                    modelData.id === novaBridge.activeConversationId

                color: active ? "#171D3A" : "#0D1120"

                border.width: active ? 1 : 0
                border.color: "#303A78"

                // ------------------------------------------------
                // NOMBRE DE LA CONVERSACIÓN
                // ------------------------------------------------

                Text {
                    id: conversationName

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top

                    anchors.leftMargin: 14
                    anchors.rightMargin: 44
                    anchors.topMargin: 11

                    text: modelData.title
                        ? modelData.title
                        : "Nueva conversación"

                    color: conversationDelegate.active
                        ? "#F8FAFC"
                        : "#CBD5E1"

                    font.family: "Segoe UI"
                    font.pixelSize: 12
                    font.bold: conversationDelegate.active

                    elide: Text.ElideRight
                }

                // ------------------------------------------------
                // FECHA
                // ------------------------------------------------

                Text {
                    anchors.left: conversationName.left
                    anchors.top: conversationName.bottom

                    anchors.topMargin: 4

                    text: {
                        var value = modelData.updated_at

                        if (!value) {
                            return ""
                        }

                        var date = new Date(value)

                        if (isNaN(date.getTime())) {
                            return ""
                        }

                        return Qt.formatDate(
                            date,
                            "dd/MM/yyyy"
                        )
                    }

                    color: "#6876A5"

                    font.family: "Segoe UI"
                    font.pixelSize: 10
                }

                // ------------------------------------------------
                // SELECCIONAR CONVERSACIÓN
                // ------------------------------------------------

                MouseArea {
                    anchors.fill: parent

                    z: 1

                    cursorShape: Qt.PointingHandCursor

                    onClicked: {
                        if (
                            modelData.id
                            === novaBridge.activeConversationId
                        ) {
                            return
                        }

                        novaBridge.load_conversation(
                            modelData.id
                        )
                    }
                }

                // ------------------------------------------------
                // BOTÓN RENOMBRAR
                // ------------------------------------------------

                Button {
                    id: renameButton

                    anchors.right: deleteButton.left
                    anchors.top: parent.top

                    anchors.rightMargin: 2
                    anchors.topMargin: 8

                    width: 30
                    height: 30

                    text: "✎"

                    z: 2

                    onClicked: {
                        renameDialog.conversationId = modelData.id
                        renameDialog.currentTitle = modelData.title
                            ? modelData.title
                            : ""

                        renameDialog.open()
                    }
                }

                // ------------------------------------------------
                // BOTÓN ELIMINAR
                // ------------------------------------------------

                Button {
                    id: deleteButton

                    anchors.right: parent.right
                    anchors.top: parent.top

                    anchors.rightMargin: 8
                    anchors.topMargin: 8

                    width: 30
                    height: 30

                    text: "×"

                    z: 2

                    onClicked: {
                        deleteDialog.conversationId = modelData.id
                        deleteDialog.conversationTitle = modelData.title
                            ? modelData.title
                            : "Nueva conversación"

                        deleteDialog.open()
                    }
                }
            }
        }
    }

    // ============================================================
    // ÁREA DE MENSAJES
    // ============================================================

    Item {
        id: conversationArea

        anchors.left: historyPanel.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        anchors.leftMargin: 24
        anchors.rightMargin: 42
    }

    // ============================================================
    // HISTORIAL DE MENSAJES
    // ============================================================

    ListView {
        id: historyList

        anchors.left: conversationArea.left
        anchors.right: conversationArea.right
        anchors.top: title.bottom
        anchors.bottom: inputContainer.top

        anchors.topMargin: 54
        anchors.bottomMargin: 22

        model: root.conversationModel
            ? root.conversationModel
            : []

        spacing: 16

        clip: true

        boundsBehavior: Flickable.StopAtBounds

        delegate: Item {
            id: messageDelegate

            width: historyList.width

            height: messageBubble.height

            property bool isUser:
                modelData.role === "user"

            Rectangle {
                id: messageBubble

                width: Math.min(
                    historyList.width * 0.78,
                    messageText.implicitWidth + 42
                )

                height: messageText.implicitHeight + 28

                anchors.left: messageDelegate.isUser
                    ? undefined
                    : parent.left

                anchors.right: messageDelegate.isUser
                    ? parent.right
                    : undefined

                radius: 18

                color: messageDelegate.isUser
                    ? "#171D3A"
                    : "#101528"

                border.width: 1

                border.color: messageDelegate.isUser
                    ? "#303A78"
                    : "#222C50"

                Text {
                    id: messageText

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom

                    anchors.leftMargin: 20
                    anchors.rightMargin: 20
                    anchors.topMargin: 14
                    anchors.bottomMargin: 14

                    text: modelData.content

                    color: messageDelegate.isUser
                        ? "#F1F5F9"
                        : "#C7D2FE"

                    font.family: "Segoe UI"
                    font.pixelSize: 14

                    wrapMode: Text.Wrap

                    lineHeight: 1.2

                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        onCountChanged: {
            Qt.callLater(function() {
                historyList.positionViewAtEnd()
            })
        }

        Component.onCompleted: {
            Qt.callLater(function() {
                historyList.positionViewAtEnd()
            })
        }
    }

    // ============================================================
    // INPUT
    // ============================================================

    Rectangle {
        id: inputContainer

        anchors.left: conversationArea.left
        anchors.right: conversationArea.right
        anchors.bottom: parent.bottom

        anchors.bottomMargin: 24

        height: 64

        radius: 16

        color: "#101528"

        border.width: 1
        border.color: "#4F46E5"

        TextInput {
            id: input

            anchors.fill: parent

            anchors.leftMargin: 20
            anchors.rightMargin: 70

            verticalAlignment: TextInput.AlignVCenter

            color: "#F8FAFC"

            selectionColor: "#4F46E5"

            font.family: "Segoe UI"
            font.pixelSize: 15

            clip: true

            onAccepted: {
                var value = text.trim()

                if (value.length === 0) {
                    return
                }

                novaBridge.send_message(value)

                text = ""
            }
        }

        Text {
            anchors.right: parent.right
            anchors.rightMargin: 20

            anchors.verticalCenter: parent.verticalCenter

            text: "↵"

            color: "#6876A5"

            font.pixelSize: 18
        }
    }

    // ============================================================
    // DIÁLOGO PARA RENOMBRAR CONVERSACIÓN
    // ============================================================

    Dialog {
        id: renameDialog

        property string conversationId: ""
        property string currentTitle: ""

        title: "Renombrar conversación"

        modal: true

        anchors.centerIn: parent

        standardButtons: Dialog.Ok | Dialog.Cancel

        width: 340

        contentItem: TextField {
            id: renameInput

            text: renameDialog.currentTitle

            placeholderText: "Nombre de la conversación"

            selectByMouse: true
        }

        onOpened: {
            renameInput.text = currentTitle
            renameInput.forceActiveFocus()
            renameInput.selectAll()
        }

        onAccepted: {
            var newTitle = renameInput.text.trim()

            if (newTitle.length === 0) {
                return
            }

            novaBridge.rename_conversation(
                conversationId,
                newTitle
            )
        }
    }
    // ============================================================
    // DIÁLOGO PARA ELIMINAR CONVERSACIÓN
    // ============================================================

    Dialog {
        id: deleteDialog

        property string conversationId: ""
        property string conversationTitle: ""

        title: "Eliminar conversación"

        modal: true

        anchors.centerIn: parent

        standardButtons: Dialog.Yes | Dialog.No

        width: 360

        contentItem: Text {
            text: "¿Estás seguro de que deseas eliminar \""
                + deleteDialog.conversationTitle
                + "\"?\n\nEsta acción no se puede deshacer."

            color: "#CBD5E1"

            font.family: "Segoe UI"
            font.pixelSize: 14

            wrapMode: Text.WordWrap

            padding: 16
        }

        onAccepted: {
            novaBridge.delete_conversation(
                conversationId
            )
        }
    }
}