import QtQuick

// Two toggle switches: the "control centre" icon.
Item {
    id: c
    property color color: Theme.barText
    width: 18; height: 14
    Rectangle { x: 1; y: 1; width: 16; height: 5; radius: 2.5; color: "transparent"; border.color: c.color; border.width: 1.2 }
    Rectangle { x: 10; y: 1.8; width: 3.6; height: 3.6; radius: 1.8; color: c.color }
    Rectangle { x: 1; y: 8; width: 16; height: 5; radius: 2.5; color: "transparent"; border.color: c.color; border.width: 1.2 }
    Rectangle { x: 3.4; y: 8.8; width: 3.6; height: 3.6; radius: 1.8; color: c.color }
}
