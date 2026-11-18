import QtQuick

Item {
    id: g
    property real value: 0.5          // 0..1
    property real thickness: 8
    property color c1: "#2f6bff"
    property color c2: "#9b6bff"
    default property alias content: inner.data

    Canvas {
        anchors.fill: parent
        property real v: g.value
        property real t: g.thickness
        onVChanged: requestPaint()
        onTChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var cx = width / 2, cy = height / 2
            var r = (Math.min(width, height) - t) / 2
            var a0 = -Math.PI / 2
            ctx.lineWidth = t
            ctx.lineCap = "round"
            ctx.strokeStyle = Qt.rgba(0.2, 0.3, 0.7, 0.25)
            ctx.beginPath(); ctx.arc(cx, cy, r, 0, 2 * Math.PI, false); ctx.stroke()
            var grad = ctx.createLinearGradient(0, 0, width, height)
            grad.addColorStop(0, g.c1)
            grad.addColorStop(1, g.c2)
            ctx.strokeStyle = grad
            ctx.beginPath(); ctx.arc(cx, cy, r, a0, a0 + Math.max(0.001, v) * 2 * Math.PI, false); ctx.stroke()
        }
    }
    Item { id: inner; anchors.fill: parent }
}
