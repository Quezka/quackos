import QtQuick

// Wi-Fi arcs: `bars` (0..4) are lit; `off` draws it dimmed with a slash.
Canvas {
    id: c
    property int bars: 0
    property bool off: false
    property color color: Theme.barText
    width: 18; height: 14
    onBarsChanged: requestPaint(); onOffChanged: requestPaint(); onColorChanged: requestPaint()
    onPaint: {
        var g = getContext("2d");
        g.reset();
        g.lineWidth = 1.9; g.lineCap = "round";
        var cx = width / 2, cy = height - 1.5;
        for (var i = 0; i < 3; i++) {
            var lit = !c.off && c.bars >= (i === 0 ? 2 : i === 1 ? 3 : 4);
            g.globalAlpha = lit ? 1.0 : 0.3;
            g.strokeStyle = c.color;
            g.beginPath();
            g.arc(cx, cy, 4.2 + i * 3.8, -3 * Math.PI / 4, -Math.PI / 4);
            g.stroke();
        }
        g.globalAlpha = (!c.off && c.bars >= 1) ? 1.0 : 0.3;
        g.fillStyle = c.color;
        g.beginPath(); g.arc(cx, cy, 1.6, 0, 2 * Math.PI); g.fill();
        if (c.off) {
            g.globalAlpha = 1.0; g.strokeStyle = c.color;
            g.beginPath(); g.moveTo(2, 1); g.lineTo(width - 2, height - 1); g.stroke();
        }
    }
}
