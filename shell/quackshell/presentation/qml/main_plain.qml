import QtQuick
import QtQuick.Window

// Same two windows as main_layer.qml, as ordinary windows: for trying the shell inside another desktop.
QtObject {
    property var bar: Window {
        visible: true
        title: "QuackOS bar"
        width: 1000; height: barHeight
        color: "transparent"
        BarContent { anchors.fill: parent }
    }
    property var dock: Window {
        visible: true
        title: "QuackOS dock"
        width: 640; height: 128
        color: "transparent"
        DockContent { anchors.fill: parent }
    }
}
