import QtQuick
import QtQuick.Layouts

// Dashboard — "Panel de control" según la referencia (Hoja 06).
// Datos reales del PC vía `backend`; actividad y accesos desde AppData.
Rectangle {
    id: page
    property string orbMode: "idle"
    property int rangeIdx: 0
    readonly property var rangeDays: [7, 30, 90]
    property var activity: []
    property int activityTotal: 0

    function refreshActivity() {
        var r = novaActivity.recent(rangeDays[rangeIdx])
        activity = r.items
        activityTotal = r.total
    }
    Component.onCompleted: refreshActivity()
    onVisibleChanged: if (visible) refreshActivity()
    onRangeIdxChanged: refreshActivity()
    Timer { interval: 10000; running: page.visible; repeat: true; onTriggered: page.refreshActivity() }
    Connections { target: novaBridge; function onConversationChanged() { if (page.visible) page.refreshActivity() } }
    Connections { target: novaMemory; function onChanged() { if (page.visible) page.refreshActivity() } }
    Connections { target: novaProjects; function onChanged() { if (page.visible) page.refreshActivity() } }
    signal navigate(int page)
    color: "#050b22"

    function icon(n, v) { return Qt.resolvedUrl("../../assets/icons/" + n + "_" + (v || "c") + ".svg") }
    function metric(k) { return k === "cpu" ? systemMetrics.cpu : (k === "ram" ? systemMetrics.ram : (k === "disk" ? systemMetrics.disk : systemMetrics.net)) }
    function hist(k) { return k === "cpu" ? systemMetrics.cpuHistory : (k === "ram" ? systemMetrics.ramHistory : (k === "disk" ? systemMetrics.diskHistory : systemMetrics.netHistory)) }
    function status(k) {
        var v = metric(k)
        if (k === "cpu") return v > 80 ? "Alto" : "Normal"
        if (k === "ram") return v > 90 ? "Crítica" : "En uso"
        if (k === "disk") return v > 90 ? "Casi lleno" : "Disponible"
        return v > 0.5 ? "Activa" : "Estable"
    }

    readonly property var meta: ({
        cpu:  { t: "CPU",     c: "#4a7bff", sc: "#2fe0a0" },
        ram:  { t: "Memoria", c: "#9b6bff", sc: "#d26bff" },
        disk: { t: "Disco",   c: "#2fe0a0", sc: "#2fe0a0" },
        net:  { t: "Red",     c: "#4a9bff", sc: "#2fe0a0" }
    })
    readonly property var ranges: ["Últimos 7 días", "Últimos 30 días", "Últimos 90 días"]
    readonly property var quick: AppData.quickActions
    readonly property var assistText: ({ idle: "En espera...", listening: "Escuchando...", processing: "Procesando...", responding: "Respondiendo...", error: "Requiere atención" })

    // rendimiento general = lo que le queda libre a CPU y memoria
    readonly property real perf: Math.max(0, 100 - (systemMetrics.cpu + systemMetrics.ram) / 2)
    property var perfHist: {
        var a = systemMetrics.cpuHistory, b = systemMetrics.ramHistory, o = []
        for (var i = 0; i < a.length; i++) o.push(100 - (a[i] + b[i]) / 2)
        return o
    }

    // forma de onda del asistente (se desplaza)
    property var wave: []
    Timer {
        interval: 120; running: true; repeat: true
        onTriggered: {
            var amp = ({ idle: 0.22, listening: 0.6, processing: 0.4, responding: 1.0, error: 0.7 })[page.orbMode] || 0.3
            var w = page.wave.slice(-47)
            var spike = Math.random() < 0.18 ? 2.2 : 1.0
            w.push(0.5 + (Math.random() - 0.5) * amp * spike)
            page.wave = w
        }
    }

    NText { x: 32; y: 38; text: "Panel de control"; font.pixelSize: 26 }
    NText { x: 32; y: 76; text: "Todo en un solo lugar."; color: "#2f8bff"; font.pixelSize: 13 }

    // selector de rango + ajustes
    Row {
        anchors { top: parent.top; right: parent.right; topMargin: 56; rightMargin: 32 }
        spacing: 10
        Rectangle {
            width: 150; height: 34; radius: 10
            color: Qt.rgba(0.07, 0.13, 0.34, 0.55); border.color: "#1f3f9a"
            NText { x: 14; anchors.verticalCenter: parent.verticalCenter; text: page.ranges[page.rangeIdx]; font.pixelSize: 11; color: "#a9bdf2" }
            Image { anchors { right: parent.right; rightMargin: 10; verticalCenter: parent.verticalCenter } width: 14; height: 14; sourceSize: Qt.size(28, 28); source: page.icon("chevron", "d") }
            TapHandler { onTapped: page.rangeIdx = (page.rangeIdx + 1) % page.ranges.length }
        }
        Rectangle {
            width: 34; height: 34; radius: 17
            color: Qt.rgba(0.07, 0.13, 0.34, 0.55); border.color: "#1f3f9a"
            Image { anchors.centerIn: parent; width: 16; height: 16; sourceSize: Qt.size(32, 32); source: page.icon("gear", "c") }
            TapHandler { onTapped: page.navigate(5) }
        }
    }

    RowLayout {
        anchors { fill: parent; topMargin: 112; leftMargin: 32; rightMargin: 32; bottomMargin: 30 }
        spacing: 16

        // ---------------- columna izquierda ----------------
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 14

            // métricas del sistema
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: false
                Layout.preferredHeight: Math.max(130, Math.min(200, page.height * 0.20))
                Layout.maximumHeight: Layout.preferredHeight
                spacing: 14
                Repeater {
                    model: ["cpu", "ram", "disk", "net"]
                    Card {
                        id: mc
                        required property string modelData
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.preferredWidth: 1
                        radius: 14
                        Column {
                            x: 18; y: 16; spacing: 3
                            NText { text: page.meta[mc.modelData].t; font.pixelSize: 12; color: "#9db4f0" }
                            NText { text: Math.round(page.metric(mc.modelData)) + "%"; font.pixelSize: 28 }
                            NText { text: page.status(mc.modelData); font.pixelSize: 11; color: page.meta[mc.modelData].sc }
                        }
                        LineChart {
                            anchors { right: parent.right; bottom: parent.bottom; rightMargin: 12; bottomMargin: 12 }
                            width: parent.width * 0.62
                            height: parent.height * 0.58
                            values: page.hist(mc.modelData)
                            lineColor: page.meta[mc.modelData].c
                            lineWidth: 1.8
                            minSpan: 25
                        }
                    }
                }
            }

            // fila inferior
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 14

                // ---- Actividad reciente: muestra tantas filas como quepan ----
                Card {
                    id: actCard
                    Layout.fillWidth: true; Layout.fillHeight: true
                    Layout.preferredWidth: 3; Layout.preferredHeight: 1
                    radius: 14
                    NText { x: 18; y: 16; text: "Actividad reciente"; font.pixelSize: 14; font.bold: true }
                    NText { anchors { right: parent.right; top: parent.top; rightMargin: 18; topMargin: 18 } text: page.activityTotal + " eventos"; font.pixelSize: 10; color: "#5d7bc0" }
                    NText { visible: page.activity.length === 0; anchors.centerIn: parent; text: "Sin actividad en este rango."; font.pixelSize: 12; color: "#6f8fe0" }
                    Column {
                        anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: 18; rightMargin: 18; topMargin: 50 }
                        Repeater {
                            model: Math.min(page.activity.length, Math.max(0, Math.floor((actCard.height - 66) / 58)))
                            Item {
                                id: ar
                                required property int index
                                readonly property var row: page.activity[index]
                                width: parent.width
                                height: 58
                                Rectangle { visible: ar.index > 0; width: parent.width; height: 1; color: "#12296a" }
                                RowLayout {
                                    anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter }
                                    spacing: 12
                                    Rectangle {
                                        Layout.preferredWidth: 30; Layout.preferredHeight: 30
                                        radius: 8; color: "#2a2fa6"; border.color: "#5b6cff"
                                        Orb { visible: ar.row.ic === "orb"; anchors.centerIn: parent; size: 24; mode: "idle" }
                                        Image {
                                            visible: ar.row.ic !== "orb"
                                            anchors.centerIn: parent; width: 16; height: 16; sourceSize: Qt.size(32, 32)
                                            source: ar.row.ic === "orb" ? "" : page.icon(ar.row.ic, "w")
                                        }
                                    }
                                    NText { Layout.preferredWidth: 80; text: ar.row.who; font.pixelSize: 12; font.bold: true }
                                    NText { Layout.fillWidth: true; text: ar.row.what; font.pixelSize: 12; color: "#6f8fe0"; elide: Text.ElideRight }
                                    NText { text: ar.row.when; font.pixelSize: 10; color: "#5d7bc0" }
                                }
                            }
                        }
                    }
                }

                // ---- Uso del sistema ----
                Card {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    Layout.preferredWidth: 2.4; Layout.preferredHeight: 1
                    radius: 14
                    ColumnLayout {
                        anchors { fill: parent; margins: 18 }
                        spacing: 12
                        NText { text: "Uso del sistema"; font.pixelSize: 14; font.bold: true }
                        Item { Layout.fillHeight: true; Layout.maximumHeight: 30 }
                        Gauge {
                            Layout.alignment: Qt.AlignHCenter
                            Layout.preferredWidth: 140; Layout.preferredHeight: 140
                            value: page.perf / 100; thickness: 11; c1: "#3d8bff"; c2: "#9b5cff"
                            Column {
                                anchors.centerIn: parent
                                NText { anchors.horizontalCenter: parent.horizontalCenter; text: Math.round(page.perf) + "%"; font.pixelSize: 28 }
                                NText { anchors.horizontalCenter: parent.horizontalCenter; text: "Rendimiento general"; font.pixelSize: 8; color: "#8fb0ff" }
                            }
                        }
                        Item { Layout.fillHeight: true; Layout.maximumHeight: 24 }
                        Repeater {
                            model: ["cpu", "ram", "disk"]
                            RowLayout {
                                id: br
                                required property string modelData
                                Layout.fillWidth: true
                                spacing: 10
                                NText { Layout.preferredWidth: 64; text: page.meta[br.modelData].t; font.pixelSize: 11; color: "#9db4f0" }
                                NovaBar {
                                    Layout.fillWidth: true
                                    value: page.metric(br.modelData) / 100
                                    c1: page.meta[br.modelData].c; c2: page.meta[br.modelData].c
                                }
                                NText { Layout.preferredWidth: 34; horizontalAlignment: Text.AlignRight; text: Math.round(page.metric(br.modelData)) + "%"; font.pixelSize: 11 }
                            }
                        }
                        Item { Layout.fillHeight: true }
                        LineChart {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 90
                            values: page.perfHist
                            lineColor: "#4a7bff"
                            minSpan: 30
                        }
                        NText { text: "Rendimiento general"; font.pixelSize: 10; color: "#8fb0ff"; Layout.alignment: Qt.AlignRight }
                    }
                }

                // ---- Estado del asistente ----
                Card {
                    id: stCard
                    Layout.fillWidth: true; Layout.fillHeight: true
                    Layout.preferredWidth: 2.4; Layout.preferredHeight: 1
                    radius: 14
                    ColumnLayout {
                        anchors { fill: parent; margins: 18 }
                        spacing: 8
                        NText { text: "Estado del asistente"; font.pixelSize: 14; font.bold: true }
                        Item { Layout.fillHeight: true }
                        Item {
                            Layout.alignment: Qt.AlignHCenter
                            readonly property real s: Math.max(120, Math.min(220, stCard.width * 0.55))
                            Layout.preferredWidth: s; Layout.preferredHeight: s * 0.85
                            Orb { anchors.centerIn: parent; size: parent.s; mode: page.orbMode }
                        }
                        NText {
                            Layout.alignment: Qt.AlignHCenter
                            text: page.orbMode === "error" ? "Atención" : "Activo"
                            font.pixelSize: 14; font.bold: true
                            color: page.orbMode === "error" ? "#ff5a78" : "#2fe0a0"
                        }
                        NText { Layout.alignment: Qt.AlignHCenter; text: page.assistText[page.orbMode] || ""; font.pixelSize: 12; color: "#cfe0ff" }
                        Item { Layout.fillHeight: true }
                        LineChart {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 90
                            filled: false; lineWidth: 1.5; lineColor: "#4a7bff"
                            minValue: 0; maxValue: 1
                            values: page.wave
                        }
                    }
                }
            }
        }

        // ---------------- Accesos rápidos + información del sistema ----------------
        Card {
            Layout.preferredWidth: Math.max(230, Math.min(290, page.width * 0.20))
            Layout.fillHeight: true
            radius: 14
            ColumnLayout {
                anchors { fill: parent; margins: 16 }
                spacing: 10
                NText { text: "Accesos rápidos"; font.pixelSize: 14; font.bold: true; Layout.leftMargin: 2; Layout.bottomMargin: 4 }
                Repeater {
                    model: page.quick
                    Card {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 46
                        radius: 10
                        onClicked: if (modelData.pg >= 0) page.navigate(modelData.pg)
                        Image { x: 14; anchors.verticalCenter: parent.verticalCenter; width: 18; height: 18; sourceSize: Qt.size(36, 36); source: page.icon(modelData.ic, "c") }
                        NText { x: 44; anchors.verticalCenter: parent.verticalCenter; text: modelData.t; font.pixelSize: 12 }
                    }
                }
                Item { Layout.fillHeight: true }
                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: "#12296a" }
                NText { text: "Información del sistema"; font.pixelSize: 13; font.bold: true; Layout.topMargin: 4 }
                Repeater {
                    model: [
                        { l: "Tiempo activo", v: systemMetrics.sysUptime },
                        { l: "Procesos", v: systemMetrics.sysProcs },
                        { l: "Núcleos CPU", v: systemMetrics.sysCores },
                        { l: "Memoria RAM", v: systemMetrics.sysRam }
                    ]
                    RowLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        NText { text: modelData.l; font.pixelSize: 11; color: "#8fb0ff"; Layout.fillWidth: true }
                        NText { text: modelData.v; font.pixelSize: 12 }
                    }
                }
                Item { Layout.preferredHeight: 6 }
            }
        }
    }
}
