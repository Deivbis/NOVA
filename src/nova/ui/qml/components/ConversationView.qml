import QtQuick

Item {
    id: root

    property var conversationModel: []

    // ============================================================
    // CONFIGURACIÓN VISUAL
    // ============================================================

    // Zona donde comienza el desvanecimiento.
    //
    // El ConversationView comienza debajo del header.
    // Ajustamos esta zona para que el fade ocurra alrededor
    // de la posición del Orb.
    property real fadeStartY: 430

    // Distancia total del degradado.
    //
    // 430 -> 250
    //
    // Dentro de esta zona el mensaje pasa:
    //
    // 100% -> 0%
    //
    property real fadeDistance: 180

    // ============================================================
    // MODELO VISUAL
    // ============================================================

    property var displayModel: {
        if (!root.conversationModel) {
            return []
        }

        return root.conversationModel.slice().reverse()
    }

    // ============================================================
    // LISTA
    // ============================================================

    ListView {
        id: messageList

        anchors.fill: parent

        model: root.displayModel

        orientation: ListView.Vertical

        verticalLayoutDirection:
            ListView.BottomToTop

        spacing: 12

        clip: true

        boundsBehavior:
            Flickable.StopAtBounds

        cacheBuffer: 400

        // ========================================================
        // DELEGATE
        // ========================================================

        delegate: Item {
            id: messageDelegate

            required property var modelData

            width: messageList.width
            height: messageBubble.height

            property bool isUser:
                modelData.role === "user"

            // ====================================================
            // POSICIÓN VISUAL
            // ====================================================

            /*
                El delegate vive dentro del contentItem del
                ListView.

                Por eso:

                    delegate.y
                    -
                    messageList.contentY

                nos da su posición relativa al viewport.

                contentY es observable en Flickable/ListView,
                así que el binding de opacity se actualiza
                cuando la conversación se mueve.
            */

            property real viewportY:
                y - messageList.contentY

            property real viewportCenterY:
                viewportY + height / 2

            // ====================================================
            // OPACIDAD
            // ====================================================

            opacity: {
                var center =
                    viewportCenterY

                // ----------------------------------------------
                // ABAJO
                // ----------------------------------------------
                //
                // Mensaje completamente visible.
                //
                if (
                    center >= root.fadeStartY
                ) {
                    return 1.0
                }

                // ----------------------------------------------
                // ARRIBA
                // ----------------------------------------------
                //
                // Mensaje completamente invisible.
                //
                if (
                    center <= (
                        root.fadeStartY
                        - root.fadeDistance
                    )
                ) {
                    return 0.0
                }

                // ----------------------------------------------
                // DEGRADADO
                // ----------------------------------------------

                var progress =
                    (
                        center
                        - (
                            root.fadeStartY
                            - root.fadeDistance
                        )
                    )
                    / root.fadeDistance

                return Math.max(
                    0.0,
                    Math.min(
                        1.0,
                        progress
                    )
                )
            }

            // ====================================================
            // BURBUJA
            // ====================================================

            Rectangle {
                id: messageBubble

                width: Math.min(
                    messageList.width * 0.72,
                    messageText.implicitWidth + 36
                )

                height:
                    messageText.implicitHeight
                    + 24

                anchors.left:
                    messageDelegate.isUser
                        ? undefined
                        : parent.left

                anchors.right:
                    messageDelegate.isUser
                        ? parent.right
                        : undefined

                radius: 16

                color:
                    messageDelegate.isUser
                        ? "#171D3A"
                        : "#101528"

                border.width: 1

                border.color:
                    messageDelegate.isUser
                        ? "#303A78"
                        : "#222C50"

                // =================================================
                // TEXTO
                // =================================================

                Text {
                    id: messageText

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom

                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    anchors.topMargin: 12
                    anchors.bottomMargin: 12

                    text:
                        messageDelegate.modelData.content

                    color:
                        messageDelegate.isUser
                            ? "#E5E7EB"
                            : "#C7D2FE"

                    font.family: "Segoe UI"
                    font.pixelSize: 14

                    wrapMode:
                        Text.Wrap

                    lineHeight: 1.2

                    horizontalAlignment:
                        Text.AlignLeft

                    verticalAlignment:
                        Text.AlignVCenter
                }
            }
        }

        // ========================================================
        // MANTENER EL ÚLTIMO MENSAJE ABAJO
        // ========================================================

        onCountChanged: {
            Qt.callLater(function() {
                if (count > 0) {
                    positionViewAtBeginning()
                }
            })
        }

        Component.onCompleted: {
            Qt.callLater(function() {
                if (count > 0) {
                    positionViewAtBeginning()
                }
            })
        }
    }
}