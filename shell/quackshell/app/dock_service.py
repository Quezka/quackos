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


class DockService:
    def __init__(self, load_entries, load_pins, launch, activate=lambda window_id: None):
        self._load_entries = load_entries
        self._load_pins = load_pins
        self._launch = launch
        self._activate = activate

    def items(self, windows=()):
        entries = self._load_entries()
        pinned = dock.resolve(self._load_pins() or dock.DEFAULT_PINS, entries)
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
