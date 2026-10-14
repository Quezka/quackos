"""A freedesktop .desktop entry: parsing and the command line it stands for. Pure, no Qt, no I/O."""
import re
import shlex
from dataclasses import dataclass

_FIELD_CODES = set("fFuUdDnNvm")


@dataclass(frozen=True)
class DesktopEntry:
    desktop_id: str
    name: str
    icon: str
    exec_line: str
    terminal: bool = False
    hidden: bool = False


def _unescape(value):
    return value.replace("\\s", " ").replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")


def _localized(group, key, locales):
    """Name[it_IT] > Name[it] > Name, like the spec's matching (the locale's own variants first)."""
    for loc in locales:
        for candidate in (loc, loc.split("_")[0]):
            value = group.get(f"{key}[{candidate}]")
            if value:
                return value
    return group.get(key, "")


def parse(text, desktop_id, locales=()):
    """The entry, or None when it is not an Application or has no Exec."""
    group = {}
    in_main = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            in_main = line == "[Desktop Entry]"
            continue
        if in_main and "=" in line:
            key, _, value = line.partition("=")
            group[key.strip()] = value.strip()
    if group.get("Type") != "Application" or not group.get("Exec"):
        return None
    return DesktopEntry(
        desktop_id=desktop_id,
        name=_unescape(_localized(group, "Name", locales)) or desktop_id.removesuffix(".desktop"),
        icon=group.get("Icon", ""),
        exec_line=group["Exec"],
        terminal=group.get("Terminal", "false").lower() == "true",
        hidden=group.get("Hidden", "false").lower() == "true",
    )


def argv(entry):
    """The program and arguments to start the app with no files: field codes dropped, %i/%c expanded, %% kept."""
    out = []
    for token in shlex.split(entry.exec_line):
        if re.fullmatch(r"%[a-zA-Z%]", token):
            code = token[1]
            if code in _FIELD_CODES or code == "k":
                continue
            if code == "i" and entry.icon:
                out += ["--icon", entry.icon]
            elif code == "c":
                out.append(entry.name)
            elif code == "%":
                out.append("%")
            continue
        out.append(re.sub(r"%([a-zA-Z%])", lambda m: "%" if m.group(1) == "%" else "", token))
    return out
