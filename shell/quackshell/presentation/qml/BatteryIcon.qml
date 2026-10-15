import QtQuick

// A battery with its level; green when charging, red when low.
Item {
    id: b
    property int percent: 100
    property bool charging: false
    property color color: Theme.barText
    width: 26; height: 14
    Rectangle { x: 0; y: 1; width: 22; height: 12; radius: 3.5; color: "transparent"; border.color: b.color; border.width: 1.2; opacity: 0.85 }
    Rectangle { x: 22.8; y: 4.5; width: 2; height: 5; radius: 1; color: b.color; opacity: 0.7 }
    Rectangle {
        x: 2; y: 3; height: 8; radius: 2
        width: 18 * Math.max(0, Math.min(100, b.percent)) / 100
        color: b.charging ? Theme.ok : (b.percent <= 15 ? Theme.danger : b.color)
    }
}
