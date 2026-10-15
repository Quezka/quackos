"""Which popup of the bar or the dock is open, and where. One popup at a time; clicking outside closes it."""
import os
import platform
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot


def read_version(root="/usr/share/quackos/version"):
    try:
        return Path(root).read_text().strip()
    except OSError:
        return ""


def machine_summary():
    """A few lines for 'About QuackOS': hardware and kernel, read from /proc (no external tool)."""
    cpu = ram = ""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal"):
                ram = f"{round(int(line.split()[1]) / 1048576)} GB"
                break
    except (OSError, ValueError, IndexError):
        pass
    return [x for x in (cpu, f"{ram} RAM" if ram else "", f"Linux {platform.release()}") if x]


class ShellState(QObject):
    popupChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup, self._x, self._data = "", 0, -1

    @Property(str, notify=popupChanged)
    def popup(self):
        return self._popup

    @Property(int, notify=popupChanged)
    def popupX(self):
        return self._x

    @Property(int, notify=popupChanged)
    def popupData(self):
        return self._data

    @Slot(str, int, int)
    def toggle(self, name, x, data=-1):
        """Open `name` anchored at screen x; a second click on the same anchor closes it again."""
        if self._popup == name and self._data == data:
            return self.close()
        self._popup, self._x, self._data = name, int(x), int(data)
        self.popupChanged.emit()

    @Slot()
    def close(self):
        if self._popup:
            self._popup, self._data = "", -1
            self.popupChanged.emit()

    @Slot(result="QVariantMap")
    def about(self):
        return {"version": read_version(), "lines": machine_summary(), "host": platform.node()}
