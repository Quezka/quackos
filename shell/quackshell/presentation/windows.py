"""Qt side of the window list: watches the compositor's connection and tells the dock and the bar."""
import sys

from PySide6.QtCore import Property, QObject, QSocketNotifier, Signal, Slot

from ..domain import windows as win


class WindowWatcher(QObject):
    windowsChanged = Signal(list)
    activeNameChanged = Signal()
    fullscreenChanged = Signal()

    def __init__(self, load_entries, parent=None):
        super().__init__(parent)
        self._load_entries = load_entries
        self._client = self._notifier = None
        self._active = ""
        self._fullscreen = False
        self._windows = []

    def start(self):
        """Connect to the compositor. False (and the shell goes on without window info) when it is not labwc."""
        try:
            from ..infra.toplevels import ToplevelClient
            self._client = ToplevelClient(self._changed)
        except Exception as exc:  # no Wayland, no protocol, or pywayland missing: the dock still launches apps
            print(f"quackos-shell: window list unavailable ({exc})", file=sys.stderr)
            return False
        self._notifier = QSocketNotifier(self._client.fileno(), QSocketNotifier.Type.Read, self)
        self._notifier.activated.connect(self._process)
        self._changed(self._client._tracker.snapshot())
        return True

    def _process(self, *_):
        try:
            self._client.process()
        except Exception as exc:  # a protocol hiccup must not kill the bar
            print(f"quackos-shell: window list error ({exc!r})", file=sys.stderr)

    def stop(self):
        if self._notifier is not None:
            self._notifier.setEnabled(False)
        if self._client is not None:
            self._client.shutdown()
            self._client = None

    # ---- what the dock and the bar call
    def activate(self, window_id):
        if self._client is not None:
            self._client.activate(window_id)

    def close_window(self, window_id):
        if self._client is not None:
            self._client.close_window(window_id)

    def minimize_window(self, window_id):
        if self._client is not None:
            self._client.minimize(window_id)

    def _app_windows(self):
        current = win.active_window(self._windows)
        return win.windows_of(current, self._windows, self._load_entries().values()) if current else []

    @Slot()
    def quitActiveApp(self):
        for w in self._app_windows():
            self.close_window(w.id)

    @Slot()
    def hideActiveApp(self):
        for w in self._app_windows():
            self.minimize_window(w.id)

    @Slot()
    def closeActive(self):
        current = win.active_window(self._windows)
        if current:
            self.close_window(current.id)

    @Slot()
    def minimizeActive(self):
        current = win.active_window(self._windows)
        if current:
            self.minimize_window(current.id)

    @Slot()
    def leaveFullscreen(self):
        current = win.active_window(self._windows)
        if current and self._client is not None:
            self._client.leave_fullscreen(current.id)

    @Property(str, notify=activeNameChanged)
    def activeName(self):
        return self._active

    @Property(bool, notify=fullscreenChanged)
    def fullscreen(self):
        return self._fullscreen

    @Property(bool, notify=activeNameChanged)
    def hasActiveApp(self):
        return bool(self._active)

    def _changed(self, windows):
        self._windows = list(windows)
        name = win.active_name(windows, self._load_entries().values())
        if name != self._active:
            self._active = name
            self.activeNameChanged.emit()
        full = win.active_fullscreen(windows)
        if full != self._fullscreen:
            self._fullscreen = full
            self.fullscreenChanged.emit()
        self.windowsChanged.emit(windows)
