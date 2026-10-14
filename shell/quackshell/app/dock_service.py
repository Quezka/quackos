"""Use cases of the dock: which apps it shows and how an item is opened."""
from ..domain import dock


class DockService:
    def __init__(self, load_entries, load_pins, launch):
        self._load_entries = load_entries
        self._load_pins = load_pins
        self._launch = launch

    def items(self):
        pins = self._load_pins() or dock.DEFAULT_PINS
        return dock.resolve(pins, self._load_entries())

    def open(self, entry):
        self._launch(entry)
