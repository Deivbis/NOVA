import QtQuick
import QtQuick.Window
import QtQuick.Layouts

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

    // ============================================================
    // NAVEGACIÓN
    // ============================================================

    property int currentPage: 0

    /*
        0 = Inicio
        1 = Conversación
        2 = Memoria
        3 = Proyectos
        4 = Dashboard
        5 = Configuración
    */

    // ============================================================
    // FONDO
    // ============================================================

    Rectangle {
        anchors.fill: parent

        color: "#080A12"
    }

    // ============================================================
    // SIDEBAR
    // ============================================================

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

            // ----------------------------------------------------
            // LOGO
            // ----------------------------------------------------

            Text {
                text: "NOVA"

                color: "#FFFFFF"

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

            // ----------------------------------------------------
            // NAVEGACIÓN
            // ----------------------------------------------------

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
                    id: navItem

                    width: parent.width
                    height: 48

                    radius: 12

                    property bool selected:
                        root.currentPage === index

                    color:
                        selected
                            ? "#171D3A"
                            : "transparent"

                    border.width:
                        selected
                            ? 1
                            : 0

                    border.color:
                        "#303A78"

                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: 16

                        anchors.verticalCenter:
                            parent.verticalCenter

                        text: modelData

                        color:
                            navItem.selected
                                ? "#FFFFFF"
                                : "#8992B8"

                        font.family: "Segoe UI"
                        font.pixelSize: 14
                    }

                    MouseArea {
                        anchors.fill: parent

                        hoverEnabled: true

                        onEntered: {
                            if (!navItem.selected) {
                                navItem.color =
                                    "#11162B"
                            }
                        }

                        onExited: {
                            if (!navItem.selected) {
                                navItem.color =
                                    "transparent"
                            }
                        }

                        onClicked: {
                            root.currentPage = index
                        }
                    }
                }
            }

            Item {
                width: parent.width
                height: 1
            }

            // ----------------------------------------------------
            // ESTADO NOVA
            // ----------------------------------------------------

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

                    anchors.verticalCenter:
                        parent.verticalCenter

                    spacing: 4

                    Text {
                        text: "NOVA"

                        color: "#FFFFFF"

                        font.family: "Segoe UI"
                        font.pixelSize: 14
                        font.bold: true
                    }

                    Text {
                        text: "Sistema activo"

                        color: "#6573A8"

                        font.family: "Segoe UI"
                        font.pixelSize: 11
                    }
                }
            }
        }
    }

    // ============================================================
    // ÁREA PRINCIPAL
    // ============================================================

    Item {
        id: mainContent

        anchors.left: sidebar.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        // ========================================================
        // PÁGINAS
        // ========================================================

        StackLayout {
            id: pages

            anchors.fill: parent

            currentIndex: root.currentPage

            HomePage {
                id: homePage
            }

            ConversationPage {
                id: conversationPage

                conversationModel: novaBridge.messages
            }

            MemoryPage {
                id: memoryPage
            }

            Item {
                Rectangle {
                    anchors.fill: parent
                    color: "#080A12"
                }

                Text {
                    anchors.centerIn: parent

                    text: "Proyectos"

                    color: "#FFFFFF"

                    font.family: "Segoe UI"
                    font.pixelSize: 30
                    font.bold: true
                }
            }

            Item {
                Rectangle {
                    anchors.fill: parent
                    color: "#080A12"
                }

                Text {
                    anchors.centerIn: parent

                    text: "Dashboard"

                    color: "#FFFFFF"

                    font.family: "Segoe UI"
                    font.pixelSize: 30
                    font.bold: true
                }
            }

            Item {
                Rectangle {
                    anchors.fill: parent
                    color: "#080A12"
                }

                Text {
                    anchors.centerIn: parent

                    text: "Configuración"

                    color: "#FFFFFF"

                    font.family: "Segoe UI"
                    font.pixelSize: 30
                    font.bold: true
                }
            }
        }
    }
}