"""Qt side of the window list: watches the compositor's connection and tells the dock and the bar."""
import sys

from PySide6.QtCore import Property, QObject, QSocketNotifier, Signal

from ..domain import windows as win


class WindowWatcher(QObject):
    windowsChanged = Signal(list)
    activeNameChanged = Signal()

    def __init__(self, load_entries, parent=None):
        super().__init__(parent)
        self._load_entries = load_entries
        self._client = self._notifier = None
        self._active = ""

    def start(self):
        """Connect to the compositor. False (and the shell goes on without window info) when it is not labwc."""
        try:
            from ..infra.toplevels import ToplevelClient
            self._client = ToplevelClient(self._changed)
        except Exception as exc:  # no Wayland, no protocol, or pywayland missing: the dock still launches apps
            print(f"quackos-shell: window list unavailable ({exc})", file=sys.stderr)
            return False
        self._notifier = QSocketNotifier(self._client.fileno(), QSocketNotifier.Type.Read, self)
        self._notifier.activated.connect(self._client.process)
        self._changed(self._client._tracker.snapshot())
        return True

    def activate(self, window_id):
        if self._client is not None:
            self._client.activate(window_id)

    @Property(str, notify=activeNameChanged)
    def activeName(self):
        return self._active

    def _changed(self, windows):
        name = win.active_name(windows, self._load_entries().values())
        if name != self._active:
            self._active = name
            self.activeNameChanged.emit()
        self.windowsChanged.emit(windows)
