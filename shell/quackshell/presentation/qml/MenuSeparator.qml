import QtQuick

Item {
    width: parent ? parent.width : 200
    height: 9
    Rectangle { anchors.centerIn: parent; width: parent.width - 8; height: 1; color: Theme.separator }
}
