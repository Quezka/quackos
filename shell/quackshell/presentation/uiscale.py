"""The same small-screen rule as the rest of the suite (see quire/presentation/uiscale.py): screens up to 800 px tall
(the laptop is 1366x768) get the whole interface at 85%, via QT_SCALE_FACTOR. Qt reads it once, at start-up, so this
must run before anything Qt-related exists."""
import gc
import os

AUTO_BELOW = 800
SMALL = 0.85


def factor(screen_height):
    return SMALL if screen_height is not None and screen_height <= AUTO_BELOW else 1.0


def _screen_height():
    """The primary screen's height, asked of a throwaway application (the real one cannot exist yet). None when
    there is no screen to ask (headless, or PySide6 missing): the scale is then left at 1.0."""
    try:
        from PySide6.QtGui import QGuiApplication
    except ImportError:
        return None
    if QGuiApplication.instance() is not None:
        return None
    probe = QGuiApplication([])
    try:
        screen = probe.primaryScreen()
        return screen.size().height() if screen else None
    finally:
        probe.shutdown()
        del probe
        gc.collect()


def apply_before_app(env=None):
    env = os.environ if env is None else env
    if "QT_SCALE_FACTOR" in env:
        return
    value = factor(_screen_height())
    if value != 1.0:
        env["QT_SCALE_FACTOR"] = f"{value:g}"
