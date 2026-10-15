"""Use cases of the dock: which items it shows (pinned apps, then other running apps) and what a click does."""
from dataclasses import dataclass

from ..domain import dock, windows as win
from ..domain.desktop_entry import DesktopEntry


@dataclass(frozen=True)
class DockItem:
    entry: DesktopEntry
    windows: tuple = ()
    pinned: bool = True

    @property
    def running(self):
        return len(self.windows)

    @property
    def icon(self):
        """`own:<name>` for the icons we draw ourselves, else the icon name of the .desktop file."""
        own = dock.own_icon(self.entry.desktop_id)
        return f"own:{own}" if own else (self.entry.icon or "own:app")


class DockService:
    def __init__(self, load_entries, load_pins, launch, activate=lambda window_id: None,
                 save_pins=lambda pins: True, close_window=lambda window_id: None, minimize_window=lambda window_id: None):
        self._load_entries = load_entries
        self._load_pins = load_pins
        self._launch = launch
        self._activate = activate
        self._save_pins = save_pins
        self._close = close_window
        self._minimize = minimize_window

    def _pins(self):
        """The user's list when there is one (even an empty one: they may have unpinned everything), else the defaults."""
        pins = self._load_pins()
        return list(dock.DEFAULT_PINS) if pins is None else list(pins)

    def items(self, windows=()):
        entries = self._load_entries()
        pinned = dock.resolve(self._pins(), entries)
        known, unknown = win.group(windows, entries.values())
        out = [DockItem(e, tuple(known.get(e.desktop_id, ())), True) for e in pinned]
        pinned_ids = {e.desktop_id for e in pinned}
        out += [DockItem(entries[i], tuple(ws), False) for i, ws in known.items() if i not in pinned_ids]
        by_app = {}
        for w in unknown:  # windows of apps we have no .desktop file for: one item per app_id
            by_app.setdefault(w.app_id or w.title, []).append(w)
        for key, ws in by_app.items():
            out.append(DockItem(DesktopEntry(f"window:{key}", key or "?", ws[0].app_id, ""), tuple(ws), False))
        return out

    def open(self, item):
        """A click: bring a running app forward (a minimized window first, else the next one), or start it."""
        target = win.next_to_raise(list(item.windows))
        if target is not None:
            self._activate(target.id)
        else:
            self._launch(item.entry)

    def new_window(self, item):
        """'Open' in the menu of a running app: a second instance (most apps just raise themselves)."""
        self._launch(item.entry)

    def toggle_pin(self, item):
        """Keep the app in the dock (or not); only apps with a real .desktop file can be pinned."""
        if item.entry.desktop_id.startswith("window:"):
            return False
        pins = self._pins()
        if item.entry.desktop_id in pins:
            pins.remove(item.entry.desktop_id)
        else:
            pins.append(item.entry.desktop_id)
        return self._save_pins(pins)

    def quit(self, item):
        for w in item.windows:
            self._close(w.id)

    def hide(self, item):
        for w in item.windows:
            self._minimize(w.id)
