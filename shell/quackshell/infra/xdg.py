"""Finds and reads the .desktop files of the installed apps (XDG_DATA_HOME, then XDG_DATA_DIRS)."""
import json
import os
from pathlib import Path

from ..domain import desktop_entry


def _data_dirs(env):
    home = Path(env.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    others = (env.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":")
    return [home] + [Path(p) for p in others if p]


def locales(env=None):
    env = os.environ if env is None else env
    raw = env.get("LC_ALL") or env.get("LC_MESSAGES") or env.get("LANG") or ""
    return [raw.split(".")[0].split("@")[0]] if raw and raw not in ("C", "POSIX") else []


def installed_entries(env=None):
    """{desktop_id: DesktopEntry}; an earlier directory wins over a later one, like the spec says."""
    env = os.environ if env is None else env
    found = {}
    for base in _data_dirs(env):
        apps = base / "applications"
        if not apps.is_dir():
            continue
        for path in sorted(apps.rglob("*.desktop")):
            desktop_id = "-".join(path.relative_to(apps).parts)
            if desktop_id in found:
                continue
            try:
                entry = desktop_entry.parse(path.read_text(errors="replace"), desktop_id, locales(env))
            except (OSError, ValueError):
                continue
            if entry is not None:
                found[desktop_id] = entry
    return found


def user_pins(env=None):
    """The user's own dock list (~/.config/quackos/dock.json, a JSON list of desktop ids), or None."""
    env = os.environ if env is None else env
    conf = Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "quackos" / "dock.json"
    try:
        data = json.loads(conf.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, list) and all(isinstance(x, str) for x in data) else None
