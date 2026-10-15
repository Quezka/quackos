import QtQuick

// Right click on a dock icon: open / hide / quit, and keep it in the dock or not.
MenuPanel {
    id: panel
    panelWidth: 220
    property var info: dockModel.info(shellState.popupData)
    property int row: shellState.popupData

    Text { x: 10; width: parent.width - 20; height: 26; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight
           text: info.name || ""; font.family: Theme.font; font.pixelSize: 12; font.bold: true; color: Theme.popupDim }
    MenuRow { text: info.running ? "Nuova finestra" : "Apri"; onTriggered: { shellState.close(); dockModel.newWindow(row) } }
    MenuRow { visible: info.running > 0; height: visible ? 28 : 0; text: "Nascondi"
              onTriggered: { shellState.close(); dockModel.hide(row) } }
    MenuRow { visible: info.running > 0; height: visible ? 28 : 0; text: "Esci"; danger: true
              onTriggered: { shellState.close(); dockModel.quit(row) } }
    MenuSeparator { visible: info.canPin; height: visible ? 9 : 0 }
    MenuRow { visible: info.canPin; height: visible ? 28 : 0; text: "Tieni nel Dock"; checked: info.pinned
              onTriggered: { shellState.close(); dockModel.togglePin(row) } }
}
