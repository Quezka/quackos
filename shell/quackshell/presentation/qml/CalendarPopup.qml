import QtQuick

// The clock's popup: the month, with today marked; the arrows move a month.
MenuPanel {
    id: panel
    panelWidth: 280
    property date shown: new Date()
    readonly property var today: new Date()

    function cells() {
        var first = new Date(shown.getFullYear(), shown.getMonth(), 1);
        var offset = (first.getDay() + 6) % 7;            // Monday first
        var out = [];
        for (var i = 0; i < 42; i++) out.push(new Date(first.getFullYear(), first.getMonth(), 1 - offset + i));
        return out;
    }

    Item {
        width: parent.width; height: 34
        Text { x: 10; anchors.verticalCenter: parent.verticalCenter
               text: { var t = Qt.locale().toString(panel.shown, "MMMM yyyy"); return t.charAt(0).toUpperCase() + t.slice(1) }
               font.family: Theme.font; font.pixelSize: 14; font.bold: true; color: Theme.popupText }
        Row {
            anchors.right: parent.right; anchors.rightMargin: 4; anchors.verticalCenter: parent.verticalCenter; spacing: 2
            Repeater {
                model: [{ t: "‹", d: -1 }, { t: "›", d: 1 }]
                delegate: Rectangle {
                    required property var modelData
                    width: 26; height: 26; radius: 6; color: ar.containsMouse ? "#33ffffff" : "transparent"
                    Text { anchors.centerIn: parent; text: modelData.t; font.pixelSize: 18; color: Theme.popupText }
                    MouseArea { id: ar; anchors.fill: parent; hoverEnabled: true
                                onClicked: panel.shown = new Date(panel.shown.getFullYear(), panel.shown.getMonth() + modelData.d, 1) }
                }
            }
        }
    }
    Grid {
        columns: 7; width: parent.width
        Repeater {
            model: ["L", "M", "M", "G", "V", "S", "D"]
            delegate: Text { width: panel.panelWidth / 7 - 2.3; height: 22; horizontalAlignment: Text.AlignHCenter; text: modelData
                             font.family: Theme.font; font.pixelSize: 11; color: Theme.popupDim }
        }
        Repeater {
            model: panel.cells()
            delegate: Rectangle {
                required property var modelData
                readonly property bool isToday: modelData.toDateString() === panel.today.toDateString()
                readonly property bool inMonth: modelData.getMonth() === panel.shown.getMonth()
                width: panel.panelWidth / 7 - 2.3; height: 30; radius: 15
                color: isToday ? Theme.accent : "transparent"
                Text { anchors.centerIn: parent; text: modelData.getDate()
                       font.family: Theme.font; font.pixelSize: 13; font.bold: isToday
                       color: isToday ? "#ffffff" : (inMonth ? Theme.popupText : "#5d6272") }
            }
        }
    }
    Item { width: 1; height: 6 }
}
