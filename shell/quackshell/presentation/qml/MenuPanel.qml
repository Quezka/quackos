import QtQuick

// The frame of every popup menu: rounded, dark glass; clicks on it do not reach the "click outside to close" area.
Rectangle {
    id: panel
    default property alias content: col.data
    property int panelWidth: 240
    width: panelWidth
    height: col.implicitHeight + 16
    radius: 12
    color: Theme.popupBg
    border.color: Theme.popupBorder
    border.width: 1

    MouseArea { anchors.fill: parent; acceptedButtons: Qt.AllButtons }
    Column { id: col; x: 8; y: 8; width: parent.width - 16; spacing: 2 }
}
