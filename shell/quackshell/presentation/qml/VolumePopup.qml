import QtQuick

MenuPanel {
    panelWidth: 260
    SliderRow { label: "Volume"; value: Math.max(0, systemModel.volume); dim: systemModel.muted
                onMoved: (v) => systemModel.setVolume(v) }
    MenuRow { text: systemModel.muted ? "Riattiva l'audio" : "Silenzia"; onTriggered: systemModel.setMuted(!systemModel.muted) }
}
