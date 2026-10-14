"""What the dock shows. The pinned apps are desktop ids; the ones that are not installed are skipped."""

# Order of the macOS-like layout of the 0.1.x panel: the suite first, then the system tools.
DEFAULT_PINS = (
    "io.github.quezka.Stagno.desktop",
    "io.github.quezka.Quire.desktop",
    "io.github.quezka.Ligature.desktop",
    "io.github.quezka.Gantry.desktop",
    "io.github.quezka.Bivouac.desktop",
    "io.github.quezka.Natter.desktop",
    "org.kde.dolphin.desktop",
    "org.kde.konsole.desktop",
    "systemsettings.desktop",
)


def resolve(pins, entries):
    """The entries for `pins`, in order, skipping ids that are unknown, hidden or repeated."""
    seen = set()
    out = []
    for desktop_id in pins:
        entry = entries.get(desktop_id)
        if entry is None or entry.hidden or desktop_id in seen:
            continue
        seen.add(desktop_id)
        out.append(entry)
    return out


def magnification(distance, base=1.0, peak=1.55, spread=70.0):
    """Scale of an icon whose centre is `distance` px from the pointer (a bell curve, 1.0 far away)."""
    if distance is None:
        return base
    return base + (peak - base) * 2.718281828 ** (-((distance / spread) ** 2))
