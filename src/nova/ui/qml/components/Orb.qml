import QtQuick

// Orbe de NOVA. Las capas salen del diseño original (assets/orb/<estado>_<capa>.png):
//   outer = halo y aros exteriores · side = ondas laterales · body = esfera de cristal · core = brillo del núcleo
// El mismo componente sirve para el orbe grande y el permanente: solo cambia `size`.
// Estados: idle, listening, processing, responding, error
Item {
    id: root
    property string mode: "idle"
    property real size: 220
    width: size
    height: size
    implicitWidth: size
    implicitHeight: size

    readonly property string dir: Qt.resolvedUrl("../../assets/" + Theme.orbSet + "/") + mode + "_"
    readonly property int breathMs: ({ idle: 2800, listening: 1200, processing: 800, responding: 480, error: 520 })[mode] || 2800

    property real wave: 1.0     // amplitud de la forma de onda (responding)
    property real shake: 0.0    // vibración (error)

    Item {
        id: stage
        width: root.width
        height: root.height
        x: root.shake

        // Halo y aros exteriores
        Image {
            id: outerImg
            anchors.centerIn: parent
            width: root.width * Theme.orbScale; height: root.height * Theme.orbScale
            source: root.dir + "outer.png"
            smooth: true; mipmap: true
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 0.72; duration: root.breathMs * 1.6; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.72; to: 1.0; duration: root.breathMs * 1.6; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on scale {
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 1.03; duration: root.breathMs * 1.6; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.03; to: 1.0; duration: root.breathMs * 1.6; easing.type: Easing.InOutSine }
            }
            // al procesar, los aros giran
            NumberAnimation on rotation {
                running: root.mode === "processing"
                from: 0; to: 360; duration: 12000; loops: Animation.Infinite
            }
            onVisibleChanged: if (!visible) rotation = 0
        }

        // Ondas laterales
        Image {
            id: sideImg
            anchors.centerIn: parent
            width: root.width * Theme.orbScale; height: root.height * Theme.orbScale
            source: root.dir + "side.png"
            smooth: true; mipmap: true
            transform: Scale { origin.x: sideImg.width / 2; origin.y: sideImg.height / 2; yScale: root.mode === "responding" ? root.wave : 1 }

            SequentialAnimation on opacity {
                running: root.mode === "listening"
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 0.30; duration: 950; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.30; to: 1.0; duration: 950; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on scale {
                running: root.mode === "listening"
                loops: Animation.Infinite
                NumberAnimation { from: 0.96; to: 1.05; duration: 950; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.05; to: 0.96; duration: 950; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on opacity {
                running: root.mode === "processing"
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 0.35; duration: 420 }
                NumberAnimation { from: 0.35; to: 1.0; duration: 420 }
            }
        }

        // Esfera de cristal (respira y ondula levemente)
        Image {
            id: bodyImg
            anchors.centerIn: parent
            width: root.width * Theme.orbScale; height: root.height * Theme.orbScale
            source: root.dir + "body.png"
            smooth: true; mipmap: true
            Image {  // aros nítidos: viajan con el cuerpo para quedar siempre alineados
                anchors.fill: parent
                source: root.dir + "crisp.png"
                smooth: true; mipmap: true
            }
            SequentialAnimation on scale {
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 1.014; duration: root.breathMs * 1.2; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.014; to: 0.994; duration: root.breathMs * 1.2; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.994; to: 1.0; duration: root.breathMs * 0.6; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on rotation {
                loops: Animation.Infinite
                NumberAnimation { from: -2; to: 2; duration: root.mode === "processing" ? 1400 : 7000; easing.type: Easing.InOutSine }
                NumberAnimation { from: 2; to: -2; duration: root.mode === "processing" ? 1400 : 7000; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on opacity {
                running: root.mode === "error" || root.mode === "processing"
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 0.8; duration: root.breathMs; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.8; to: 1.0; duration: root.breathMs; easing.type: Easing.InOutSine }
            }
        }

        // Brillo del núcleo (pulsa)
        Image {
            anchors.centerIn: parent
            width: root.width * Theme.orbScale; height: root.height * Theme.orbScale
            source: root.dir + "core.png"
            smooth: true; mipmap: true
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                NumberAnimation { from: 0.15; to: 0.85; duration: root.breathMs; easing.type: Easing.InOutSine }
                NumberAnimation { from: 0.85; to: 0.15; duration: root.breathMs; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on scale {
                loops: Animation.Infinite
                NumberAnimation { from: 0.9; to: 1.12; duration: root.breathMs; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.12; to: 0.9; duration: root.breathMs; easing.type: Easing.InOutSine }
            }
        }
    }

    // Forma de onda al responder
    SequentialAnimation on wave {
        running: root.mode === "responding"
        loops: Animation.Infinite
        NumberAnimation { to: 0.35; duration: 230; easing.type: Easing.InOutSine }
        NumberAnimation { to: 1.25; duration: 310; easing.type: Easing.InOutSine }
        NumberAnimation { to: 0.6; duration: 190; easing.type: Easing.InOutSine }
        NumberAnimation { to: 1.0; duration: 270; easing.type: Easing.InOutSine }
    }

    // Vibración en error
    SequentialAnimation on shake {
        running: root.mode === "error"
        loops: Animation.Infinite
        NumberAnimation { to: -root.size * 0.010; duration: 70 }
        NumberAnimation { to: root.size * 0.010; duration: 70 }
        NumberAnimation { to: -root.size * 0.006; duration: 70 }
        NumberAnimation { to: 0; duration: 70 }
        PauseAnimation { duration: 900 }
    }

    onModeChanged: { wave = 1.0; shake = 0.0 }
}
