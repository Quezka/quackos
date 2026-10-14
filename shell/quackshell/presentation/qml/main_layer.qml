import QtQuick
import QtQuick.Window
import org.kde.layershell 1.0 as LayerShell

// The bar and the dock as layer-shell surfaces: the bar reserves its height at the top, the dock (anchored only to
// the bottom edge, so the compositor centres it) reserves the glass plus its margin; the room above the glass
// for the grown icons is not reserved.
QtObject {
    property var bar: Window {
        visible: true
        title: "QuackOS bar"
        width: Screen.width; height: barHeight
        color: "transparent"
        LayerShell.Window.scope: "quackos-bar"
        LayerShell.Window.layer: LayerShell.Window.LayerTop
        LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
        LayerShell.Window.exclusionZone: barHeight
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
        BarContent { anchors.fill: parent }
    }
    property var dock: Window {
        visible: true
        title: "QuackOS dock"
        width: 760; height: 128
        color: "transparent"
        LayerShell.Window.scope: "quackos-dock"
        LayerShell.Window.layer: LayerShell.Window.LayerTop
        LayerShell.Window.anchors: LayerShell.Window.AnchorBottom
        LayerShell.Window.exclusionZone: 82
        LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityNone
        DockContent { anchors.fill: parent }
    }
}
