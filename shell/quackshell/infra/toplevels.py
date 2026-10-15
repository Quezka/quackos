"""The compositor's list of windows, over the wlr-foreign-toplevel-management protocol (labwc speaks it).

`Tracker` keeps the state from protocol events and is pure; `ToplevelClient` wires it to a Wayland connection. The
client has no Qt: the shell watches `fileno()` with a QSocketNotifier and calls `process()` when it is readable."""
import array

from ..domain import windows as w


class Tracker:
    """Pending and published windows. Events change a pending copy; `done` publishes it, as the protocol says."""

    def __init__(self, on_change):
        self._pending, self._published, self._order = {}, {}, []
        self._on_change = on_change

    def opened(self, wid):
        self._pending[wid] = w.Window(wid)

    def title(self, wid, text):
        self._edit(wid, title=text)

    def app_id(self, wid, text):
        self._edit(wid, app_id=text)

    def state(self, wid, raw):
        if isinstance(raw, (bytes, bytearray, memoryview)):
            values = set(array.array("I", bytes(raw)))
        else:
            values = set(raw)
        if wid in self._pending:
            self._pending[wid] = w.apply_state(self._pending[wid], values)

    def done(self, wid):
        if wid not in self._pending:
            return
        if wid not in self._published:
            self._order.append(wid)
        self._published[wid] = self._pending[wid]
        self._emit()

    def closed(self, wid):
        self._pending.pop(wid, None)
        if self._published.pop(wid, None) is not None:
            self._order.remove(wid)
            self._emit()

    def snapshot(self):
        return [self._published[i] for i in self._order]

    def _edit(self, wid, **changes):
        cur = self._pending.get(wid)
        if cur is not None:
            self._pending[wid] = w.Window(**{**cur.__dict__, **changes})

    def _emit(self):
        self._on_change(self.snapshot())


class ToplevelClient:
    """A Wayland connection that follows the windows; `activate`/`close`/`minimize` ask the compositor."""

    def __init__(self, on_change):
        from pywayland.client import Display
        from pywayland.protocol.wayland import WlSeat

        from .protocols.wlr_foreign_toplevel_management_unstable_v1 import ZwlrForeignToplevelManagerV1

        self._WlSeat, self._Manager = WlSeat, ZwlrForeignToplevelManagerV1
        self._tracker = Tracker(on_change)
        self._handles, self._next_id = {}, 0
        self._seat = self._manager = None
        self._display = Display()
        self._display.connect()
        # KEEP the registry referenced: pywayland finds the display for every new object (each new window) through the
        # live WlRegistry proxies, so a registry that gets garbage collected makes every later window fail with
        # "Cannot find display" (found in QEMU: the dock only knew the windows open when the shell started).
        self._registry = self._display.get_registry()
        self._registry.dispatcher["global"] = self._on_global
        self._display.roundtrip()   # globals
        self._display.roundtrip()   # the first toplevels
        if self._manager is None:
            raise RuntimeError("the compositor has no wlr-foreign-toplevel-management")

    def fileno(self):
        return self._display.get_fd()

    def close_window(self, wid):
        if wid in self._handles:
            self._handles[wid].close()
            self._display.flush()

    def shutdown(self):
        """Release the protocol objects BEFORE the connection: destroying them the other way round (what the garbage
        collector does at exit) crashes libwayland."""
        for handle in list(self._handles.values()):
            try:
                handle.destroy()
            except Exception:
                pass
        self._handles.clear()
        try:
            if self._manager is not None:
                self._manager.stop()
                self._display.flush()
        except Exception:
            pass
        self._manager = self._seat = self._registry = None
        try:
            self._display.disconnect()
        except Exception:
            pass

    def process(self):
        self._display.read()
        self._display.dispatch()
        self._display.flush()

    def activate(self, wid):
        if self._seat is not None and wid in self._handles:
            self._handles[wid].activate(self._seat)
            self._display.flush()

    def minimize(self, wid):
        if wid in self._handles:
            self._handles[wid].set_minimized()
            self._display.flush()

    def leave_fullscreen(self, wid):
        if wid in self._handles:
            self._handles[wid].unset_fullscreen()
            self._display.flush()

    # --- protocol wiring ---
    def _on_global(self, registry, name, interface, version):
        if interface == "zwlr_foreign_toplevel_manager_v1":
            self._manager = registry.bind(name, self._Manager, min(version, 3))
            self._manager.dispatcher["toplevel"] = self._on_toplevel
        elif interface == "wl_seat" and self._seat is None:
            self._seat = registry.bind(name, self._WlSeat, min(version, 5))

    def _on_toplevel(self, manager, handle):
        self._next_id += 1
        wid = self._next_id
        self._handles[wid] = handle
        self._tracker.opened(wid)
        handle.dispatcher["title"] = lambda h, text: self._tracker.title(wid, text)
        handle.dispatcher["app_id"] = lambda h, text: self._tracker.app_id(wid, text)
        handle.dispatcher["state"] = lambda h, raw: self._tracker.state(wid, raw)
        handle.dispatcher["done"] = lambda h: self._tracker.done(wid)
        handle.dispatcher["closed"] = lambda h: self._on_closed(wid, h)

    def _on_closed(self, wid, handle):
        self._tracker.closed(wid)
        self._handles.pop(wid, None)
        handle.destroy()
