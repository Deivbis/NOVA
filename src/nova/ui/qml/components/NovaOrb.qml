import QtQuick

Item {
    id: root

    property string orbState: "idle"
    property real orbScale: 1.0

    width: 260 * orbScale
    height: 260 * orbScale

    readonly property color stateColor:
        orbState === "listening" ? "#22D3EE" :
        orbState === "processing" ? "#F59E0B" :
        orbState === "responding" ? "#38BDF8" :
        orbState === "error" ? "#EF4444" :
        "#6366F1"

    Item {
        anchors.centerIn: parent

        width: 220 * root.orbScale
        height: 220 * root.orbScale

        Rectangle {
            anchors.centerIn: parent

            width: parent.width
            height: parent.height

            radius: width / 2
            color: root.stateColor
            opacity: root.orbState === "idle" ? 0.10 : 0.18

            scale: 1.12

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite

                NumberAnimation {
                    from: 1.08
                    to: 1.16
                    duration: 1800
                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.16
                    to: 1.08
                    duration: 1800
                    easing.type: Easing.InOutSine
                }
            }
        }

        Rectangle {
            anchors.centerIn: parent

            width: parent.width * 0.78
            height: parent.height * 0.78

            radius: width / 2
            color: root.stateColor
            opacity: 0.16
        }

        Rectangle {
            anchors.centerIn: parent

            width: parent.width * 0.62
            height: parent.height * 0.62

            radius: width / 2
            color: "#11162A"
            border.width: 2
            border.color: root.stateColor
            opacity: 0.98
        }

        Rectangle {
            anchors.centerIn: parent

            width: parent.width * 0.48
            height: parent.height * 0.48

            radius: width / 2
            color: root.stateColor
            opacity: 0.92

            scale: root.orbState === "processing" ? 1.08 : 1.0

            Behavior on scale {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.OutCubic
                }
            }
        }

        Text {
            anchors.centerIn: parent

            text:
                root.orbState === "listening" ? "\u25CF" :
                root.orbState === "processing" ? "\u22EF" :
                root.orbState === "error" ? "!" :
                "N"

            color: "white"
            font.family: "Segoe UI"
            font.pixelSize: 38 * root.orbScale
            font.bold: true
        }
    }
}
