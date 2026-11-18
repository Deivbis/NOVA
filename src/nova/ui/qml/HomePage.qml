import QtQuick
import QtQuick.Controls

// Pantalla de Inicio. Posiciones proporcionales a la referencia (Hoja 01).
Item {
    id: page
    property string orbMode: "idle"
    property string userName: "Deivis"
    signal navigate(int page)

    readonly property real pw: width
    readonly property real ph: height
    readonly property real orbSize: Math.min(pw * 0.22, ph * 0.40)
    readonly property real orbItem: orbSize * 1.25                 // tamaño del componente Orb
    // centro vertical del orbe: más abajo, entre la barra superior y el título "NOVA"
    readonly property real orbCy: Math.max(orbItem * 0.42 + 44, Math.min(ph * 0.32, ph * 0.51 - 40 - orbItem * 0.42))

    function greeting() {
        var h = new Date().getHours()
        return h < 12 ? "Buenos días" : (h < 20 ? "Buenas tardes" : "Buenas noches")
    }
    function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)) }
    function submit(raw) {
        var t = raw.trim()
        if (t === "") return
        novaBridge.start_conversation_with(t)   // crea el chat y envía el mensaje
        homeInput.text = ""
        navigate(1)                             // salta a la conversación creada
    }

    // Fondo
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#050826" }
            GradientStop { position: 0.6; color: "#1f1470" }
            GradientStop { position: 1.0; color: "#070d2b" }
        }
    }
    Image {
        anchors.fill: parent
        source: Qt.resolvedUrl("../assets/bg_home.jpg")
        fillMode: Image.PreserveAspectCrop
        smooth: true
    }
    Rectangle { // oscurece suavemente la parte baja para que el texto se lea
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 0.42; color: Qt.rgba(0.01, 0.02, 0.10, 0.10) }
            GradientStop { position: 1.0; color: Qt.rgba(0.01, 0.02, 0.09, 0.62) }
        }
    }

    // Botones superiores derechos (sonido / ajustes)
    Row {
        anchors { top: parent.top; right: parent.right; topMargin: 46; rightMargin: 24 }
        spacing: 10
        Repeater {
            model: [ { ic: "speaker", pg: -1 }, { ic: "gear", pg: 5 } ]
            Rectangle {
                required property var modelData
                width: 34; height: 34; radius: 17
                color: Qt.rgba(0.10, 0.17, 0.45, 0.55)
                border.color: "#3b5bd0"
                opacity: modelData.ic === "speaker" && !novaBridge.voiceEnabled ? 0.45 : 1.0
                Image { anchors.centerIn: parent; width: 17; height: 17; sourceSize: Qt.size(34, 34); source: Qt.resolvedUrl("../assets/icons/" + modelData.ic + "_c.svg") }
                TapHandler { onTapped: modelData.pg >= 0 ? page.navigate(modelData.pg) : novaBridge.set_voice_enabled(!novaBridge.voiceEnabled) }
            }
        }
    }

    // Orbe
    Orb {
        x: (page.pw - size) / 2
        y: page.orbCy - size / 2
        size: page.orbItem
        mode: page.orbMode
    }

    // Textos
    NText {
        id: title
        anchors.horizontalCenter: parent.horizontalCenter
        y: page.ph * 0.51 - height / 2
        text: "NOVA"
        font.pixelSize: page.clamp(page.pw * 0.034, 30, 62)
        font.letterSpacing: page.clamp(page.pw * 0.034, 30, 62) * 0.10
        color: "white"
    }
    NText {
        id: greet
        anchors.horizontalCenter: parent.horizontalCenter
        y: page.ph * 0.585 - height / 2
        text: page.greeting() + ", " + page.userName
        font.pixelSize: page.clamp(page.pw * 0.0225, 18, 32)
        color: "#9db6ff"
    }
    NText {
        anchors.horizontalCenter: parent.horizontalCenter
        y: page.ph * 0.64 - height / 2
        text: "¿En qué puedo ayudarte hoy?"
        font.pixelSize: page.clamp(page.pw * 0.0145, 12, 20)
        color: "#e4ebff"
    }

    // Barra de entrada
    Rectangle {
        id: inputBar
        width: page.pw * 0.62
        height: page.clamp(page.ph * 0.062, 46, 60)
        x: (page.pw - width) / 2
        y: page.ph * 0.735 - height / 2
        radius: height / 2
        border.width: 1.5
        border.color: "#4a6dff"
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0; color: Qt.rgba(0.10, 0.17, 0.45, 0.72) }
            GradientStop { position: 1; color: Qt.rgba(0.07, 0.12, 0.36, 0.72) }
        }
        Rectangle { // resplandor exterior
            anchors.fill: parent; anchors.margins: -3; radius: height / 2 + 3
            color: "transparent"; border.width: 3; border.color: Qt.rgba(0.3, 0.45, 1, 0.16); z: -1
        }
        Image { x: 18; anchors.verticalCenter: parent.verticalCenter; width: 24; height: 24; sourceSize: Qt.size(48, 48); source: Qt.resolvedUrl("../assets/icons/sparkle_c.svg") }
        TextField {
            id: homeInput
            anchors { left: parent.left; right: micIcon.left; verticalCenter: parent.verticalCenter; leftMargin: 62; rightMargin: homeInput.text.trim() !== "" ? 54 : 10 }
            placeholderText: "Escribe o habla con NOVA..."
            placeholderTextColor: "#8fb0f5"
            color: "white"
            font.family: Theme.fontFamily
            font.pixelSize: 14
            background: null
            onAccepted: page.submit(text)
        }
        Rectangle {
                    visible: homeInput.text.trim() !== ""
                    anchors { right: micIcon.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
                    width: 32; height: 32; radius: 16
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: "#2447e6" }
                        GradientStop { position: 1; color: "#3b7bff" }
                    }
                    Image { anchors.centerIn: parent; width: 16; height: 16; sourceSize: Qt.size(32, 32); source: Qt.resolvedUrl("../assets/icons/send_w.svg") }
                    TapHandler { onTapped: page.submit(homeInput.text) }
                }
                Image {
                    id: micIcon
                    anchors { right: parent.right; rightMargin: 20; verticalCenter: parent.verticalCenter }
                    width: 22; height: 22; sourceSize: Qt.size(44, 44)
                    source: Qt.resolvedUrl("../assets/icons/mic_" + (page.orbMode === "listening" ? "w" : "c") + ".svg")
                    TapHandler { onTapped: novaBridge.toggle_voice_input() }
                }   
            }

    // Acciones rápidas
    Row {
        id: quick
        spacing: page.pw * 0.016
        anchors.horizontalCenter: parent.horizontalCenter
        y: page.ph * 0.895 - 34
        Repeater {
            model: [
                { ic: "folder", t: "Crear proyecto", s: "Inicia algo nuevo", pg: 3 },
                { ic: "search", t: "Buscar información", s: "Explora y aprende", pg: 1 },
                { ic: "memory", t: "Gestionar memoria", s: "Recuerda lo importante", pg: 2 },
                { ic: "chart",  t: "Abrir dashboard", s: "Ver tu progreso", pg: 4 }
            ]
            Card {
                required property var modelData
                width: page.clamp(page.pw * 0.175, 160, 260)
                height: page.clamp(page.ph * 0.085, 58, 76)
                radius: 12
                onClicked: page.navigate(modelData.pg)
                Rectangle {
                    x: 12; anchors.verticalCenter: parent.verticalCenter
                    width: 36; height: 36; radius: 9
                    color: Qt.rgba(0.14, 0.22, 0.62, 0.55); border.color: "#4a6dff"
                    Image { anchors.centerIn: parent; width: 20; height: 20; sourceSize: Qt.size(40, 40); source: Qt.resolvedUrl("../assets/icons/" + modelData.ic + "_c.svg") }
                }
                Column {
                    x: 58; anchors.verticalCenter: parent.verticalCenter; spacing: 3
                    NText { text: modelData.t; font.pixelSize: 12; font.bold: true }
                    NText { text: modelData.s; font.pixelSize: 10; color: "#7fa0f0" }
                }
            }
        }
    }
}
