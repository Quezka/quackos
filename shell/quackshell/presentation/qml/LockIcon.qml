import QtQuick

// A small padlock (for protected Wi-Fi networks), built from two rounded rectangles.
Item {
    id: c
    property color color: Theme.popupDim
    width: 11; height: 14
    Rectangle { x: 2.2; y: 0.6; width: 6.6; height: 8; radius: 3.3; color: "transparent"; border.color: c.color; border.width: 1.6 }
    Rectangle { x: 0; y: 6; width: 11; height: 8; radius: 2; color: c.color }
}
