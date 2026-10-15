import QtQuick

// "About QuackOS": version and a few facts about the machine.
Rectangle {
    id: dlg
    property var info: shellState.about()
    width: 360; height: 290; radius: 16
    color: Theme.popupBg; border.color: Theme.popupBorder; border.width: 1
    MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }

    Image { anchors.horizontalCenter: parent.horizontalCenter; y: 26; width: 84; height: 84
            source: "image://theme/quackos"; sourceSize: Qt.size(168, 168) }
    Text { anchors.horizontalCenter: parent.horizontalCenter; y: 122; text: "QuackOS"
           font.family: Theme.font; font.pixelSize: 22; font.bold: true; color: Theme.popupText }
    Text { anchors.horizontalCenter: parent.horizontalCenter; y: 154
           text: info.version !== "" ? "Versione " + info.version : "Versione di sviluppo"
           font.family: Theme.font; font.pixelSize: 13; color: Theme.popupDim }
    Text { anchors.horizontalCenter: parent.horizontalCenter; y: 180; width: parent.width - 40
           horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
           text: info.lines.join("\n"); lineHeight: 1.3
           font.family: Theme.font; font.pixelSize: 12; color: Theme.popupDim }
    Text { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 14
           text: "the distro that quacks"; font.family: Theme.font; font.pixelSize: 11; font.italic: true; color: Theme.popupDim }
}
