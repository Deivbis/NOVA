import QtQuick
import QtQuick.Shapes

Item {
    id: root

    // ============================================================
    // PROPIEDADES DE ESTADO Y ESCALA
    // ============================================================
    property string orbState: "idle" // "idle", "listening", "processing", "responding", "error"
    property real orbScale: 1.0

    implicitWidth: 320 * orbScale
    implicitHeight: 320 * orbScale

    // Transición suave de color según el estado
    property color stateColor:
        orbState === "listening"  ? "#00F2FE" : // Cian brillante
        orbState === "processing" ? "#FF9900" : // Ámbar / Naranja
        orbState === "responding" ? "#0066FF" : // Azul eléctrico
        orbState === "error"      ? "#FF1744" : // Rojo / Neón magenta
        "#5B21B6"                              // Púrpura profundo (Idle)

    Behavior on stateColor {
        ColorAnimation { duration: 400; easing.type: Easing.InOutQuad }
    }

    readonly property color coreColor: "#FFFFFF"

    Item {
        id: orbVisual
        anchors.centerIn: parent
        width: 280 * root.orbScale
        height: 280 * root.orbScale

        // ============================================================
        // SECCIÓN 1: HALO DE GLOW PROFUNDO EXTERIOR
        // ============================================================
        Rectangle {
            id: deepHalo
            anchors.centerIn: parent
            width: parent.width * 1.05
            height: parent.height * 1.05
            radius: width / 2
            color: "transparent"
            border.color: root.stateColor
            border.width: 18
            opacity: root.orbState === "processing" ? 0.28 : 0.12

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite
                NumberAnimation { from: 0.94; to: 1.06; duration: root.orbState === "processing" ? 800 : 2800; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.06; to: 0.94; duration: root.orbState === "processing" ? 800 : 2800; easing.type: Easing.InOutSine }
            }
        }

        // ============================================================
        // SECCIÓN 2: HALO INTERMEDIO Y RESPLANDOR
        // ============================================================
        Rectangle {
            id: middleHalo
            anchors.centerIn: parent
            width: parent.width * 0.90
            height: parent.height * 0.90
            radius: width / 2
            color: root.stateColor
            opacity: root.orbState === "error" ? 0.20 : 0.08

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite
                NumberAnimation { from: 0.97; to: 1.03; duration: 2000; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.03; to: 0.97; duration: 2000; easing.type: Easing.InOutSine }
            }
        }

        // ============================================================
        // SECCIÓN 3: PULSOS Y ONDAS DE ENERGÍA DE FONDO
        // ============================================================
        Repeater {
            id: energyPulseRepeater
            model: 3

            Rectangle {
                required property int index
                anchors.centerIn: parent
                width: parent.width * 0.40
                height: parent.height * 0.40
                radius: width / 2
                color: "transparent"
                border.width: root.orbState === "processing" ? 2.0 : 1.2
                border.color: root.stateColor
                opacity: 0.0
                scale: 0.55

                SequentialAnimation on scale {
                    running: true
                    loops: Animation.Infinite
                    PauseAnimation { duration: index * (root.orbState === "processing" ? 250 : 500) }
                    NumberAnimation { from: 0.55; to: root.orbState === "processing" ? 1.55 : 1.35; duration: root.orbState === "processing" ? 900 : 1800; easing.type: Easing.OutCubic }
                    NumberAnimation { from: root.orbState === "processing" ? 1.55 : 1.35; to: 0.55; duration: 0 }
                }

                SequentialAnimation on opacity {
                    running: true
                    loops: Animation.Infinite
                    PauseAnimation { duration: index * (root.orbState === "processing" ? 250 : 500) }
                    NumberAnimation { from: 0.0; to: root.orbState === "error" ? 0.0 : 0.35; duration: 400; easing.type: Easing.OutCubic }
                    NumberAnimation { from: 0.35; to: 0.0; duration: root.orbState === "processing" ? 500 : 1400; easing.type: Easing.InCubic }
                }
            }
        }

        // ============================================================
        // SECCIÓN 4: ONDAS LATERALES DE AUDIO IZQUIERDAS
        // ============================================================
        Item {
            id: leftAudioWaves
            anchors.verticalCenter: parent.verticalCenter
            x: -parent.width * 0.15
            width: parent.width * 0.3
            height: parent.height * 0.4
            opacity: (root.orbState === "listening" || root.orbState === "responding" || root.orbState === "idle") ? 0.9 : 0.15

            Repeater {
                model: 6
                Rectangle {
                    required property int index
                    anchors.verticalCenter: parent.verticalCenter
                    x: index * 9 * root.orbScale
                    width: 3 * root.orbScale
                    height: (12 + Math.sin(index) * 10) * root.orbScale
                    radius: width / 2
                    color: root.stateColor

                    SequentialAnimation on height {
                        running: root.orbState === "listening" || root.orbState === "responding"
                        loops: Animation.Infinite
                        PauseAnimation { duration: index * 70 }
                        NumberAnimation { from: 8 * root.orbScale; to: (22 + index * 4) * root.orbScale; duration: root.orbState === "listening" ? 280 : 420; easing.type: Easing.InOutSine }
                        NumberAnimation { from: (22 + index * 4) * root.orbScale; to: 8 * root.orbScale; duration: root.orbState === "listening" ? 280 : 420; easing.type: Easing.InOutSine }
                    }
                }
            }
        }

        // ============================================================
        // SECCIÓN 5: ONDAS LATERALES DE AUDIO DERECHAS
        // ============================================================
        Item {
            id: rightAudioWaves
            anchors.verticalCenter: parent.verticalCenter
            x: parent.width * 0.85
            width: parent.width * 0.3
            height: parent.height * 0.4
            opacity: (root.orbState === "listening" || root.orbState === "responding" || root.orbState === "idle") ? 0.9 : 0.15

            Repeater {
                model: 6
                Rectangle {
                    required property int index
                    anchors.verticalCenter: parent.verticalCenter
                    x: index * 9 * root.orbScale
                    width: 3 * root.orbScale
                    height: (12 + Math.cos(index) * 10) * root.orbScale
                    radius: width / 2
                    color: root.stateColor

                    SequentialAnimation on height {
                        running: root.orbState === "listening" || root.orbState === "responding"
                        loops: Animation.Infinite
                        PauseAnimation { duration: (5 - index) * 70 }
                        NumberAnimation { from: 8 * root.orbScale; to: (22 + (5 - index) * 4) * root.orbScale; duration: root.orbState === "listening" ? 280 : 420; easing.type: Easing.InOutSine }
                        NumberAnimation { from: (22 + (5 - index) * 4) * root.orbScale; to: 8 * root.orbScale; duration: root.orbState === "listening" ? 280 : 420; easing.type: Easing.InOutSine }
                    }
                }
            }
        }

        // ============================================================
        // SECCIÓN 6: ÓRBITA EXTERIOR PRINCIPAL (Shape Path Arc)
        // ============================================================
        Shape {
            id: outerOrbit
            anchors.centerIn: parent
            width: parent.width * 0.92
            height: parent.height * 0.92
            antialiasing: true
            preferredRendererType: Shape.CurveRenderer

            ShapePath {
                fillColor: "transparent"
                strokeColor: root.stateColor
                strokeWidth: 1.8
                capStyle: ShapePath.RoundCap

                startX: outerOrbit.width * 0.8
                startY: outerOrbit.height * 0.2

                PathArc {
                    x: outerOrbit.width * 0.2
                    y: outerOrbit.height * 0.8
                    radiusX: outerOrbit.width * 0.42
                    radiusY: outerOrbit.height * 0.42
                    useLargeArc: false
                    direction: PathArc.Clockwise
                }
            }

            RotationAnimation on rotation {
                running: true
                loops: Animation.Infinite
                from: 0; to: 360
                duration: root.orbState === "processing" ? 5000 : 14000
                easing.type: Easing.Linear
            }
        }

        // ============================================================
        // SECCIÓN 7: ÓRBITA EXTERIOR SECUNDARIA CONTRA-ROTATORIA
        // ============================================================
        Shape {
            id: secondaryOrbit
            anchors.centerIn: parent
            width: parent.width * 0.84
            height: parent.height * 0.84
            antialiasing: true
            preferredRendererType: Shape.CurveRenderer
            opacity: 0.6

            ShapePath {
                fillColor: "transparent"
                strokeColor: root.stateColor
                strokeWidth: 1.2

                startX: secondaryOrbit.width * 0.15
                startY: secondaryOrbit.height * 0.35

                PathArc {
                    x: secondaryOrbit.width * 0.85
                    y: secondaryOrbit.height * 0.65
                    radiusX: secondaryOrbit.width * 0.38
                    radiusY: secondaryOrbit.height * 0.38
                    useLargeArc: false
                    direction: PathArc.Counterclockwise
                }
            }

            RotationAnimation on rotation {
                running: true
                loops: Animation.Infinite
                from: 360; to: 0
                duration: root.orbState === "processing" ? 3800 : 10000
                easing.type: Easing.Linear
            }
        }

        // ============================================================
        // SECCIÓN 8: ANILLO EXTERIOR DELIMITADOR
        // ============================================================
        Rectangle {
            id: outerRing
            anchors.centerIn: parent
            width: parent.width * 0.78
            height: parent.height * 0.78
            radius: width / 2
            color: "transparent"
            border.width: 1.2
            border.color: root.stateColor
            opacity: root.orbState === "processing" ? 0.8 : 0.45

            RotationAnimation on rotation {
                running: true
                loops: Animation.Infinite
                from: 0; to: 360
                duration: 16000
                easing.type: Easing.Linear
            }
        }

        // ============================================================
        // SECCIÓN 9: ANILLO INTERNO DENTRO DE LA ESTRUCTURA
        // ============================================================
        Rectangle {
            id: innerRing
            anchors.centerIn: parent
            width: parent.width * 0.66
            height: parent.height * 0.66
            radius: width / 2
            color: "transparent"
            border.width: 1.8
            border.color: root.stateColor
            opacity: 0.6

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite
                NumberAnimation { from: 0.96; to: 1.04; duration: root.orbState === "processing" ? 900 : 2200; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.04; to: 0.96; duration: root.orbState === "processing" ? 900 : 2200; easing.type: Easing.InOutSine }
            }
        }

        // ============================================================
        // SECCIÓN 10: SISTEMA DE PARTÍCULAS ORBITALES Y ENERGÍA
        // ============================================================
        Item {
            id: energyParticles
            anchors.centerIn: parent
            width: parent.width * 0.72
            height: parent.height * 0.72

            RotationAnimation on rotation {
                running: true
                loops: Animation.Infinite
                from: 0; to: 360
                duration: root.orbState === "processing" ? 3500 : 11000
                easing.type: Easing.Linear
            }

            Repeater {
                model: 8
                Rectangle {
                    required property int index
                    width: (index % 3 === 0 ? 5 : 3) * root.orbScale
                    height: width
                    radius: width / 2
                    color: root.stateColor
                    opacity: index % 2 === 0 ? 0.85 : 0.50

                    x: (parent.width / 2) + Math.cos((index / 8.0) * Math.PI * 2) * (parent.width * 0.4) - width / 2
                    y: (parent.height / 2) + Math.sin((index / 8.0) * Math.PI * 2) * (parent.height * 0.4) - height / 2

                    SequentialAnimation on scale {
                        running: true
                        loops: Animation.Infinite
                        PauseAnimation { duration: index * 100 }
                        NumberAnimation { from: 0.7; to: root.orbState === "processing" ? 1.4 : 1.1; duration: 600; easing.type: Easing.InOutSine }
                        NumberAnimation { from: root.orbState === "processing" ? 1.4 : 1.1; to: 0.7; duration: 600; easing.type: Easing.InOutSine }
                    }
                }
            }
        }

        // ============================================================
        // SECCIÓN 11: ENERGÍA CURVA SUPERIOR
        // ============================================================
        Shape {
            id: topEnergy
            anchors.centerIn: parent
            width: parent.width * 0.8
            height: parent.height * 0.8
            antialiasing: true

            ShapePath {
                fillColor: "transparent"
                strokeColor: root.stateColor
                strokeWidth: 1.5
                capStyle: ShapePath.RoundCap

                startX: topEnergy.width * 0.25
                startY: topEnergy.height * 0.25

                PathCubic {
                    x: topEnergy.width * 0.75
                    y: topEnergy.height * 0.25
                    control1X: topEnergy.width * 0.4
                    control1Y: topEnergy.height * 0.1
                    control2X: topEnergy.width * 0.6
                    control2Y: topEnergy.height * 0.1
                }
            }
        }

        // ============================================================
        // SECCIÓN 12: ENERGÍA CURVA INFERIOR
        // ============================================================
        Shape {
            id: bottomEnergy
            anchors.centerIn: parent
            width: parent.width * 0.8
            height: parent.height * 0.8
            antialiasing: true

            ShapePath {
                fillColor: "transparent"
                strokeColor: root.stateColor
                strokeWidth: 1.5
                capStyle: ShapePath.RoundCap

                startX: bottomEnergy.width * 0.25
                startY: bottomEnergy.height * 0.75

                PathCubic {
                    x: bottomEnergy.width * 0.75
                    y: bottomEnergy.height * 0.75
                    control1X: bottomEnergy.width * 0.4
                    control1Y: bottomEnergy.height * 0.9
                    control2X: bottomEnergy.width * 0.6
                    control2Y: bottomEnergy.height * 0.9
                }
            }
        }

        // ============================================================
        // SECCIÓN 13: RESPLANDOR EXTERIOR DEL NÚCLEO
        // ============================================================
        Rectangle {
            id: coreOuterGlow
            anchors.centerIn: parent
            width: parent.width * 0.45
            height: parent.height * 0.45
            radius: width / 2
            color: root.stateColor
            opacity: 0.35

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite
                NumberAnimation { from: 0.88; to: 1.15; duration: 1100; easing.type: Easing.InOutSine }
                NumberAnimation { from: 1.15; to: 0.88; duration: 1100; easing.type: Easing.InOutSine }
            }
        }

        // ============================================================
        // SECCIÓN 14: HALO LUMINOSO INTERMEDIO DEL NÚCLEO
        // ============================================================
        Rectangle {
            id: coreMidHalo
            anchors.centerIn: parent
            width: parent.width * 0.32
            height: parent.height * 0.32
            radius: width / 2
            color: root.stateColor
            opacity: 0.65
        }

        // ============================================================
        // SECCIÓN 15: BRANQUIAS Y RESPLANDOR INTENSO CENTRAL
        // ============================================================
        Rectangle {
            id: coreGlowIntense
            anchors.centerIn: parent
            width: parent.width * 0.22
            height: parent.height * 0.22
            radius: width / 2
            color: root.coreColor
            border.color: root.stateColor
            border.width: 2.5

            SequentialAnimation on opacity {
                running: root.orbState === "listening" || root.orbState === "processing"
                loops: Animation.Infinite
                NumberAnimation { from: 0.8; to: 1.0; duration: 300 }
                NumberAnimation { from: 1.0; to: 0.8; duration: 300 }
            }
        }

        // ============================================================
        // SECCIÓN 16: PUNTO BLANCO CENTRAL RADIANTE (NÚCLEO FINAL)
        // ============================================================
        Rectangle {
            id: coreCenterDot
            anchors.centerIn: parent
            width: parent.width * 0.12
            height: parent.height * 0.12
            radius: width / 2
            color: root.coreColor
            visible: root.orbState !== "error"
        }

        // ============================================================
        // SECCIÓN 17: ÍCONO TRIANGULAR DE ALERTA (ESTADO ERROR)
        // ============================================================
        Item {
            id: errorTriangle
            anchors.centerIn: parent
            width: parent.width * 0.32
            height: parent.height * 0.32
            visible: root.orbState === "error"

            Shape {
                anchors.fill: parent
                antialiasing: true

                ShapePath {
                    fillColor: "transparent"
                    strokeColor: "#FFFFFF"
                    strokeWidth: 2.5
                    capStyle: ShapePath.RoundCap
                    joinStyle: ShapePath.MiterJoin

                    startX: errorTriangle.width * 0.5
                    startY: errorTriangle.height * 0.12
                    PathLine { x: errorTriangle.width * 0.88; y: errorTriangle.height * 0.85 }
                    PathLine { x: errorTriangle.width * 0.12; y: errorTriangle.height * 0.85 }
                    PathLine { x: errorTriangle.width * 0.5;  y: errorTriangle.height * 0.12 }
                }

                // Signo de exclamación (Línea)
                ShapePath {
                    fillColor: "#FFFFFF"
                    strokeColor: "#FFFFFF"
                    strokeWidth: 2.2
                    capStyle: ShapePath.RoundCap

                    startX: errorTriangle.width * 0.5
                    startY: errorTriangle.height * 0.38
                    PathLine { x: errorTriangle.width * 0.5; y: errorTriangle.height * 0.60 }
                }

                // Signo de exclamación (Punto)
                ShapePath {
                    fillColor: "#FFFFFF"
                    strokeColor: "#FFFFFF"
                    strokeWidth: 2.5

                    startX: errorTriangle.width * 0.5
                    startY: errorTriangle.height * 0.71
                    PathLine { x: errorTriangle.width * 0.5; y: errorTriangle.height * 0.73 }
                }
            }

            // Parpadeo intermitente de alerta
            SequentialAnimation on opacity {
                running: root.orbState === "error"
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 0.3; duration: 350 }
                NumberAnimation { from: 0.3; to: 1.0; duration: 350 }
            }
        }

        // ============================================================
        // SECCIÓN 18: CAPA FINAL DE DESTELLO Y VIBRACIÓN DE ESTADO
        // ============================================================
        SequentialAnimation on x {
            running: root.orbState === "error"
            loops: Animation.Infinite
            NumberAnimation { from: -2; to: 2; duration: 50 }
            NumberAnimation { from: 2; to: -2; duration: 50 }
            NumberAnimation { from: -2; to: 0; duration: 50 }
            PauseAnimation { duration: 400 }
        }
    }
}