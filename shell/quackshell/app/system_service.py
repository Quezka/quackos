"""Use cases of the bar's status items: read everything in one go, change one thing."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SystemStatus:
    volume: int = -1            # -1: no sound server
    muted: bool = False
    brightness: int = -1        # -1: no backlight (desktop)
    battery: int = -1           # -1: no battery
    charging: bool = False
    wifi_available: bool = False
    wifi_enabled: bool = False
    networks: tuple = field(default_factory=tuple)


class SystemService:
    def __init__(self, audio, brightness, battery, network, power):
        self.audio, self.brightness, self.battery, self.network, self.power = audio, brightness, battery, network, power

    def snapshot(self):
        volume, muted = self.audio.read()
        level = self.brightness.read()
        percent, charging = self.battery.read()
        available = self.network.available()
        enabled = self.network.enabled() if available else False
        networks = tuple(self.network.networks()) if enabled else ()
        return SystemStatus(-1 if volume is None else volume, muted, -1 if level is None else level,
                            -1 if percent is None else percent, charging, available, enabled, networks)
