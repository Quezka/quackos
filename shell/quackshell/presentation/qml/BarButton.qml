import QtQuick

// A clickable spot of the bar with a soft highlight; `pressedAt(x)` gives the screen x of its centre, where its popup opens.
Item {
    id: b
    default property alias content: holder.data
    property bool open: false
    signal pressedAt(int cx)
    implicitWidth: holder.childrenRect.width + 16
    width: implicitWidth
    height: Theme.barHeight

    Rectangle {
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width - 2; height: 22; x: 1; radius: 5
        color: b.open ? "#40ffffff" : (area.containsMouse ? Theme.barHover : "transparent")
    }
    Item {
        id: holder
        x: 8; height: parent.height
        width: childrenRect.width
    }
    MouseArea {
        id: area
        anchors.fill: parent; hoverEnabled: true
        onClicked: b.pressedAt(Math.round(b.mapToItem(null, b.width / 2, 0).x))
    }
}
