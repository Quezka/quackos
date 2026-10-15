import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell

// The shell as layer-shell surfaces: the bar (top, reserves its height), the dock (bottom, centred, reserves the glass),
// the popup layer (above everything, only while a popup is open) and the thin "reveal" strip at the top edge while a window is full screen.
QtObject {
    property var bar: Window {
        visible: true
        title: "QuackOS bar"
        width: Screen.width; height: Theme.barHeight
        color: "transparent"
        LayerShell.Window.scope: "quackos-bar"
        LayerShell.Window.layer: LayerShell.Window.LayerTop
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
        LayerShell.Window.exclusionZone: Theme.barHeight
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
        BarContent { anchors.fill: parent }
    }
    property var dock: Window {
        visible: true
        title: "QuackOS dock"
        width: 820; height: 140
        color: "transparent"
        LayerShell.Window.scope: "quackos-dock"
        LayerShell.Window.layer: LayerShell.Window.LayerTop
        LayerShell.Window.anchors: LayerShell.Window.AnchorBottom
        LayerShell.Window.exclusionZone: Theme.dockIcon + 28
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
        DockContent { anchors.fill: parent }
    }
    property var popups: Window {
        visible: shellState.popup !== ""
        title: "QuackOS popups"
        width: Screen.width; height: Screen.height
        color: "transparent"
        LayerShell.Window.scope: "quackos-popups"
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
        LayerShell.Window.exclusionZone: -1
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityOnDemand
        PopupLayer { anchors.fill: parent }
    }
    property var reveal: Window {
        visible: windowWatcher.fullscreen
        title: "QuackOS fullscreen reveal"
        width: Screen.width; height: revealContent.shown ? Theme.barHeight : 3
        color: "transparent"
        LayerShell.Window.scope: "quackos-reveal"
        LayerShell.Window.layer: LayerShell.Window.LayerOverlay
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
        LayerShell.Window.exclusionZone: -1   // -1: ignore the (hidden) bar's reserved space, sit on the very top edge
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
        FullscreenReveal { id: revealContent; anchors.fill: parent }
    }
}
