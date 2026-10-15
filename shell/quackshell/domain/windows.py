"""Open windows as the compositor reports them, and which app each belongs to. Pure, no Qt, no Wayland."""
import os
import shlex
from dataclasses import dataclass

from .desktop_entry import DesktopEntry

MAXIMIZED, MINIMIZED, ACTIVATED, FULLSCREEN = 0, 1, 2, 3  # values of zwlr_foreign_toplevel_handle_v1.state


@dataclass(frozen=True)
class Window:
    id: int
    title: str = ""
    app_id: str = ""
    activated: bool = False
    minimized: bool = False
    fullscreen: bool = False


def _keys(entry):
    """Names an app_id may use for this entry: the id without .desktop, its last segment, StartupWMClass, the command."""
    stem = entry.desktop_id.removesuffix(".desktop")
    keys = {stem.lower(), stem.rsplit(".", 1)[-1].lower()}
    if entry.wm_class:
        keys.add(entry.wm_class.lower())
    try:
        first = shlex.split(entry.exec_line)[0]
        keys.add(os.path.basename(first).lower())
    except (ValueError, IndexError):
        pass
    return keys


def entry_for(app_id, entries):
    """The DesktopEntry a window's app_id stands for, or None. An exact match on the whole id beats the loose ones."""
    if not app_id:
        return None
    wanted = app_id.lower()
    loose = None
    for entry in entries:
        stem = entry.desktop_id.removesuffix(".desktop").lower()
        if wanted == stem:
            return entry
        if loose is None and wanted in _keys(entry):
            loose = entry
    return loose


def group(windows, entries):
    """({desktop_id: [Window]}, [Window with no known entry]) with `windows` in the order given."""
    entries = list(entries)
    known, unknown = {}, []
    for w in windows:
        entry = entry_for(w.app_id, entries)
        if entry is None:
            unknown.append(w)
        else:
            known.setdefault(entry.desktop_id, []).append(w)
    return known, unknown


def active_name(windows, entries):
    """What the bar shows next to the logo: the focused app's name, else its title or app_id, else ''."""
    for w in windows:
        if w.activated and not w.minimized:
            entry = entry_for(w.app_id, entries)
            return entry.name if entry else (w.app_id or w.title)
    return ""


def next_to_raise(windows):
    """The window a dock click should bring forward: the first minimized one, else the one after the focused one."""
    if not windows:
        return None
    for w in windows:
        if w.minimized:
            return w
    for i, w in enumerate(windows):
        if w.activated:
            return windows[(i + 1) % len(windows)]
    return windows[0]


def apply_state(window, states):
    """`window` with the flags of a protocol `state` array (values 0=maximized 1=minimized 2=activated 3=fullscreen)."""
    return Window(window.id, window.title, window.app_id, ACTIVATED in states, MINIMIZED in states, FULLSCREEN in states)


def active_fullscreen(windows):
    """True while the focused window is full screen: the dock and the bar stay out of the way (macOS does the same)."""
    return any(w.activated and w.fullscreen and not w.minimized for w in windows)


def active_window(windows):
    """The focused window that is on screen, or None."""
    return next((w for w in windows if w.activated and not w.minimized), None)


def windows_of(app_windows_source, windows, entries):
    """The windows that belong to the same app as `app_windows_source` (a Window): for 'hide' and 'quit' of an app."""
    entries = list(entries)
    target = entry_for(app_windows_source.app_id, entries)
    out = []
    for w in windows:
        if w.app_id == app_windows_source.app_id or (target is not None and entry_for(w.app_id, entries) is target):
            out.append(w)
    return out
