import QtQuick

// One line of a menu. `danger` colours it red, `checked` puts a tick on the right, `hint` shows a shortcut.
Rectangle {
    id: row
    property string text: ""
    property string hint: ""
    property bool danger: false
    property bool checked: false
    property bool active: true
    property bool lock: false
    signal triggered()

    width: parent ? parent.width : 200
    height: 28
    radius: 6
    color: area.containsMouse && row.active ? Theme.accent : "transparent"

    Text {
        x: 10; anchors.verticalCenter: parent.verticalCenter
        width: parent.width - 20 - (hintText.visible ? hintText.width + 8 : 0)
        text: row.text; elide: Text.ElideRight
        font.family: Theme.font; font.pixelSize: 13
        color: !row.active ? Theme.popupDim : (area.containsMouse ? "#ffffff" : (row.danger ? Theme.danger : Theme.popupText))
    }
    Text {
        id: hintText
        visible: row.hint !== "" || row.checked
        anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
        text: row.checked ? "✓" : row.hint
        font.family: Theme.font; font.pixelSize: 12
        color: area.containsMouse ? "#ddddff" : Theme.popupDim
    }
    LockIcon {
        visible: row.lock
        anchors.right: parent.right; anchors.rightMargin: 10; anchors.verticalCenter: parent.verticalCenter
        color: area.containsMouse ? "#ddddff" : Theme.popupDim
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; enabled: row.active; onClicked: row.triggered() }
}
