import QtQuick

// The control centre: the quick settings of the machine in one place.
MenuPanel {
    panelWidth: 320
    Text { x: 10; text: "Centro di controllo"; height: 30; verticalAlignment: Text.AlignVCenter
           font.family: Theme.font; font.pixelSize: 14; font.bold: true; color: Theme.popupText }
    Item {
        visible: systemModel.wifiAvailable; width: parent.width; height: visible ? 52 : 0
        Rectangle {
            x: 4; y: 2; width: parent.width - 8; height: 48; radius: 10; color: wifiArea.containsMouse ? "#33ffffff" : "#1fffffff"
            Rectangle { x: 10; y: 9; width: 30; height: 30; radius: 15; color: systemModel.wifiEnabled ? Theme.accent : "#44ffffff"
                        WifiIcon { anchors.centerIn: parent; bars: systemModel.wifiBars > 0 ? systemModel.wifiBars : 4; off: !systemModel.wifiEnabled; color: "#ffffff" } }
            Text { x: 50; y: 8; text: "Wi-Fi"; font.family: Theme.font; font.pixelSize: 13; font.bold: true; color: Theme.popupText }
            Text { x: 50; y: 26; width: parent.width - 60; elide: Text.ElideRight
                   text: !systemModel.wifiEnabled ? "Spento" : (systemModel.wifiName !== "" ? systemModel.wifiName : "Non collegato")
                   font.family: Theme.font; font.pixelSize: 12; color: Theme.popupDim }
            MouseArea { id: wifiArea; anchors.fill: parent; hoverEnabled: true; onClicked: shellState.toggle("wifi", shellState.popupX, -1) }
        }
    }
    SliderRow { visible: systemModel.volume >= 0; height: visible ? 34 : 0; label: "Audio"; value: Math.max(0, systemModel.volume)
                dim: systemModel.muted; onMoved: (v) => systemModel.setVolume(v) }
    SliderRow { visible: systemModel.brightness >= 0; height: visible ? 34 : 0; label: "Schermo"; value: Math.max(1, systemModel.brightness)
                onMoved: (v) => systemModel.setBrightness(Math.max(1, v)) }
    MenuSeparator {}
    MenuRow { text: "Blocca lo schermo"; hint: "⌃⌘Q"; onTriggered: { shellState.close(); systemModel.lock() } }
}
