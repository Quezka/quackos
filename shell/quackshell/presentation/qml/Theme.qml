pragma Singleton
import QtQuick

// Colours and sizes of the QuackOS shell (the indigo of the suite apps, on a glass look like macOS).
QtObject {
    readonly property color barBg: "#cc151622"
    readonly property color barText: "#f4f5f9"
    readonly property color barDim: "#aeb2c0"
    readonly property color barHover: "#33ffffff"
    readonly property color glass: "#3dffffff"
    readonly property color glassBorder: "#66ffffff"
    readonly property color popupBg: "#f01c1d27"
    readonly property color popupBorder: "#38ffffff"
    readonly property color popupText: "#f4f5f9"
    readonly property color popupDim: "#9ea3b4"
    readonly property color separator: "#26ffffff"
    readonly property color accent: "#5b5bd6"
    readonly property color accentLight: "#8182f0"
    readonly property color danger: "#ff6369"
    readonly property color ok: "#30d158"
    readonly property string font: "Inter"
    readonly property int barHeight: 28
    readonly property int dockIcon: 52
    readonly property int dockHeight: 92
}
