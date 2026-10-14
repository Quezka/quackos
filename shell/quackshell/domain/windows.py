"""Open windows as the compositor reports them, and which app each belongs to. Pure, no Qt, no Wayland."""
import os
import shlex
from dataclasses import dataclass

from .desktop_entry import DesktopEntry

ACTIVATED, MINIMIZED = 2, 1  # values of zwlr_foreign_toplevel_handle_v1.state


@dataclass(frozen=True)
class Window:
    id: int
    title: str = ""
    app_id: str = ""
    activated: bool = False
    minimized: bool = False


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
    return Window(window.id, window.title, window.app_id, ACTIVATED in states, MINIMIZED in states)
