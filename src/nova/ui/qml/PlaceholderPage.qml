import QtQuick

Rectangle {
    property string title: ""
    gradient: Gradient {
        GradientStop { position: 0; color: Theme.bg1 }
        GradientStop { position: 1; color: Theme.bg0 }
    }
    Text {
        anchors.centerIn: parent
        text: title + " (próximamente)"
        color: Theme.textSecondary
        font.family: Theme.fontFamily
        font.pixelSize: 18
    }
}
