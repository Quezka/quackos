import QtQuick

MenuPanel {
    panelWidth: 230
    Item { width: parent.width; height: 44
        Text { x: 10; y: 4; text: systemModel.battery + "%"; font.family: Theme.font; font.pixelSize: 20; font.bold: true; color: Theme.popupText }
        Text { x: 10; y: 28; text: systemModel.charging ? "In carica" : "A batteria"; font.family: Theme.font; font.pixelSize: 12; color: Theme.popupDim } }
}
