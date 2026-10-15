import QtQuick

// Fills the screen above everything (a transparent overlay surface): a click anywhere outside the popup closes it.
// The popup itself is placed under its bar button (or above its dock icon), or centred for the dialogs.
Item {
    id: layer
    focus: true
    Keys.onEscapePressed: shellState.close()

    Connections { target: shellState; function onPopupChanged() { if (shellState.popup !== "") layer.forceActiveFocus() } }

    MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons; onPressed: shellState.close() }

    readonly property bool isDialog: shellState.popup === "about" || shellState.popup.indexOf("confirm-") === 0
    readonly property bool isDock: shellState.popup === "dockmenu"

    Loader {
        id: loader
        active: shellState.popup !== ""
        sourceComponent: {
            var p = shellState.popup;
            if (p === "logo") return logoMenu;
            if (p === "app") return appMenu;
            if (p === "wifi") return wifiPopup;
            if (p === "volume") return volumePopup;
            if (p === "battery") return batteryPopup;
            if (p === "control") return controlCenter;
            if (p === "calendar") return calendarPopup;
            if (p === "dockmenu") return dockMenu;
            if (p === "about") return aboutDialog;
            if (p.indexOf("confirm-") === 0) return confirmDialog;
            return null;
        }
        readonly property real w: item ? item.width : 0
        readonly property real h: item ? item.height : 0
        x: layer.isDialog ? (layer.width - w) / 2
           : Math.max(8, Math.min(layer.width - w - 8, shellState.popup === "logo" ? shellState.popupX - 14 : shellState.popupX - w / 2))
        y: layer.isDialog ? (layer.height - h) / 2 - 40
           : (layer.isDock ? layer.height - Theme.dockHeight - h - 6 : Theme.barHeight + 4)
        opacity: item ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 90 } }
    }

    Component { id: logoMenu; LogoMenu {} }
    Component { id: appMenu; AppMenu {} }
    Component { id: wifiPopup; WifiPopup {} }
    Component { id: volumePopup; VolumePopup {} }
    Component { id: batteryPopup; BatteryPopup {} }
    Component { id: controlCenter; ControlCenter {} }
    Component { id: calendarPopup; CalendarPopup {} }
    Component { id: dockMenu; DockMenu {} }
    Component { id: aboutDialog; AboutDialog {} }
    Component { id: confirmDialog; ConfirmDialog { kind: shellState.popup.substring(8) } }
}
