import QtQuick
import QtQuick.Window
import "components"

Window {
    id: root

    width: 1280
    height: 800

    minimumWidth: 1100
    minimumHeight: 680

    visible: true

    title: "NOVA – Personal Intelligence Platform"

    color: "#080A12"

    Rectangle {
        anchors.fill: parent
        color: "#080A12"
    }

    // =========================
    // SIDEBAR
    // =========================

    Rectangle {
        id: sidebar

        width: 230
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: parent.left

        color: "#0D1020"

        Rectangle {
            width: 1
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            color: "#1B2140"
        }

        Column {
            anchors.fill: parent
            anchors.margins: 22
            spacing: 12

            Text {
                text: "NOVA"
                color: "white"
                font.family: "Segoe UI"
                font.pixelSize: 26
                font.bold: true
            }

            Text {
                text: "PERSONAL INTELLIGENCE"
                color: "#6873A8"
                font.family: "Segoe UI"
                font.pixelSize: 9
                font.bold: true
            }

            Rectangle {
                width: parent.width
                height: 1
                color: "#202746"
            }

            Item {
                width: parent.width
                height: 26
            }

            Repeater {
                model: [
                    "Inicio",
                    "Conversación",
                    "Memoria",
                    "Proyectos",
                    "Dashboard",
                    "Configuración"
                ]

                delegate: Rectangle {
                    width: parent.width
                    height: 48

                    radius: 12

                    color: index === 0
                           ? "#171D3A"
                           : "transparent"

                    border.width: index === 0 ? 1 : 0
                    border.color: "#303A78"

                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 16
                        anchors.verticalCenter: parent.verticalCenter

                        text: modelData

                        color: index === 0
                               ? "#FFFFFF"
                               : "#8992B8"

                        font.family: "Segoe UI"
                        font.pixelSize: 14
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true

                        onEntered: {
                            if (index !== 0)
                                parent.color = "#11162B"
                        }

                        onExited: {
                            if (index !== 0)
                                parent.color = "transparent"
                        }
                    }
                }
            }

            Item {
                height: 1
            }

            Rectangle {
                width: parent.width
                height: 74

                radius: 14

                color: "#11162A"
                border.width: 1
                border.color: "#20294D"

                Column {
                    anchors.left: parent.left
                    anchors.leftMargin: 14
                    anchors.verticalCenter: parent.verticalCenter

                    spacing: 4

                    Text {
                        text: "NOVA"
                        color: "#FFFFFF"
                        font.pixelSize: 14
                        font.bold: true
                    }

                    Text {
                        text: "Sistema activo"
                        color: "#6573A8"
                        font.pixelSize: 11
                    }
                }
            }
        }
    }

    // =========================
    // MAIN CONTENT
    // =========================

    Item {
        anchors.left: sidebar.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        Column {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top

            anchors.margins: 42
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

        // =========================
        // CENTRAL ORB
        // =========================

        NovaOrb {
            id: mainOrb

            anchors.centerIn: parent

            orbState: novaBridge.orbState
            orbScale: 1.0
        }

        Text {
            anchors.horizontalCenter: mainOrb.horizontalCenter
            anchors.top: mainOrb.bottom
            anchors.topMargin: -4

            text: "Reposo"

            color: "#6875AE"
            font.family: "Segoe UI"
            font.pixelSize: 13
        }

        // =========================
        // INPUT
        // =========================

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom

            anchors.leftMargin: 42
            anchors.rightMargin: 42
            anchors.bottomMargin: 34

            height: 62

            radius: 18

            color: "#101528"

            border.width: 1
            border.color: "#222C50"

            Text {
                anchors.left: parent.left
                anchors.leftMargin: 22
                anchors.verticalCenter: parent.verticalCenter

                text: "Escribe o habla con NOVA..."

                color: "#596585"
                font.family: "Segoe UI"
                font.pixelSize: 14
            }
        }
    }
}