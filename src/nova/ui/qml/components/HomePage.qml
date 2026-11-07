import QtQuick

Item {
    id: root

    // ============================================================
    // FONDO
    // ============================================================

    Rectangle {
        anchors.fill: parent
        color: "#080A12"
    }

    // ============================================================
    // HEADER
    // ============================================================

    Column {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top

        anchors.leftMargin: 42
        anchors.rightMargin: 42
        anchors.topMargin: 34

        spacing: 8

        Text {
            text: "Buenos días, Jefe."

            color: "#FFFFFF"

            font.family: "Segoe UI"
            font.pixelSize: 30
            font.bold: true
        }

        Text {
            text: "NOVA está lista."

            color: "#7D89B7"

            font.family: "Segoe UI"
            font.pixelSize: 15
        }
    }

    // ============================================================
    // CONVERSACIÓN RECIENTE
    // ============================================================

    ConversationView {
        id: conversationView

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: conversationInputContainer.top

        anchors.leftMargin: 42
        anchors.rightMargin: 42

        anchors.topMargin: 150
        anchors.bottomMargin: 24

        conversationModel: novaBridge.messages

        z: 1
    }

    // ============================================================
    // CENTRAL ORB
    // ============================================================

    NovaOrb {
        id: mainOrb

        anchors.horizontalCenter:
            parent.horizontalCenter

        anchors.verticalCenter:
            parent.verticalCenter

        anchors.verticalCenterOffset: -35

        orbState: novaBridge.orbState
        orbScale: 1.0

        z: 10
    }

    // ============================================================
    // ORB STATUS
    // ============================================================

    Text {
        anchors.horizontalCenter:
            mainOrb.horizontalCenter

        anchors.top:
            mainOrb.bottom

        anchors.topMargin: -4

        z: 11

        text:
            novaBridge.orbState === "listening"
                ? "Escuchando"
                : novaBridge.orbState === "processing"
                    ? "Procesando"
                    : novaBridge.orbState === "responding"
                        ? "Respondiendo"
                        : novaBridge.orbState === "error"
                            ? "Error"
                            : "Reposo"

        color:
            novaBridge.orbState === "listening"
                ? "#22D3EE"
                : novaBridge.orbState === "processing"
                    ? "#F59E0B"
                    : novaBridge.orbState === "responding"
                        ? "#38BDF8"
                        : novaBridge.orbState === "error"
                            ? "#EF4444"
                            : "#6875AE"

        font.family: "Segoe UI"
        font.pixelSize: 13
    }

    // ============================================================
    // INPUT
    // ============================================================

    Rectangle {
        id: conversationInputContainer

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        anchors.leftMargin: 42
        anchors.rightMargin: 42
        anchors.bottomMargin: 34

        height: 62

        radius: 18

        color: "#101528"

        border.width:
            conversationInput.activeFocus
                ? 1.5
                : 1

        border.color:
            conversationInput.activeFocus
                ? "#4F46E5"
                : "#222C50"

        Text {
            id: conversationPlaceholder

            anchors.left: parent.left
            anchors.leftMargin: 22

            anchors.verticalCenter:
                parent.verticalCenter

            text: "Escribe o habla con NOVA..."

            color: "#596585"

            font.family: "Segoe UI"
            font.pixelSize: 14

            visible:
                conversationInput.text.length === 0
                && !conversationInput.activeFocus
        }

        TextInput {
            id: conversationInput

            anchors.left: parent.left
            anchors.right: parent.right

            anchors.leftMargin: 22
            anchors.rightMargin: 22

            anchors.verticalCenter:
                parent.verticalCenter

            height: 28

            color: "#E5E7EB"

            selectionColor: "#4F46E5"
            selectedTextColor: "#FFFFFF"

            font.family: "Segoe UI"
            font.pixelSize: 14

            clip: true

            activeFocusOnPress: true
            selectByMouse: true

            verticalAlignment:
                TextInput.AlignVCenter

            Keys.onReturnPressed: {
                if (text.trim().length === 0) {
                    return
                }

                console.log(
                    "NOVA INPUT:",
                    text
                )

                novaBridge.send_message(text)

                clear()
            }

            Keys.onEnterPressed: {
                if (text.trim().length === 0) {
                    return
                }

                console.log(
                    "NOVA INPUT:",
                    text
                )

                novaBridge.send_message(text)

                clear()
            }
        }
    }
}