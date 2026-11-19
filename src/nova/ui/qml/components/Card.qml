import QtQuick

Rectangle {
    id: card
    property bool highlighted: false
    signal clicked()
    default property alias content: holder.data

    radius: Theme.radiusMd
    border.width: 1
    border.color: (hover.hovered || highlighted) ? Theme.strokeStrong : Theme.stroke
    Behavior on border.color { ColorAnimation { duration: 160 } }

    gradient: Gradient {
        GradientStop { position: 0.0; color: Qt.rgba(0.07, 0.14, 0.38, 0.50) }
        GradientStop { position: 1.0; color: Qt.rgba(0.03, 0.06, 0.18, 0.72) }
    }

    HoverHandler { id: hover }
    TapHandler { onTapped: card.clicked() }
    Item { id: holder; anchors.fill: parent }
}
