import QtQuick

// The logo menu (the "apple menu"): about, settings, lock, and the power actions (the dangerous ones ask first).
MenuPanel {
    panelWidth: 250
    MenuRow { text: "Informazioni su QuackOS"; onTriggered: shellState.toggle("about", 0, -1) }
    MenuSeparator {}
    MenuRow { text: "Impostazioni di sistema…"; onTriggered: shellState.toggle("control", shellState.popupX, -1) }
    MenuSeparator {}
    MenuRow { text: "Blocca lo schermo"; hint: "⌃⌘Q"; onTriggered: { shellState.close(); systemModel.lock() } }
    MenuRow { text: "Esci…"; onTriggered: shellState.toggle("confirm-logout", 0, -1) }
    MenuSeparator {}
    MenuRow { text: "Riavvia…"; onTriggered: shellState.toggle("confirm-reboot", 0, -1) }
    MenuRow { text: "Spegni…"; danger: true; onTriggered: shellState.toggle("confirm-poweroff", 0, -1) }
}
