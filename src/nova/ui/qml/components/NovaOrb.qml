import QtQuick
import QtQuick.Shapes

Item {
    id: root

    property string orbState: "idle"
    property real orbScale: 1.0

    width: 320 * orbScale
    height: 320 * orbScale

    property color stateColor:
        orbState === "listening" ? "#22D3EE" :
        orbState === "processing" ? "#F59E0B" :
        orbState === "responding" ? "#38BDF8" :
        orbState === "error" ? "#EF4444" :
        "#6366F1"

    readonly property color coreColor: "#E8F7FF"

    property real stateIntensity:
        orbState === "listening" ? 1.0 :
        orbState === "processing" ? 1.0 :
        orbState === "responding" ? 1.0 :
        orbState === "error" ? 1.0 :
        1.0

    property real statePulse:
        orbState === "processing" ? 0.14 :
        orbState === "listening" ? 0.10 :
        orbState === "responding" ? 0.12 :
        orbState === "error" ? 0.16 :
        0.05

    Item {
        id: orbVisual

        anchors.centerIn: parent

        width: 270 * root.orbScale
        height: 270 * root.orbScale

        // ============================================================
        // 1. HALO PROFUNDO
        // ============================================================

        Rectangle {
            id: deepHalo

            anchors.centerIn: parent

            width: parent.width * 1.02
            height: parent.height * 1.02

            radius: width / 2

            color: root.stateColor

            opacity: 0.035 + root.statePulse

            scale: 1.0

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.94
                    to: 1.06
                    duration: root.orbState === "processing" ? 1500 : 3200
                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.06
                    to: 0.94
                    duration: root.orbState === "processing" ? 1500 : 3200
                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 2. HALO INTERMEDIO
        // ============================================================

        Rectangle {
            id: middleHalo

            anchors.centerIn: parent

            width: parent.width * 0.88
            height: parent.height * 0.88

            radius: width / 2

            color: root.stateColor

            opacity:
                root.orbState === "idle" ? 0.045 :
                root.orbState === "listening" ? 0.10 :
                root.orbState === "processing" ? 0.12 :
                root.orbState === "responding" ? 0.10 :
                0.12

            scale: 1.0

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.97
                    to: 1.03
                    duration: 2200
                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.03
                    to: 0.97
                    duration: 2200
                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 3. PULSOS DE ENERGÍA
        // ============================================================

        Repeater {
            id: energyPulseRepeater

            model: 3

            Rectangle {
                id: energyPulse

                anchors.centerIn: parent

                width: parent.width * 0.34
                height: parent.height * 0.34

                radius: width / 2

                color: "transparent"

                border.width:
                    root.orbState === "processing"
                        ? 2.0
                        : 1.2

                border.color: root.stateColor

                opacity: 0.0

                scale: 0.55

                SequentialAnimation on scale {
                    running: true
                    loops: Animation.Infinite

                    PauseAnimation {
                        duration:
                            index *
                            (
                                root.orbState === "processing"
                                    ? 260
                                    : 520
                            )
                    }

                    NumberAnimation {
                        from: 0.55
                        to:
                            root.orbState === "processing"
                                ? 1.55
                                : 1.35

                        duration:
                            root.orbState === "processing"
                                ? 900
                                : 1800

                        easing.type: Easing.OutCubic
                    }

                    NumberAnimation {
                        from:
                            root.orbState === "processing"
                                ? 0.72
                                : 0.58

                        to: 0.0

                        duration:
                            root.orbState === "processing"
                                ? 900
                                : 1800

                        easing.type: Easing.InCubic
                    }

                    PropertyAction {
                        target: energyPulse
                        property: "scale"
                        value: 0.55
                    }
                }

                SequentialAnimation on opacity {
                    running: true
                    loops: Animation.Infinite

                    PauseAnimation {
                        duration:
                            index *
                            (
                                root.orbState === "processing"
                                    ? 260
                                    : 520
                            )
                    }

                    NumberAnimation {
                        from: 0.0
                        to:
                            root.orbState === "error"
                                ? 0.0
                                : root.orbState === "idle"
                                    ? 0.16
                                    : 0.42

                        duration:
                            root.orbState === "processing"
                                ? 250
                                : 450

                        easing.type: Easing.OutCubic
                    }

                    NumberAnimation {
                        from:
                            root.orbState === "processing"
                                ? 0.72
                                : 0.58

                        to: 0.0

                        duration:
                            root.orbState === "processing"
                                ? 650
                                : 1350

                        easing.type: Easing.InCubic
                    }

                    PropertyAction {
                        target: energyPulse
                        property: "opacity"
                        value: 0.0
                    }
                }
            }
        }



        // ============================================================
        // 3. ÓRBITA EXTERIOR PRINCIPAL
        // ============================================================

        Shape {
            id: outerOrbit

            anchors.centerIn: parent

            width: parent.width * 0.94
            height: parent.height * 0.94

            antialiasing: true
            preferredRendererType: Shape.CurveRenderer

            opacity:
                root.orbState === "idle" ? 0.72 :
                root.orbState === "listening" ? 0.95 :
                root.orbState === "processing" ? 1.0 :
                root.orbState === "responding" ? 0.95 :
                1.0

            ShapePath {
                fillColor: "transparent"

                strokeColor: root.stateColor
                strokeWidth: 1.15

                startX: outerOrbit.width * 0.78
                startY: outerOrbit.height * 0.18

                PathArc {
                    x: outerOrbit.width * 0.18
                    y: outerOrbit.height * 0.82

                    radiusX: outerOrbit.width * 0.40
                    radiusY: outerOrbit.height * 0.40

                    useLargeArc: false
                    direction: PathArc.Clockwise
                }
            }

            RotationAnimation on rotation {
                running: true
                loops: Animation.Infinite

                from: 0
                to: 360

                duration:
                    root.orbState === "processing" ? 7000 :
                    root.orbState === "listening" ? 11000 :
                    18000

                easing.type: Easing.Linear
            }
        }

        // ============================================================
        // 4. ÓRBITA EXTERIOR SECUNDARIA
        // ============================================================

        Shape {
            id: secondaryOrbit

            anchors.centerIn: parent

            width: parent.width * 0.84
            height: parent.height * 0.84

            antialiasing: true
            preferredRendererType: Shape.CurveRenderer

            opacity: 0.42

            ShapePath {
                fillColor: "transparent"

                strokeColor: root.stateColor
                strokeWidth: 0.85

                startX: secondaryOrbit.width * 0.20
                startY: secondaryOrbit.height * 0.30

                PathArc {
                    x: secondaryOrbit.width * 0.80
                    y: secondaryOrbit.height * 0.70

                    radiusX: secondaryOrbit.width * 0.36
                    radiusY: secondaryOrbit.height * 0.36

                    useLargeArc: false
                    direction: PathArc.Counterclockwise
                }
            }

            RotationAnimation on rotation {
                running: true
                loops: Animation.Infinite

                from: 360
                to: 0

                duration:
                    root.orbState === "processing" ? 5200 :
                    13000

                easing.type: Easing.Linear
            }
        }

        // ============================================================
        // 5. PARTÍCULAS ENERGÉTICAS
        // ============================================================

        Item {
            id: energyParticles

            anchors.centerIn: parent

            width: parent.width * 0.78
            height: parent.height * 0.78

            opacity:
                root.orbState === "idle" ? 0.32 :
                root.orbState === "listening" ? 0.82 :
                root.orbState === "processing" ? 0.72 :
                root.orbState === "responding" ? 0.86 :
                0.18

            rotation: 0

            RotationAnimation on rotation {
                running: true
                loops: Animation.Infinite

                from: 0
                to: 360

                duration:
                    root.orbState === "processing" ? 4200 :
                    root.orbState === "listening" ? 8000 :
                    root.orbState === "responding" ? 6500 :
                    15000

                easing.type: Easing.Linear
            }

            Repeater {
                model: 8

                Rectangle {
                    width:
                        (index % 3 === 0 ? 5 : 3)
                        * root.orbScale

                    height: width

                    radius: width / 2

                    color: root.stateColor

                    opacity:
                        index % 3 === 0 ? 0.80 : 0.48

                    x: {
                        var angle =
                            (index / 8.0) * Math.PI * 2

                        var radius =
                            parent.width *
                            (index % 2 === 0 ? 0.39 : 0.33)

                        return (
                            parent.width / 2 +
                            Math.cos(angle) * radius -
                            width / 2
                        )
                    }

                    y: {
                        var angle =
                            (index / 8.0) * Math.PI * 2

                        var radius =
                            parent.height *
                            (index % 2 === 0 ? 0.39 : 0.33)

                        return (
                            parent.height / 2 +
                            Math.sin(angle) * radius -
                            height / 2
                        )
                    }

                    scale: 1.0

                    SequentialAnimation on scale {
                        running: true
                        loops: Animation.Infinite

                        PauseAnimation {
                            duration: index * 110
                        }

                        NumberAnimation {
                            from: 0.65
                            to:
                                root.orbState === "processing"
                                    ? 1.45
                                    : 1.15

                            duration:
                                root.orbState === "processing"
                                    ? 450
                                    : 900

                            easing.type: Easing.InOutSine
                        }

                        NumberAnimation {
                            from:
                                root.orbState === "processing"
                                    ? 1.45
                                    : 1.15
                            to: 0.65

                            duration:
                                root.orbState === "processing"
                                    ? 450
                                    : 900

                            easing.type: Easing.InOutSine
                        }
                    }
                }
            }
        }

        // ============================================================
        // 5. ANILLO EXTERIOR
        // ============================================================

        Rectangle {
            id: outerRing

            anchors.centerIn: parent

            width: parent.width * 0.80
            height: parent.height * 0.80

            radius: width / 2

            color: "transparent"

            border.width: 1.4
            border.color: root.stateColor

            opacity:
                root.orbState === "idle" ? 0.45 :
                root.orbState === "processing" ? 0.78 :
                0.62

            RotationAnimation on rotation {
                running: true
                loops: Animation.Infinite

                from: 360
                to: 0

                duration: 15000

                easing.type: Easing.Linear
            }
        }

        // ============================================================
        // 6. ANILLO INTERNO
        // ============================================================

        Rectangle {
            id: innerRing

            anchors.centerIn: parent

            width: parent.width * 0.70
            height: parent.height * 0.70

            radius: width / 2

            color: "transparent"

            border.width: 2
            border.color: root.stateColor

            opacity:
                root.orbState === "idle" ? 0.30 :
                root.orbState === "listening" ? 0.58 :
                root.orbState === "processing" ? 0.65 :
                root.orbState === "responding" ? 0.58 :
                0.72

            scale: 1.0

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.965
                    to: 1.035
                    duration:
                        root.orbState === "processing"
                            ? 1000
                            : 2600

                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.035
                    to: 0.965
                    duration:
                        root.orbState === "processing"
                            ? 1000
                            : 2600

                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 7. ENERGÍA LATERAL IZQUIERDA
        // ============================================================

        Shape {
            id: leftEnergy

            anchors.centerIn: parent

            width: parent.width * 0.92
            height: parent.height * 0.56

            antialiasing: true
            preferredRendererType: Shape.CurveRenderer

            opacity:
                root.orbState === "listening" ? 0.92 :
                root.orbState === "responding" ? 0.72 :
                root.orbState === "processing" ? 0.40 :
                0.10

            ShapePath {
                fillColor: "transparent"

                strokeColor: root.stateColor

                strokeWidth:
                    root.orbState === "listening"
                        ? 2.0
                        : 1.2

                startX: leftEnergy.width * 0.05
                startY: leftEnergy.height * 0.50

                PathCubic {
                    x: leftEnergy.width * 0.43
                    y: leftEnergy.height * 0.50

                    control1X: leftEnergy.width * 0.17
                    control1Y: leftEnergy.height * 0.20

                    control2X: leftEnergy.width * 0.30
                    control2Y: leftEnergy.height * 0.80
                }
            }

            SequentialAnimation on scale {
                running:
                    root.orbState === "listening" ||
                    root.orbState === "responding"

                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.94
                    to: 1.08
                    duration: 700
                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.08
                    to: 0.94
                    duration: 700
                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 8. ENERGÍA LATERAL DERECHA
        // ============================================================

        Shape {
            id: rightEnergy

            anchors.centerIn: parent

            width: parent.width * 0.92
            height: parent.height * 0.56

            antialiasing: true
            preferredRendererType: Shape.CurveRenderer

            opacity:
                root.orbState === "listening" ? 0.88 :
                root.orbState === "responding" ? 0.94 :
                root.orbState === "processing" ? 0.42 :
                0.08

            ShapePath {
                fillColor: "transparent"

                strokeColor: root.stateColor

                strokeWidth:
                    root.orbState === "responding"
                        ? 2.0
                        : 1.15

                startX: rightEnergy.width * 0.95
                startY: rightEnergy.height * 0.50

                PathCubic {
                    x: rightEnergy.width * 0.57
                    y: rightEnergy.height * 0.50

                    control1X: rightEnergy.width * 0.83
                    control1Y: rightEnergy.height * 0.80

                    control2X: rightEnergy.width * 0.70
                    control2Y: rightEnergy.height * 0.20
                }
            }

            SequentialAnimation on scale {
                running:
                    root.orbState === "listening" ||
                    root.orbState === "responding"

                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.95
                    to: 1.10
                    duration: 820
                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.10
                    to: 0.95
                    duration: 820
                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 9. CAPA ORGÁNICA
        // ============================================================

        Rectangle {
            id: organicLayer

            anchors.centerIn: parent

            width: parent.width * 0.59
            height: parent.height * 0.59

            radius: width / 2

            color: root.stateColor

            opacity:
                root.orbState === "idle" ? 0.075 :
                root.orbState === "listening" ? 0.12 :
                root.orbState === "processing" ? 0.16 :
                root.orbState === "responding" ? 0.13 :
                0.16

            border.width: 2
            border.color: root.stateColor

            rotation: 0

            SequentialAnimation on rotation {
                running: true
                loops: Animation.Infinite

                NumberAnimation {
                    from: -8
                    to: 8

                    duration:
                        root.orbState === "processing"
                            ? 1300
                            : 3200

                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 8
                    to: -8

                    duration:
                        root.orbState === "processing"
                            ? 1300
                            : 3200

                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 10. SEGUNDA CAPA ORGÁNICA
        // ============================================================

        Rectangle {
            id: organicInner

            anchors.centerIn: parent

            width: parent.width * 0.51
            height: parent.height * 0.51

            radius: width / 2

            color: root.stateColor

            opacity:
                root.orbState === "idle" ? 0.06 :
                root.orbState === "processing" ? 0.13 :
                0.10

            scale: 1.0

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.94
                    to: 1.06

                    duration:
                        root.orbState === "processing"
                            ? 800
                            : 2100

                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.06
                    to: 0.94

                    duration:
                        root.orbState === "processing"
                            ? 800
                            : 2100

                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 11. NÚCLEO OSCURO
        // ============================================================

        Rectangle {
            id: coreShell

            anchors.centerIn: parent

            width: parent.width * 0.43
            height: parent.height * 0.43

            radius: width / 2

            color: "#081021"

            border.width: 1.8
            border.color: root.stateColor

            opacity: 0.98

            scale:
                root.orbState === "processing"
                    ? 1.04
                    : 1.0

            Behavior on scale {
                NumberAnimation {
                    duration: 500
                    easing.type: Easing.OutCubic
                }
            }
        }

        // ============================================================
        // 12. REFLEJO INTERNO
        // ============================================================

        Rectangle {
            id: innerReflection

            anchors.centerIn: parent

            width: parent.width * 0.34
            height: parent.height * 0.34

            radius: width / 2

            color: root.stateColor

            opacity:
                root.orbState === "idle" ? 0.24 :
                root.orbState === "listening" ? 0.38 :
                root.orbState === "processing" ? 0.48 :
                root.orbState === "responding" ? 0.42 :
                0.48

            scale: 1.0

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.90
                    to: 1.10

                    duration:
                        root.orbState === "processing"
                            ? 700
                            : 1900

                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.10
                    to: 0.90

                    duration:
                        root.orbState === "processing"
                            ? 700
                            : 1900

                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 13. ENERGÍA CENTRAL
        // ============================================================

        Rectangle {
            id: innerEnergy

            anchors.centerIn: parent

            width: parent.width * 0.255
            height: parent.height * 0.255

            radius: width / 2

            color: root.stateColor

            opacity:
                root.orbState === "idle" ? 0.58 :
                root.orbState === "listening" ? 0.86 :
                root.orbState === "processing" ? 0.88 :
                root.orbState === "responding" ? 0.82 :
                0.90

            scale: 1.0

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.91
                    to: 1.09

                    duration:
                        root.orbState === "processing"
                            ? 600
                            : 1500

                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.09
                    to: 0.91

                    duration:
                        root.orbState === "processing"
                            ? 600
                            : 1500

                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 14. NÚCLEO LUMINOSO
        // ============================================================

        Rectangle {
            id: luminousCore

            anchors.centerIn: parent

            width: parent.width * 0.17
            height: parent.height * 0.17

            radius: width / 2

            color: root.coreColor

            opacity:
                root.orbState === "error"
                    ? 0.92
                    : 0.98

            scale: 1.0

            SequentialAnimation on scale {
                running: true
                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.91
                    to: 1.09

                    duration:
                        root.orbState === "processing"
                            ? 550
                            : 1400

                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 1.09
                    to: 0.91

                    duration:
                        root.orbState === "processing"
                            ? 550
                            : 1400

                    easing.type: Easing.InOutSine
                }
            }
        }

        // ============================================================
        // 15. PUNTO CENTRAL
        // ============================================================

        Rectangle {
            id: corePoint

            anchors.centerIn: parent

            width: parent.width * 0.065
            height: parent.height * 0.065

            radius: width / 2

            color: "white"

            opacity: 1.0

            scale:
                root.orbState === "processing"
                    ? 1.18
                    : 1.0

            Behavior on scale {
                NumberAnimation {
                    duration: 350
                    easing.type: Easing.OutCubic
                }
            }
        }

        // ============================================================
        // 16. BRILLO CENTRAL SUPERIOR
        // ============================================================

        Rectangle {
            id: coreHighlight

            anchors.centerIn: parent

            anchors.verticalCenterOffset:
                -parent.height * 0.035

            width: parent.width * 0.055
            height: parent.height * 0.028

            radius: height / 2

            color: "white"

            opacity: 0.72

            rotation: -18
        }

        // ============================================================
        // 17. ERROR — ANILLO DE ALERTA
        // ============================================================

        Rectangle {
            id: errorRing

            anchors.centerIn: parent

            width: parent.width * 0.76
            height: parent.height * 0.76

            radius: width / 2

            color: "transparent"

            border.width: 2
            border.color: "#EF4444"

            opacity:
                root.orbState === "error"
                    ? 0.90
                    : 0.0

            scale:
                root.orbState === "error"
                    ? 1.0
                    : 0.88

            SequentialAnimation on opacity {
                running: root.orbState === "error"
                loops: Animation.Infinite

                NumberAnimation {
                    from: 0.35
                    to: 0.95
                    duration: 500
                    easing.type: Easing.InOutSine
                }

                NumberAnimation {
                    from: 0.95
                    to: 0.35
                    duration: 500
                    easing.type: Easing.InOutSine
                }
            }
        }
    }

    // ============================================================
    // 18. INDICADOR DE ERROR
    // ============================================================

    Text {
        id: errorIndicator

        anchors.centerIn: parent

        text: "!"
        visible: root.orbState === "error"

        color: "#FFFFFF"

        font.family: "Segoe UI"
        font.bold: true
        font.pixelSize: 34 * root.orbScale

        opacity: 0.95

        scale: 1.0

        SequentialAnimation on scale {
            running: root.orbState === "error"
            loops: Animation.Infinite

            NumberAnimation {
                from: 0.90
                to: 1.12
                duration: 500
                easing.type: Easing.InOutSine
            }

            NumberAnimation {
                from: 1.12
                to: 0.90
                duration: 500
                easing.type: Easing.InOutSine
            }
        }
    }

    // ================================================================
    // TRANSICIÓN DE COLOR
    // ================================================================

    Behavior on stateColor {
        ColorAnimation {
            duration: 450
            easing.type: Easing.InOutCubic
        }
    }
}
