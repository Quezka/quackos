import QtQuick

// Wi-Fi: the switch and the networks in range. A new protected network asks for its password in place.
MenuPanel {
    id: panel
    panelWidth: 300
    property string asking: ""
    property string note: ""

    Connections {
        target: systemModel
        function onWifiResult(ssid, ok) { panel.note = ok ? "" : "Non sono riuscito a collegarmi a " + ssid + "."; if (ok) panel.asking = "" }
    }
    Component.onCompleted: systemModel.rescanWifi()

    Item {
        width: parent.width; height: 34
        Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: "Wi-Fi"; font.family: Theme.font; font.pixelSize: 14; font.bold: true; color: Theme.popupText }
        Rectangle {
            id: sw; anchors.right: parent.right; anchors.rightMargin: 8; anchors.verticalCenter: parent.verticalCenter
            width: 40; height: 22; radius: 11; color: systemModel.wifiEnabled ? Theme.accent : "#44ffffff"
            Rectangle { x: systemModel.wifiEnabled ? 20 : 2; y: 2; width: 18; height: 18; radius: 9; color: "#fff"
                        Behavior on x { NumberAnimation { duration: 120 } } }
            MouseArea { anchors.fill: parent; onClicked: systemModel.setWifiEnabled(!systemModel.wifiEnabled) }
        }
    }
    MenuSeparator { visible: systemModel.wifiEnabled }
    Text { visible: systemModel.wifiEnabled && systemModel.networks.length === 0; x: 10; width: parent.width - 20
           text: "Cerco reti…"; font.family: Theme.font; font.pixelSize: 12; color: Theme.popupDim; height: 28; verticalAlignment: Text.AlignVCenter }
    Repeater {
        model: systemModel.wifiEnabled ? systemModel.networks.slice(0, 8) : []
        delegate: MenuRow {
            required property var modelData
            text: modelData.ssid
            checked: modelData.active
            lock: modelData.secured && !modelData.active
            onTriggered: {
                if (modelData.active) return
                if (modelData.secured && !modelData.known) { panel.asking = modelData.ssid; pass.text = ""; pass.forceActiveFocus() }
                else { panel.note = ""; systemModel.connectWifi(modelData.ssid, "") }
            }
        }
    }
    Item {
        visible: panel.asking !== ""; width: parent.width; height: visible ? 74 : 0
        Text { x: 10; y: 4; text: "Password di " + panel.asking; font.family: Theme.font; font.pixelSize: 12; color: Theme.popupDim }
        Rectangle {
            x: 8; y: 24; width: parent.width - 16; height: 28; radius: 6; color: "#26ffffff"; border.color: Theme.accentLight; border.width: 1
            TextInput { id: pass; anchors.fill: parent; anchors.margins: 6; echoMode: TextInput.Password
                        font.family: Theme.font; font.pixelSize: 13; color: Theme.popupText; clip: true
                        onAccepted: { systemModel.connectWifi(panel.asking, text); text = "" } }
        }
        Text { x: 10; y: 55; text: "Invio per collegarsi"; font.family: Theme.font; font.pixelSize: 11; color: Theme.popupDim }
    }
    Text { visible: panel.note !== ""; x: 10; width: parent.width - 20; text: panel.note; wrapMode: Text.WordWrap
           font.family: Theme.font; font.pixelSize: 12; color: Theme.danger }
}
