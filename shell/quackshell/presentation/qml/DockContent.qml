import QtQuick
import QtQuick.Window

// The floating dock. Icons grow near the pointer (a bell curve over the distance to it, like macOS); a dot marks the
// open apps; right click opens the app's menu; a new app bounces while it starts. The window is taller than the glass
// so the grown icons have room; the glass sits at the bottom.
Item {
    id: root
    property real iconSize: Theme.dockIcon
    property real peak: 1.5
    property real spread: 78
    property real pointerX: -1000
    readonly property bool hovering: pointerX > -500
    // layer-shell centres this window (it is anchored to the bottom edge only): its left edge on the screen
    readonly property real screenLeft: (Screen.width - width) / 2

    Rectangle {
        id: glass
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 8
        height: root.iconSize + 20
        width: row.width + 24
        radius: 20
        color: Theme.glass
        border.color: Theme.glassBorder
        border.width: 1
        Behavior on width { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
    }

    Row {
        id: row
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 18
        spacing: 8

        Repeater {
            model: dockModel
            delegate: Item {
                id: cell
                property bool bouncing: false
                readonly property real centerX: x + width / 2 + row.x
                readonly property real distance: root.hovering ? Math.abs(root.pointerX - centerX) : -1
                readonly property real factor: distance < 0 ? 1.0
                    : 1.0 + (root.peak - 1.0) * Math.exp(-Math.pow(distance / root.spread, 2))
                width: root.iconSize * factor
                height: root.iconSize * factor
                anchors.bottom: parent.bottom
                Behavior on width { NumberAnimation { duration: 70 } }
                Behavior on height { NumberAnimation { duration: 70 } }

                Item {
                    id: lift
                    anchors.fill: parent
                    SequentialAnimation on y {
                        running: cell.bouncing; loops: 4
                        NumberAnimation { to: -22; duration: 210; easing.type: Easing.OutQuad }
                        NumberAnimation { to: 0; duration: 210; easing.type: Easing.InQuad }
                    }
                    Image {
                        anchors.fill: parent
                        source: "image://theme/" + model.icon
                        sourceSize: Qt.size(128, 128)
                        smooth: true; mipmap: true
                    }
                }
                Timer { interval: 6000; running: cell.bouncing; onTriggered: cell.bouncing = false }
                Connections { target: model; function onRunningChanged() { if (model.running > 0) cell.bouncing = false } }

                Rectangle {  // "this app is open"
                    visible: model.running > 0
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.bottom
                    anchors.topMargin: 5
                    width: 4; height: 4; radius: 2
                    color: "#ffffff"; opacity: 0.9
                }
                Rectangle {  // tooltip with the name
                    visible: ma.containsMouse && shellState.popup === ""
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.top
                    anchors.bottomMargin: 10
                    width: tip.implicitWidth + 20; height: tip.implicitHeight + 10
                    radius: 8
                    color: "#e61c1d27"; border.color: Theme.popupBorder; border.width: 1
                    Text { id: tip; anchors.centerIn: parent; text: model.name; color: Theme.popupText
                           font.family: Theme.font; font.pixelSize: 12 }
                }
                MouseArea {
                    id: ma
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: (m) => {
                        if (m.button === Qt.RightButton) {
                            shellState.toggle("dockmenu", Math.round(root.screenLeft + cell.centerX), index)
                        } else {
                            if (model.running === 0) cell.bouncing = true
                            dockModel.open(index)
                        }
                    }
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
