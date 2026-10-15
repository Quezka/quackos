"""Qt side of the status items (sound, brightness, battery, Wi-Fi) and of the power actions. The tools are slow and may
hang, so they run on one worker thread; the answers come back as a signal, and the sliders answer instantly (optimistic)."""
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from ..domain import status


class SystemModel(QObject):
    changed = Signal()
    _snapshot = Signal(object)
    wifiResult = Signal(str, bool)

    def __init__(self, service, interval_ms=6000, parent=None):
        super().__init__(parent)
        self._service = service
        self._s = None
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="quackshell-system")
        self._snapshot.connect(self._apply)
        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.refresh)
        self._busy = False

    def start(self):
        self._timer.start()
        self.refresh()

    # ---- reading
    @Slot()
    def refresh(self):
        if self._busy:
            return
        self._busy = True
        self._pool.submit(self._read)

    def _read(self):
        try:
            self._snapshot.emit(self._service.snapshot())
        except Exception:
            self._snapshot.emit(None)

    def _apply(self, snap):
        self._busy = False
        if snap is not None and snap != self._s:
            self._s = snap
            self.changed.emit()

    def _get(self, name, default):
        return getattr(self._s, name) if self._s is not None else default

    volume = Property(int, lambda self: self._get("volume", -1), notify=changed)
    muted = Property(bool, lambda self: self._get("muted", False), notify=changed)
    brightness = Property(int, lambda self: self._get("brightness", -1), notify=changed)
    battery = Property(int, lambda self: self._get("battery", -1), notify=changed)
    charging = Property(bool, lambda self: self._get("charging", False), notify=changed)
    wifiAvailable = Property(bool, lambda self: self._get("wifi_available", False), notify=changed)
    wifiEnabled = Property(bool, lambda self: self._get("wifi_enabled", False), notify=changed)

    @Property("QVariantList", notify=changed)
    def networks(self):
        return [{"ssid": n.ssid, "signal": n.signal, "bars": status.wifi_bars(n.signal), "secured": n.secured,
                 "active": n.active, "known": n.known} for n in self._get("networks", ())]

    @Property(int, notify=changed)
    def wifiBars(self):
        """0 = off or not connected, 1..4 = signal of the connected network."""
        active = next((n for n in self._get("networks", ()) if n.active), None)
        return status.wifi_bars(active.signal) if active else 0

    @Property(str, notify=changed)
    def wifiName(self):
        active = next((n for n in self._get("networks", ()) if n.active), None)
        return active.ssid if active else ""

    # ---- changing (the screen follows at once, the tool in the background)
    def _patch(self, **changes):
        from dataclasses import replace
        if self._s is not None:
            self._s = replace(self._s, **changes)
            self.changed.emit()

    def _later(self, fn, *args):
        self._pool.submit(fn, *args)

    @Slot(int)
    def setVolume(self, percent):
        self._patch(volume=int(percent), muted=False)
        self._later(self._service.audio.set_muted, False)
        self._later(self._service.audio.set_volume, percent)

    @Slot(bool)
    def setMuted(self, muted):
        self._patch(muted=bool(muted))
        self._later(self._service.audio.set_muted, bool(muted))

    @Slot(int)
    def setBrightness(self, percent):
        self._patch(brightness=int(percent))
        self._later(self._service.brightness.set, percent)

    @Slot(bool)
    def setWifiEnabled(self, on):
        self._patch(wifi_enabled=bool(on))
        self._later(self._service.network.set_enabled, bool(on))
        QTimer.singleShot(2500, self.refresh)

    @Slot()
    def rescanWifi(self):
        self._later(self._service.network.rescan)
        QTimer.singleShot(3000, self.refresh)

    @Slot(str, str)
    def connectWifi(self, ssid, password):
        def work():
            ok = self._service.network.connect(ssid, password)
            self.wifiResult.emit(ssid, ok)
            self._snapshot.emit(self._service.snapshot())
        self._later(work)

    # ---- power
    @Slot()
    def lock(self):
        self._service.power.lock()

    @Slot()
    def logout(self):
        self._service.power.logout()

    @Slot()
    def reboot(self):
        self._service.power.reboot()

    @Slot()
    def poweroff(self):
        self._service.power.poweroff()
