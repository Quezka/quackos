import QtQuick

// A speaker; `level` 0..100 decides how many waves, `muted` draws the slash.
Canvas {
    id: c
    property int level: 50
    property bool muted: false
    property color color: Theme.barText
    width: 18; height: 14
    onLevelChanged: requestPaint(); onMutedChanged: requestPaint(); onColorChanged: requestPaint()
    onPaint: {
        var g = getContext("2d");
        g.reset();
        g.fillStyle = c.color; g.strokeStyle = c.color; g.lineWidth = 1.7; g.lineCap = "round";
        g.beginPath();
        g.moveTo(1.5, 5); g.lineTo(4.8, 5); g.lineTo(8.8, 1.5); g.lineTo(8.8, 12.5); g.lineTo(4.8, 9); g.lineTo(1.5, 9);
        g.closePath(); g.fill();
        if (!c.muted && c.level > 0) {
            g.beginPath(); g.arc(8.8, 7, 3.4, -Math.PI / 3, Math.PI / 3); g.stroke();
            if (c.level > 40) { g.beginPath(); g.arc(8.8, 7, 6.4, -Math.PI / 3, Math.PI / 3); g.stroke(); }
        } else {
            g.beginPath(); g.moveTo(11, 4.5); g.lineTo(16, 9.5); g.moveTo(16, 4.5); g.lineTo(11, 9.5); g.stroke();
        }
    }
}
