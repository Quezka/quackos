import QtQuick

// "Are you sure?" for log out / restart / shut down, centred like a macOS alert.
Rectangle {
    id: dlg
    property string kind: "poweroff"
    readonly property var texts: ({
        "poweroff": { title: "Vuoi spegnere il computer?", yes: "Spegni", run: function () { systemModel.poweroff() } },
        "reboot":   { title: "Vuoi riavviare il computer?", yes: "Riavvia", run: function () { systemModel.reboot() } },
        "logout":   { title: "Vuoi uscire dalla sessione?", yes: "Esci", run: function () { systemModel.logout() } }
    })
    width: 340; height: 150; radius: 16
    color: Theme.popupBg; border.color: Theme.popupBorder; border.width: 1
    MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }

    Image { x: 20; y: 22; width: 44; height: 44; source: "image://theme/quackos"; sourceSize: Qt.size(88, 88) }
    Text { x: 78; y: 24; width: parent.width - 98; text: texts[kind].title; wrapMode: Text.WordWrap
           font.family: Theme.font; font.pixelSize: 15; font.bold: true; color: Theme.popupText }
    Text { x: 78; y: 52; width: parent.width - 98; text: "Salva il lavoro nelle app aperte prima di continuare."; wrapMode: Text.WordWrap
           font.family: Theme.font; font.pixelSize: 12; color: Theme.popupDim }
    Row {
        anchors.right: parent.right; anchors.rightMargin: 18; anchors.bottom: parent.bottom; anchors.bottomMargin: 16
        spacing: 10
        Rectangle {
            width: 96; height: 30; radius: 8; color: cancelArea.containsMouse ? "#40ffffff" : "#26ffffff"
            Text { anchors.centerIn: parent; text: "Annulla"; font.family: Theme.font; font.pixelSize: 13; color: Theme.popupText }
            MouseArea { id: cancelArea; anchors.fill: parent; hoverEnabled: true; onClicked: shellState.close() }
        }
        Rectangle {
            width: 96; height: 30; radius: 8; color: yesArea.containsMouse ? "#ff7a80" : Theme.danger
            Text { anchors.centerIn: parent; text: texts[kind].yes; font.family: Theme.font; font.pixelSize: 13; font.bold: true; color: "#ffffff" }
            MouseArea { id: yesArea; anchors.fill: parent; hoverEnabled: true
                        onClicked: { shellState.close(); texts[kind].run() } }
        }
    }
}
