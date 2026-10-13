import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    Timer {
        interval: 6000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }


    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#14152e"
            Text {
                anchors.centerIn: parent
                horizontalAlignment: Text.AlignHCenter
                color: "#ffffff"
                font.pixelSize: 26
                text: "🦆\n\nWelcome to QuackOS\nThe distro that quacks."
            }
        }
    }
    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#14152e"
            Text {
                anchors.centerIn: parent
                horizontalAlignment: Text.AlignHCenter
                color: "#ffffff"
                font.pixelSize: 24
                text: "Stagno, Quire, Ligature, Gantry,\nBivouac and Natter are already here.\n\nThey update themselves."
            }
        }
    }
    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#14152e"
            Text {
                anchors.centerIn: parent
                horizontalAlignment: Text.AlignHCenter
                color: "#ffffff"
                font.pixelSize: 24
                text: "Type  quack  in a terminal\nfor the pond report."
            }
        }
    }
}
