"""Reading the output of the system tools the bar uses (wpctl, brightnessctl, nmcli, sysfs). Pure: text in, values out."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class WifiNetwork:
    ssid: str
    signal: int
    secured: bool
    active: bool = False
    known: bool = False


def parse_wpctl_volume(text):
    """`wpctl get-volume @DEFAULT_AUDIO_SINK@` -> (percent, muted); (None, False) when there is no sound server."""
    m = re.search(r"Volume:\s*([0-9]*\.?[0-9]+)", text or "")
    if not m:
        return None, False
    return max(0, min(150, round(float(m.group(1)) * 100))), "[MUTED]" in text


def parse_brightnessctl(text):
    """`brightnessctl -m` -> percent of the first backlight device, or None (a desktop has none)."""
    for line in (text or "").splitlines():
        parts = line.split(",")
        if len(parts) >= 5 and parts[1] == "backlight":
            m = re.match(r"(\d+)%", parts[3])
            if m:
                return int(m.group(1))
    return None


def parse_battery(capacity, status):
    """sysfs `capacity` and `status` -> (percent, charging); (None, False) when there is no battery."""
    try:
        percent = max(0, min(100, int(str(capacity).strip())))
    except (TypeError, ValueError):
        return None, False
    return percent, str(status).strip() in ("Charging", "Full")


def split_nmcli(line):
    """nmcli -t escapes ':' and '\\' inside a field with a backslash."""
    out, cur, i = [], "", 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line):
            cur += line[i + 1]
            i += 2
        elif c == ":":
            out.append(cur)
            cur, i = "", i + 1
        else:
            cur += c
            i += 1
    out.append(cur)
    return out


def parse_wifi_list(text, known=()):
    """`nmcli -t -f ACTIVE,SSID,SIGNAL,SECURITY dev wifi list`: strongest entry per name, the active one first, then by
    signal; hidden networks (empty name) are dropped."""
    best = {}
    for line in (text or "").splitlines():
        f = split_nmcli(line)
        if len(f) < 4 or not f[1]:
            continue
        try:
            signal = int(f[2])
        except ValueError:
            continue
        net = WifiNetwork(f[1], signal, f[3] not in ("", "--"), f[0] == "yes", f[1] in known)
        old = best.get(net.ssid)
        if old is None or net.active or (not old.active and net.signal > old.signal):
            best[net.ssid] = net
    return sorted(best.values(), key=lambda n: (not n.active, -n.signal, n.ssid.lower()))


def parse_wifi_enabled(text):
    return (text or "").strip().lower() == "enabled"


def wifi_bars(signal):
    """0..4 bars for the icon."""
    return 0 if signal <= 0 else 1 if signal < 25 else 2 if signal < 50 else 3 if signal < 75 else 4
