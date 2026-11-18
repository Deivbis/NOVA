import QtQuick
import QtQuick.Window
import QtQuick.Layouts

Window {
    id: win
    width: 1280
    height: 800
    minimumWidth: 980
    minimumHeight: 700
    visible: true
    title: "NOVA"
    color: Theme.bg0
    flags: Qt.Window | Qt.FramelessWindowHint

    // Estado real del Core. La vista previa de Configuración lo sustituye 4 s.
    property string previewMode: ""
    readonly property string orbMode: previewMode !== "" ? previewMode : novaBridge.orbState

    Timer { id: previewTimer; interval: 4000; onTriggered: win.previewMode = "" }

    Connections {
        target: novaBridge
        function onNavigateRequested(page) { sidebar.current = page }
    }

    Sidebar {
        id: sidebar
        width: 190
        height: parent.height
        orbMode: win.orbMode
        onCurrentChanged: novaBridge.set_current_page(current)
    }

    StackLayout {
        anchors { left: sidebar.right; right: parent.right; top: parent.top; bottom: parent.bottom }
        currentIndex: sidebar.current

        HomePage { userName: novaBridge.userName; orbMode: win.orbMode; onNavigate: (i) => sidebar.current = i }
        ConversationPage { orbMode: win.orbMode }
        MemoryPage { orbMode: win.orbMode }
        ProjectsPage { }
        DashboardPage { orbMode: win.orbMode; onNavigate: (i) => sidebar.current = i }
        SettingsPage {
            orbMode: win.orbMode
            widgetOn: novaBridge.permanentOrbEnabled
            onModeSelected: (m) => { win.previewMode = m; previewTimer.restart() }
            onWidgetToggled: (on) => novaBridge.set_permanent_orb(on)
        }
    }

    Rectangle { anchors.fill: parent; color: "transparent"; border.color: Theme.stroke; border.width: 1; z: 100 }

    Item {
        anchors { top: parent.top; left: sidebar.right; right: parent.right }
        height: 30
        z: 50
        DragHandler { onActiveChanged: if (active) win.startSystemMove() }
    }

    Row {
        anchors { top: parent.top; right: parent.right; topMargin: 12; rightMargin: 16 }
        spacing: 16
        z: 60
        Repeater {
            model: [ { ic: "min", a: "min" }, { ic: "max", a: "max" }, { ic: "close", a: "close" } ]
            Image {
                required property var modelData
                width: 16; height: 16
                sourceSize: Qt.size(32, 32)
                source: Qt.resolvedUrl("../assets/icons/" + modelData.ic + "_d.svg")
                TapHandler {
                    onTapped: {
                        if (modelData.a === "min") win.showMinimized()
                        else if (modelData.a === "max") win.visibility === Window.Maximized ? win.showNormal() : win.showMaximized()
                        else Qt.quit()
                    }
                }
            }
        }
    }
}