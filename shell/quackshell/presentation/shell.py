"""Starts the shell: a top bar and a floating dock as layer-shell windows (plain windows when there is no layer-shell,
so the shell can be tried from inside any other desktop)."""
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine

from ..app.dock_service import DockService
from ..app.system_service import SystemService
from ..infra import process, system as sysinfra, xdg
from .models import DockModel, Launcher, ThemeIcons
from .state import ShellState
from .system import SystemModel
from .uiscale import apply_before_app
from .windows import WindowWatcher

QML = Path(__file__).parent / "qml"


def qml_import_paths(env=os.environ):
    extra = [p for key in ("QML_IMPORT_PATH", "QML2_IMPORT_PATH") for p in env.get(key, "").split(":") if p]
    return extra + [QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)]


def layer_shell_available(env=os.environ, paths=None):
    """layer-shell needs a Wayland session and the org.kde.layershell QML module."""
    if not env.get("WAYLAND_DISPLAY") or env.get("QUACKSHELL_PLAIN"):
        return False
    return any((Path(p) / "org/kde/layershell/qmldir").is_file() for p in (paths or qml_import_paths(env)))


def setup_icons(env=os.environ):
    """Qt has no platform theme here, so say where the icons are: every XDG data dir, theme breeze (phase 1 still
    ships it with Plasma) and hicolor behind it, where the suite's own icons live."""
    dirs = [Path(env.get("XDG_DATA_HOME") or Path.home() / ".local/share")]
    dirs += [Path(p) for p in (env.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if p]
    QIcon.setThemeSearchPaths([str(d / "icons") for d in dirs])
    QIcon.setThemeName(env.get("QUACKSHELL_ICON_THEME", "breeze"))
    QIcon.setFallbackThemeName("hicolor")


def _detached(argv):
    subprocess.Popen(argv, start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(argv=None):
    apply_before_app()  # must run before any Qt object exists
    layer = layer_shell_available()
    if layer:
        os.environ["QT_WAYLAND_SHELL_INTEGRATION"] = "layer-shell"  # must be set before the app exists
    app = QGuiApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("quackos-shell")
    app.setDesktopFileName("quackos-shell")
    app.setQuitOnLastWindowClosed(False)
    setup_icons()

    watcher = WindowWatcher(xdg.installed_entries)
    service = DockService(xdg.installed_entries, xdg.user_pins, process.launch, watcher.activate,
                          save_pins=xdg.save_pins, close_window=watcher.close_window, minimize_window=watcher.minimize_window)
    state = ShellState()
    system = SystemModel(SystemService(sysinfra.Audio(), sysinfra.Brightness(), sysinfra.Battery(),
                                       sysinfra.Network(), sysinfra.Power()))
    engine = QQmlApplicationEngine()
    engine.addImageProvider("theme", ThemeIcons())
    model = DockModel(service)
    launcher = Launcher(_detached)
    ctx = engine.rootContext()
    ctx.setContextProperty("dockModel", model)
    ctx.setContextProperty("launcher", launcher)
    ctx.setContextProperty("windowWatcher", watcher)
    ctx.setContextProperty("shellState", state)
    ctx.setContextProperty("systemModel", system)
    watcher.windowsChanged.connect(model.setWindows)
    if layer:  # a plain run inside another desktop has no labwc to ask
        watcher.start()
        app.aboutToQuit.connect(watcher.stop)
    engine.load(QUrl.fromLocalFile(str(QML / ("main_layer.qml" if layer else "main_plain.qml"))))
    if not engine.rootObjects():
        print("quackos-shell: the QML did not load", file=sys.stderr)
        return 1
    system.start()
    return app.exec()
