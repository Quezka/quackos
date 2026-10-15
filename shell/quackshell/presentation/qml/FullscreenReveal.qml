import QtQuick

// While a window is full screen the bar and dock are hidden; moving the pointer to the very top edge brings back a thin
// bar with the three coloured buttons (green = leave full screen) and the app name, like macOS.
Rectangle {
    id: root
    readonly property bool shown: hover.hovered
    color: shown ? Theme.barBg : "transparent"
    HoverHandler { id: hover }

    Row {
        visible: root.shown
        anchors.left: parent.left; anchors.leftMargin: 12; anchors.verticalCenter: parent.verticalCenter
        spacing: 8
        Repeater {
            model: [{ c: "#ff5f57", a: 0 }, { c: "#febc2e", a: 1 }, { c: "#28c840", a: 2 }]
            delegate: Rectangle {
                required property var modelData
                width: 13; height: 13; radius: 6.5; color: modelData.c
                border.color: "#33000000"; border.width: 1
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (modelData.a === 0) windowWatcher.closeActive()
                        else if (modelData.a === 1) windowWatcher.minimizeActive()
                        else windowWatcher.leaveFullscreen()
                    }
                }
            }
        }
        Text { leftPadding: 10; anchors.verticalCenter: parent.verticalCenter; text: windowWatcher.activeName
               font.family: Theme.font; font.pixelSize: 13; font.bold: true; color: Theme.barText }
    }
}
