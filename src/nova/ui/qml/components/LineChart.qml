import QtQuick

Canvas {
    id: cv
    property var values: []
    property color lineColor: Theme.accentSoft
    property bool filled: true
    property real lineWidth: 2
    property real minValue: NaN   // fija el mínimo (p. ej. 0) si se desea
    property real maxValue: NaN
    property real minSpan: 0      // rango mínimo visible (evita que variaciones diminutas parezcan saltos)

    onValuesChanged: requestPaint()
    onLineColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        var n = values.length
        if (n < 2) return
        var mx = isNaN(maxValue) ? Math.max.apply(null, values) : maxValue
        var mn = isNaN(minValue) ? Math.min.apply(null, values) : minValue
        if (mx - mn < minSpan) { var mid = (mx + mn) / 2; mx = mid + minSpan / 2; mn = mid - minSpan / 2 }
        if (mx === mn) mx = mn + 1
        var pad = lineWidth + 2
        var pts = []
        for (var i = 0; i < n; i++)
            pts.push({ x: i * width / (n - 1), y: pad + (1 - (values[i] - mn) / (mx - mn)) * (height - 2 * pad) })
        ctx.beginPath()
        ctx.moveTo(pts[0].x, pts[0].y)
        for (var j = 1; j < n - 1; j++) {
            var xc = (pts[j].x + pts[j + 1].x) / 2
            var yc = (pts[j].y + pts[j + 1].y) / 2
            ctx.quadraticCurveTo(pts[j].x, pts[j].y, xc, yc)
        }
        ctx.lineTo(pts[n - 1].x, pts[n - 1].y)
        ctx.strokeStyle = lineColor
        ctx.lineWidth = lineWidth
        ctx.lineJoin = "round"
        ctx.stroke()
        if (filled) {
            ctx.lineTo(width, height)
            ctx.lineTo(0, height)
            ctx.closePath()
            var g = ctx.createLinearGradient(0, 0, 0, height)
            g.addColorStop(0, Qt.alpha(lineColor, 0.38))
            g.addColorStop(1, Qt.alpha(lineColor, 0.0))
            ctx.fillStyle = g
            ctx.fill()
        }
    }
}
