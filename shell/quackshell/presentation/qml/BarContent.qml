import QtQuick

// The top bar: logo (opens the launcher) on the left, date and time on the right. Phase 2 adds the app menu,
// the status icons and the control centre.
Rectangle {
    id: root
    color: "#cc16181d"

    Row {
        anchors.left: parent.left
        anchors.leftMargin: 14
        anchors.verticalCenter: parent.verticalCenter
        spacing: 8

        Item {
            width: 20; height: 20
            anchors.verticalCenter: parent.verticalCenter
            Image {
                anchors.fill: parent
                source: "image://theme/quackos"
                sourceSize: Qt.size(40, 40)
                smooth: true
            }
            MouseArea { anchors.fill: parent; onClicked: launcher.openLauncher() }
        }
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: windowWatcher.activeName !== "" ? windowWatcher.activeName : "QuackOS"
            color: "#ecedef"
            font.pixelSize: 13
            font.bold: true
        }
    }

    Text {
        id: clock
        anchors.right: parent.right
        anchors.rightMargin: 14
        anchors.verticalCenter: parent.verticalCenter
        color: "#ecedef"
        font.pixelSize: 13
        function tick() { text = Qt.locale().toString(new Date(), "ddd d MMM  HH:mm") }
        Component.onCompleted: tick()
        Timer { interval: 1000; running: true; repeat: true; onTriggered: clock.tick() }
    }
}
