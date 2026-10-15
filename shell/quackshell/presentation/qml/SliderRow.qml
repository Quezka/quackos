import QtQuick

// A horizontal slider (0..100) with a label on the left; `moved(v)` while the pointer drags.
Item {
    id: root
    property string label: ""
    property int value: 0
    property int maximum: 100
    property bool dim: false
    signal moved(int v)
    width: parent ? parent.width : 220
    height: 34

    Text {
        id: caption
        x: 10; anchors.verticalCenter: parent.verticalCenter
        text: root.label; width: 70
        font.family: Theme.font; font.pixelSize: 13; color: Theme.popupText
    }
    Rectangle {
        id: track
        x: 84; width: parent.width - 84 - 12; height: 6; radius: 3
        anchors.verticalCenter: parent.verticalCenter
        color: "#33ffffff"
        Rectangle { width: track.width * Math.min(1, root.value / root.maximum); height: parent.height; radius: 3
                    color: root.dim ? Theme.popupDim : Theme.accentLight }
        Rectangle {
            x: track.width * Math.min(1, root.value / root.maximum) - width / 2; y: -6
            width: 18; height: 18; radius: 9; color: "#ffffff"
            border.color: "#40000000"; border.width: 1
        }
    }
    MouseArea {
        x: track.x - 8; width: track.width + 16; height: parent.height
        function setFrom(mx) { root.moved(Math.round(Math.max(0, Math.min(1, (mx - 8) / track.width)) * root.maximum)) }
        onPressed: (m) => setFrom(m.x)
        onPositionChanged: (m) => { if (pressed) setFrom(m.x) }
    }
}
