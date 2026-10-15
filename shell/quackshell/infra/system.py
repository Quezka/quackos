"""The machine the bar talks to: sound (wpctl), screen brightness (brightnessctl), battery (sysfs), Wi-Fi (nmcli), power
(systemctl, labwc, swaylock). Every call has a timeout and never raises: a missing tool just reads as 'not available'."""
import subprocess
from pathlib import Path

from ..domain import status


def run(argv, timeout=4):
    """(exit code, stdout); (-1, '') when the program is missing or too slow."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return p.returncode, p.stdout
    except (OSError, subprocess.SubprocessError):
        return -1, ""


class Audio:
    SINK = "@DEFAULT_AUDIO_SINK@"

    def __init__(self, runner=run):
        self._run = runner

    def read(self):
        code, out = self._run(["wpctl", "get-volume", self.SINK])
        return status.parse_wpctl_volume(out) if code == 0 else (None, False)

    def set_volume(self, percent):
        self._run(["wpctl", "set-volume", "-l", "1.0", self.SINK, f"{max(0, min(100, int(percent)))}%"])

    def set_muted(self, muted):
        self._run(["wpctl", "set-mute", self.SINK, "1" if muted else "0"])


class Brightness:
    def __init__(self, runner=run):
        self._run = runner

    def read(self):
        code, out = self._run(["brightnessctl", "-m"])
        return status.parse_brightnessctl(out) if code == 0 else None

    def set(self, percent):
        self._run(["brightnessctl", "set", f"{max(1, min(100, int(percent)))}%"])


class Battery:
    def __init__(self, root="/sys/class/power_supply"):
        self._root = Path(root)

    def read(self):
        for bat in sorted(self._root.glob("BAT*")):
            try:
                return status.parse_battery((bat / "capacity").read_text(), (bat / "status").read_text())
            except OSError:
                continue
        return None, False


class Network:
    def __init__(self, runner=run):
        self._run = runner

    def enabled(self):
        code, out = self._run(["nmcli", "-t", "-f", "WIFI", "general"])
        return code == 0 and status.parse_wifi_enabled(out)

    def available(self):
        """True when NetworkManager knows a Wi-Fi adapter."""
        code, out = self._run(["nmcli", "-t", "-f", "TYPE", "device"])
        return code == 0 and "wifi" in out.split()

    def networks(self):
        code, out = self._run(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL,SECURITY", "dev", "wifi", "list", "--rescan", "no"], 8)
        if code != 0:
            return []
        _, known_out = self._run(["nmcli", "-t", "-f", "NAME", "connection", "show"])
        known = [status.split_nmcli(line)[0] for line in known_out.splitlines()]
        return status.parse_wifi_list(out, known)

    def rescan(self):
        self._run(["nmcli", "dev", "wifi", "rescan"], 10)

    def set_enabled(self, on):
        self._run(["nmcli", "radio", "wifi", "on" if on else "off"])

    def connect(self, ssid, password=""):
        argv = ["nmcli", "dev", "wifi", "connect", ssid] + (["password", password] if password else [])
        code, out = self._run(argv, 30)
        return code == 0


class Power:
    """Detached on purpose: the session is going away (or the lock screen is staying) and we must not wait for it."""

    def __init__(self, spawn=None):
        self._spawn = spawn or self._detached

    @staticmethod
    def _detached(argv):
        subprocess.Popen(argv, start_new_session=True, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def lock(self):
        self._spawn(["swaylock", "-f", "-c", "111214"])

    def logout(self):
        self._spawn(["labwc", "--exit"])

    def reboot(self):
        self._spawn(["systemctl", "reboot"])

    def poweroff(self):
        self._spawn(["systemctl", "poweroff"])
