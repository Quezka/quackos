import QtQuick
import QtQuick.Window

// The same windows as main_layer.qml as ordinary windows: for trying the shell inside another desktop, and for the tests.
QtObject {
    property var bar: Window {
        visible: true
        title: "QuackOS bar"
        width: 1000; height: Theme.barHeight
        color: "transparent"
        BarContent { anchors.fill: parent }
    }
    property var dock: Window {
        visible: true
        title: "QuackOS dock"
        width: 820; height: 140
        color: "transparent"
        DockContent { anchors.fill: parent }
    }
    property var popups: Window {
        visible: shellState.popup !== ""
        title: "QuackOS popups"
        width: 1000; height: 640
        color: "transparent"
        PopupLayer { anchors.fill: parent }
    }
}
