import QtQuick

Item {
    id: root

    Rectangle {
        anchors.fill: parent
        color: "#080A12"
    }

    // ---------------------------------------------------------
    // HEADER
    // ---------------------------------------------------------

    Text {
        id: title

        anchors.left: parent.left
        anchors.top: parent.top

        anchors.leftMargin: 42
        anchors.topMargin: 34

        text: "Memoria"

        color: "#F8FAFC"

        font.family: "Segoe UI"
        font.pixelSize: 30
        font.bold: true
    }

    Text {
        anchors.left: title.left
        anchors.top: title.bottom

        anchors.topMargin: 8

        text: "Conocimiento y contexto almacenado por NOVA"

        color: "#6876A5"

        font.family: "Segoe UI"
        font.pixelSize: 13
    }

    // ---------------------------------------------------------
    // SEARCH
    // ---------------------------------------------------------

    Rectangle {
        id: searchContainer

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: title.bottom

        anchors.leftMargin: 42
        anchors.rightMargin: 42
        anchors.topMargin: 48

        height: 52

        radius: 15

        color: "#101528"

        border.width: 1
        border.color:
            searchInput.activeFocus
                ? "#4F46E5"
                : "#222C50"

        Text {
            anchors.left: parent.left
            anchors.leftMargin: 18

            anchors.verticalCenter: parent.verticalCenter

            text: "⌕"

            color: "#6876A5"

            font.pixelSize: 22
        }

        TextInput {
            id: searchInput

            anchors.left: parent.left
            anchors.right: parent.right

            anchors.leftMargin: 48
            anchors.rightMargin: 18

            anchors.verticalCenter: parent.verticalCenter

            height: 30

            color: "#E5E7EB"

            selectionColor: "#4F46E5"
            selectedTextColor: "#FFFFFF"

            font.family: "Segoe UI"
            font.pixelSize: 14

            clip: true

            Text {
                anchors.fill: parent

                text: "Buscar en la memoria de NOVA..."

                color: "#596585"

                font.family: "Segoe UI"
                font.pixelSize: 14

                verticalAlignment: Text.AlignVCenter

                visible:
                    searchInput.text.length === 0
                    && !searchInput.activeFocus
            }
        }
    }

    // ---------------------------------------------------------
    // CATEGORY BAR
    // ---------------------------------------------------------

    Row {
        id: categoryBar

        anchors.left: searchContainer.left
        anchors.top: searchContainer.bottom

        anchors.topMargin: 18

        spacing: 10

        property int selectedCategory: 0

        Repeater {
            model: [
                "Todo",
                "Personas",
                "Preferencias",
                "Proyectos",
                "Contexto"
            ]

            delegate: Rectangle {
                id: categoryItem

                width: categoryText.implicitWidth + 30
                height: 34

                radius: 17

                property bool selected:
                    categoryBar.selectedCategory === index

                color:
                    selected
                        ? "#171D3A"
                        : "#0D1120"

                border.width: 1

                border.color:
                    selected
                        ? "#303A78"
                        : "#1A2240"

                Text {
                    id: categoryText

                    anchors.centerIn: parent

                    text: modelData

                    color:
                        categoryItem.selected
                            ? "#FFFFFF"
                            : "#7783AA"

                    font.family: "Segoe UI"
                    font.pixelSize: 12
                    font.bold: categoryItem.selected
                }

                MouseArea {
                    anchors.fill: parent

                    cursorShape: Qt.PointingHandCursor

                    onClicked: {
                        categoryBar.selectedCategory = index
                    }
                }
            }
        }
    }

    // ---------------------------------------------------------
    // MEMORY CARDS
    // ---------------------------------------------------------

    ListView {
        id: memoryList

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: categoryBar.bottom
        anchors.bottom: parent.bottom

        anchors.leftMargin: 42
        anchors.rightMargin: 42

        anchors.topMargin: 24
        anchors.bottomMargin: 30

        clip: true

        spacing: 12

        model: [
            {
                title: "Preferencias de interacción",
                category: "Preferencias",
                description:
                    "NOVA adapta sus respuestas al estilo de interacción configurado.",
                meta: "Preferencias"
            },
            {
                title: "Contexto de conversación",
                category: "Contexto",
                description:
                    "Información relevante derivada de conversaciones recientes.",
                meta: "Contexto"
            },
            {
                title: "Proyectos activos",
                category: "Proyectos",
                description:
                    "NOVA mantiene referencias sobre proyectos y tareas en curso.",
                meta: "Proyectos"
            },
            {
                title: "Información personal",
                category: "Personas",
                description:
                    "Datos que el usuario haya decidido conservar explícitamente.",
                meta: "Personas"
            }
        ]

        delegate: Rectangle {
            id: memoryCard

            width: memoryList.width
            height: 92

            radius: 16

            color: "#101528"

            border.width: 1
            border.color: "#20294D"

            Row {
                anchors.fill: parent

                anchors.leftMargin: 18
                anchors.rightMargin: 18

                spacing: 16

                Rectangle {
                    width: 44
                    height: 44

                    anchors.verticalCenter: parent.verticalCenter

                    radius: 13

                    color: "#171D3A"

                    border.width: 1
                    border.color: "#303A78"

                    Text {
                        anchors.centerIn: parent

                        text: "N"

                        color: "#818CF8"

                        font.family: "Segoe UI"
                        font.pixelSize: 17
                        font.bold: true
                    }
                }

                Column {
                    anchors.verticalCenter: parent.verticalCenter

                    width:
                        memoryCard.width
                        - 44
                        - 16
                        - 36

                    spacing: 5

                    Text {
                        width: parent.width

                        text: modelData.title

                        color: "#F1F5F9"

                        font.family: "Segoe UI"
                        font.pixelSize: 14
                        font.bold: true

                        elide: Text.ElideRight
                    }

                    Text {
                        width: parent.width

                        text: modelData.description

                        color: "#7885AA"

                        font.family: "Segoe UI"
                        font.pixelSize: 12

                        elide: Text.ElideRight
                    }
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter

                    text: modelData.meta

                    color: "#58668E"

                    font.family: "Segoe UI"
                    font.pixelSize: 11
                }
            }

            MouseArea {
                anchors.fill: parent

                hoverEnabled: true

                onEntered: {
                    memoryCard.border.color = "#303A78"
                }

                onExited: {
                    memoryCard.border.color = "#20294D"
                }
            }
        }
    }
}