"""Qt side of the dock: a list model over the DockService and an icon provider backed by our icons and the icon theme."""
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, QSize, Qt, Slot
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtQuick import QQuickImageProvider


class DockModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    IconRole = Qt.UserRole + 2
    RunningRole = Qt.UserRole + 3
    PinnedRole = Qt.UserRole + 4

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self._service = service
        self._windows = []
        self._items = service.items()

    def roleNames(self):
        return {self.NameRole: b"name", self.IconRole: b"icon", self.RunningRole: b"running", self.PinnedRole: b"pinned"}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        if role in (self.NameRole, Qt.DisplayRole):
            return item.entry.name
        if role == self.IconRole:
            return item.icon
        if role == self.RunningRole:
            return item.running
        if role == self.PinnedRole:
            return item.pinned
        return None

    @Slot(int)
    def open(self, row):
        if 0 <= row < len(self._items):
            self._service.open(self._items[row])

    @Slot(int)
    def newWindow(self, row):
        if 0 <= row < len(self._items):
            self._service.new_window(self._items[row])

    @Slot(int)
    def togglePin(self, row):
        if 0 <= row < len(self._items) and self._service.toggle_pin(self._items[row]):
            self.reload()

    @Slot(int)
    def quit(self, row):
        if 0 <= row < len(self._items):
            self._service.quit(self._items[row])

    @Slot(int)
    def hide(self, row):
        if 0 <= row < len(self._items):
            self._service.hide(self._items[row])

    @Slot(int, result="QVariantMap")
    def info(self, row):
        """What the dock's right-click menu needs to know about one item."""
        if not 0 <= row < len(self._items):
            return {}
        item = self._items[row]
        return {"name": item.entry.name, "running": item.running, "pinned": item.pinned, "icon": item.icon,
                "canPin": not item.entry.desktop_id.startswith("window:")}

    def setWindows(self, windows):
        self._windows = list(windows)
        self.reload()

    @Slot()
    def reload(self):
        self.beginResetModel()
        self._items = self._service.items(self._windows)
        self.endResetModel()


class ThemeIcons(QQuickImageProvider):
    """image://theme/<name or absolute path>: what QML's Image needs to show an icon of the current theme."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Pixmap)

    OWN = Path(__file__).parent / "icons"

    def requestPixmap(self, icon_id, size, requested):
        side = max(requested.width(), requested.height(), 64)
        if icon_id.startswith("own:"):
            icon = QIcon(str(self.OWN / (icon_id[4:] + ".svg")))
        elif icon_id.startswith("/"):
            icon = QIcon(icon_id)
        else:
            icon = QIcon.fromTheme(icon_id)
        if icon.isNull() and not icon_id.startswith("own:"):
            icon = QIcon(str(self.OWN / "app.svg"))
        pixmap = icon.pixmap(QSize(side, side))
        if pixmap.isNull():
            pixmap = QPixmap.fromImage(QImage(side, side, QImage.Format_ARGB32))
            pixmap.fill(Qt.transparent)
        size.setWidth(pixmap.width())
        size.setHeight(pixmap.height())
        return pixmap


class Launcher(QObject):
    """Things the bar can start: the app launcher (fuzzel for now)."""

    def __init__(self, run, parent=None):
        super().__init__(parent)
        self._run = run

    @Slot()
    def openLauncher(self):
        self._run(["fuzzel"])

