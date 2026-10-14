import QtQuick

// The floating dock. Icons grow near the pointer (a bell curve over the distance to it, like macOS). The window
// is taller than the glass so the grown icons have room; the glass sits at the bottom.
Item {
    id: root
    property real iconSize: 48
    property real peak: 1.55
    property real spread: 70
    property real pointerX: -1000
    readonly property bool hovering: pointerX > -500

    // the glass is as wide as the icons at rest, plus padding
    Rectangle {
        id: glass
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 6
        height: root.iconSize + 22
        width: row.width + 24
        radius: 18
        color: "#b816181d"
        border.color: "#33ffffff"
        border.width: 1
        Behavior on width { NumberAnimation { duration: 120 } }
    }

    Row {
        id: row
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 17
        spacing: 6

        Repeater {
            model: dockModel
            delegate: Item {
                id: cell
                readonly property real centerX: x + width / 2 + row.x
                readonly property real distance: root.hovering ? Math.abs(root.pointerX - centerX) : -1
                readonly property real factor: distance < 0 ? 1.0
                    : 1.0 + (root.peak - 1.0) * Math.exp(-Math.pow(distance / root.spread, 2))
                width: root.iconSize * factor
                height: root.iconSize * factor
                anchors.bottom: parent.bottom
                Behavior on width { NumberAnimation { duration: 60 } }
                Behavior on height { NumberAnimation { duration: 60 } }

                Image {
                    anchors.fill: parent
                    source: "image://theme/" + model.icon
                    sourceSize: Qt.size(128, 128)
                    smooth: true
                    mipmap: true
                }
                Rectangle {  // the "this app is open" dot under the icon
                    visible: model.running > 0
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.bottom
                    anchors.topMargin: 5
                    width: 4; height: 4; radius: 2
                    color: "#ecedef"
                }
                Rectangle {
                    visible: ma.containsMouse
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.top
                    anchors.bottomMargin: 8
                    width: tip.implicitWidth + 16; height: tip.implicitHeight + 8
                    radius: 7
                    color: "#e616181d"
                    Text { id: tip; anchors.centerIn: parent; text: model.name; color: "#ecedef"; font.pixelSize: 12 }
                }
                MouseArea {
                    id: ma
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: dockModel.open(index)
                }
            }
        }
    }

    // follows the pointer over the whole dock window, including the gaps between icons
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
        onPositionChanged: (m) => root.pointerX = m.x
        onExited: root.pointerX = -1000
    }
}
