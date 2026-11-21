import QtQuick
Rectangle {
    id: c
    property string label: ""
    property string icon: ""
    property bool active: false
    signal clicked()
    implicitWidth: row.implicitWidth + 28
    implicitHeight: 28
    radius: 14
    color: active ? "#1f4fd8" : Qt.rgba(0.07, 0.13, 0.34, 0.55)
    border.color: active ? "#4a7bff" : "#16306f"
    Row {
        id: row
        anchors.centerIn: parent
        spacing: 7
        Image {
            visible: c.icon !== ""
            anchors.verticalCenter: parent.verticalCenter
            width: 13; height: 13; sourceSize: Qt.size(26, 26)
            source: c.icon !== "" ? Qt.resolvedUrl("../../assets/icons/" + c.icon + (c.active ? "_w" : "_d") + ".svg") : ""
        }
        NText { anchors.verticalCenter: parent.verticalCenter; text: c.label; font.pixelSize: 11; color: c.active ? "white" : "#8fb0ff" }
    }
    TapHandler { onTapped: c.clicked() }
}
