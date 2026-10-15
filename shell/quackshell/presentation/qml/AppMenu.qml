import QtQuick

// The menu of the app in front (its bold name in the bar): hide it or quit it.
MenuPanel {
    panelWidth: 230
    MenuRow { text: "Nascondi " + windowWatcher.activeName; hint: "⌘H"
              onTriggered: { shellState.close(); windowWatcher.hideActiveApp() } }
    MenuSeparator {}
    MenuRow { text: "Esci da " + windowWatcher.activeName; hint: "⌘Q"
              onTriggered: { shellState.close(); windowWatcher.quitActiveApp() } }
}
