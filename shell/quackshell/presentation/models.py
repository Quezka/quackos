"""Qt side of the dock: a list model over the DockService and an icon provider backed by the icon theme."""
from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, QSize, Qt, Slot
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtQuick import QQuickImageProvider


class DockModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    IconRole = Qt.UserRole + 2

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self._service = service
        self._items = service.items()

    def roleNames(self):
        return {self.NameRole: b"name", self.IconRole: b"icon"}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        entry = self._items[index.row()]
        if role in (self.NameRole, Qt.DisplayRole):
            return entry.name
        if role == self.IconRole:
            return entry.icon
        return None

    @Slot(int)
    def open(self, row):
        if 0 <= row < len(self._items):
            self._service.open(self._items[row])

    @Slot()
    def reload(self):
        self.beginResetModel()
        self._items = self._service.items()
        self.endResetModel()


class ThemeIcons(QQuickImageProvider):
    """image://theme/<name or absolute path>: what QML's Image needs to show an icon of the current theme."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Pixmap)

    def requestPixmap(self, icon_id, size, requested):
        side = max(requested.width(), requested.height(), 64)
        icon = QIcon(icon_id) if icon_id.startswith("/") else QIcon.fromTheme(icon_id)
        if icon.isNull():
            icon = QIcon.fromTheme("application-x-executable")
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
