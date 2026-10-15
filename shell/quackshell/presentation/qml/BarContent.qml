import QtQuick

// The top bar. Left: the logo menu and the name of the focused app (its menu hides or quits it). Right: Wi-Fi, sound,
// battery, the control centre and the clock, each opening a popup (PopupLayer).
Rectangle {
    id: root
    color: Theme.barBg
    readonly property string popup: shellState.popup

    Row {
        anchors.left: parent.left; anchors.leftMargin: 6
        height: parent.height

        BarButton {
            open: root.popup === "logo"
            onPressedAt: (cx) => shellState.toggle("logo", cx, -1)
            Image {
                y: 4; width: 20; height: 20; sourceSize: Qt.size(40, 40); smooth: true
                source: "image://theme/quackos"
            }
        }
        BarButton {
            open: root.popup === "app"
            visible: windowWatcher.activeName !== ""
            onPressedAt: (cx) => shellState.toggle("app", cx, -1)
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: windowWatcher.activeName
                color: Theme.barText; font.family: Theme.font; font.pixelSize: 13; font.bold: true
            }
        }
        Text {
            visible: windowWatcher.activeName === ""
            anchors.verticalCenter: parent.verticalCenter
            leftPadding: 8
            text: "QuackOS"; color: Theme.barText; font.family: Theme.font; font.pixelSize: 13; font.bold: true
        }
    }

    Row {
        anchors.right: parent.right; anchors.rightMargin: 6
        height: parent.height

        BarButton {
            visible: systemModel.wifiAvailable
            open: root.popup === "wifi"
            onPressedAt: (cx) => shellState.toggle("wifi", cx, -1)
            WifiIcon { y: 7; bars: systemModel.wifiBars; off: !systemModel.wifiEnabled }
        }
        BarButton {
            visible: systemModel.volume >= 0
            open: root.popup === "volume"
            onPressedAt: (cx) => shellState.toggle("volume", cx, -1)
            VolumeIcon { y: 7; level: systemModel.volume; muted: systemModel.muted }
        }
        BarButton {
            visible: systemModel.battery >= 0
            open: root.popup === "battery"
            onPressedAt: (cx) => shellState.toggle("battery", cx, -1)
            Row {
                spacing: 6; y: 7
                BatteryIcon { percent: systemModel.battery; charging: systemModel.charging }
                Text { text: systemModel.battery + "%"; color: Theme.barText; font.family: Theme.font; font.pixelSize: 12
                       anchors.verticalCenter: parent.verticalCenter }
            }
        }
        BarButton {
            open: root.popup === "control"
            onPressedAt: (cx) => shellState.toggle("control", cx, -1)
            ControlIcon { y: 7 }
        }
        BarButton {
            open: root.popup === "calendar"
            onPressedAt: (cx) => shellState.toggle("calendar", cx, -1)
            Text {
                id: clock
                anchors.verticalCenter: parent.verticalCenter
                color: Theme.barText; font.family: Theme.font; font.pixelSize: 13
                function tick() { text = Qt.locale().toString(new Date(), "ddd d MMM  HH:mm") }
                Component.onCompleted: tick()
                Timer { interval: 1000; running: true; repeat: true; onTriggered: clock.tick() }
            }
        }
    }
}
