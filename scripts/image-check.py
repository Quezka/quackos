#!/usr/bin/env python3
"""Checks the CONTENTS of a built QuackOS ISO without booting it (about a minute, no QEMU).

    image-check.py <iso>             extracts the filesystem and checks it
    image-check.py --listing FILE    checks a saved `unsquashfs -ll` listing (used by the tests)

Every item below was missing from the image once and broke something real; see docs/design.md "Lezioni".
"""
import re
import subprocess
import sys
import tempfile

# path in the image -> why it must exist
MUST_EXIST = {
    "usr/lib/user-setup/user-setup-apply": "live-config creates the live user with it (missing = 'wrong password')",
    "usr/lib/live/config/0030-user-setup": "live-config user setup",
    "usr/lib/live/config/0085-sddm": "live-config SDDM autologin",
    "usr/lib/live/config/0086-quackos-session": "QuackOS X11 session for the live user",
    "usr/bin/sudo": "live user sudo", "usr/bin/pkexec": "installer launcher",
    "usr/bin/sddm": "display manager", "usr/bin/startplasma-x11": "Plasma X11 session",
    "usr/bin/startplasma-wayland": "Plasma Wayland session", "usr/bin/kwin_x11": "X11 window manager",
    "usr/bin/kwin_wayland": "Wayland window manager",
    "usr/share/xsessions/plasmax11.desktop": "the session SDDM autologs into",
    "usr/lib/xorg/Xorg": "X server",
    "usr/bin/calamares": "installer", "usr/bin/calamares-install-debian": "installer launcher",
    "usr/bin/unsquashfs": "Calamares unpacks the live filesystem with it", "usr/bin/xhost": "installer launcher",
    "usr/bin/rsync": "installer", "usr/bin/ntfs-3g": "NTFS support",
    "usr/share/applications/calamares-install-debian.desktop": "the 'Install QuackOS' icon",
    "usr/share/calamares/branding/quackos/branding.desc": "installer branding",
    "usr/share/wallpapers/Next/metadata.json": "QuackOS wallpaper package",
    "usr/share/wallpapers/Next/contents/images/3840x2160.png": "wallpaper images (else the desktop is black)",
    "usr/share/wallpapers/Next/contents/images/1920x1080.png": "wallpaper images",
    "usr/share/plymouth/themes/quackos/logo.png": "boot splash",
    "usr/lib/x86_64-linux-gnu/dri/swrast_dri.so": "Mesa software renderer (KWin cannot draw without Mesa)",
    "usr/lib/firmware/i915/skl_dmc_ver1_27.bin": "Intel Skylake graphics firmware",
    "usr/local/bin/quack": "the quack command",
    "usr/local/share/plasma/layout-templates/org.kde.plasma.desktop.defaultPanel/contents/layout.js": "panel with the suite",
    "etc/udisks2/mount_options.conf": "safe NTFS mounting",
    "opt/stagno/Stagno": "Stagno", "usr/share/applications/io.github.quezka.Stagno.desktop": "Stagno launcher",
    "usr/share/applications/io.github.quezka.Quire.desktop": "Quire launcher",
    "usr/share/applications/io.github.quezka.Ligature.desktop": "Ligature launcher",
    "usr/share/applications/io.github.quezka.Gantry.desktop": "Gantry launcher",
    "usr/share/applications/io.github.quezka.Bivouac.desktop": "Bivouac launcher",
    "usr/share/applications/io.github.quezka.Natter.desktop": "Natter launcher",
    "usr/bin/firefox-esr": "the regular web browser",
    # the QuackOS desktop session (labwc + our own shell), docs/de-design.md
    "usr/bin/labwc": "the compositor of the QuackOS session",
    "usr/share/wayland-sessions/quackos.desktop": "the QuackOS session SDDM can start",
    "usr/local/bin/quackos-session": "the session script", "usr/local/bin/quackos-shell": "the shell launcher",
    "usr/lib/quackos/shell/quackshell/__main__.py": "the shell code",
    "usr/lib/quackos/shell/quackshell/presentation/qml/main_layer.qml": "the shell's QML",
    "usr/share/quackos/labwc/rc.xml": "compositor configuration",
    "usr/share/quackos/labwc/autostart": "what the session starts",
    "usr/share/themes/QuackOS/labwc/themerc": "window theme",
    "usr/share/themes/QuackOS/labwc/close-active.svg": "traffic-light buttons",
    "usr/bin/swaybg": "wallpaper", "usr/bin/mako": "notifications", "usr/bin/fuzzel": "launcher",
    "usr/bin/foot": "terminal", "usr/bin/swaylock": "lock screen",
    "usr/lib/python3/dist-packages/PySide6/QtQuick.abi3.so": "PySide6 Qt Quick (the shell)",
    "usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/layershell/qmldir": "layer-shell QML module (bar and dock)",
    "usr/lib/x86_64-linux-gnu/qt6/qml/QtQuick/Window/qmldir": "QtQuick.Window QML module",
    "usr/lib/x86_64-linux-gnu/libLayerShellQtInterface.so.6": "layer-shell for Qt",
    "usr/lib/x86_64-linux-gnu/libexec/polkit-kde-authentication-agent-1": "polkit prompt used by the session",
}
# paths that must NOT be there
MUST_NOT_EXIST = {
    "usr/share/wallpapers/Altai/metadata.json": "a stock wallpaper package with Id Next must not sneak in",
    "usr/lib/live/config/0900-quackos-installer-icon": "the old broken installer launcher",
    "etc/systemd/system/quackos-debug.service": "the removed debug service",
}


def normalise(path):
    path = path.strip().lstrip("./")
    return path.replace("squashfs-root/", "", 1) if path.startswith("squashfs-root/") else path


def paths_from_listing(text):
    """`unsquashfs -ll` lines: 'drwxr-xr-x root/root 0 2026-10-13 10:00 squashfs-root/usr' (symlinks: 'name -> target')."""
    found = set()
    for line in text.splitlines():
        m = re.match(r"^\S+\s+\S+\s+\d+\s+\d{4}-\d\d-\d\d \d\d:\d\d (.+)$", line)
        if m:
            found.add(normalise(m.group(1).split(" -> ")[0]))
    return found


def check(paths, version):
    """Returns a list of failures. `paths` is the set of file paths in the image."""
    failures = ["missing %s: %s" % (p, why) for p, why in MUST_EXIST.items() if p not in paths]
    failures += ["unexpected %s: %s" % (p, why) for p, why in MUST_NOT_EXIST.items() if p in paths]
    return failures


def listing_of_iso(iso):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["xorriso", "-osirrox", "on", "-indev", iso, "-extract", "/live/filesystem.squashfs",
                        tmp + "/fs.squashfs"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        listing = subprocess.run(["unsquashfs", "-ll", tmp + "/fs.squashfs"], check=True, capture_output=True, text=True).stdout
        os_release = subprocess.run(["unsquashfs", "-cat", tmp + "/fs.squashfs", "usr/lib/os-release"],
                                    capture_output=True, text=True).stdout
    return listing, os_release


def main(argv):
    if len(argv) == 3 and argv[1] == "--listing":
        with open(argv[2], encoding="utf-8") as f:
            listing, os_release = f.read(), ""
    elif len(argv) == 2:
        listing, os_release = listing_of_iso(argv[1])
    else:
        print(__doc__, file=sys.stderr)
        return 2
    failures = check(paths_from_listing(listing), None)
    if os_release:
        if 'ID=quackos' not in os_release or 'ID_LIKE=debian' not in os_release:
            failures.append("usr/lib/os-release does not say ID=quackos / ID_LIKE=debian")
        print(os_release.strip().splitlines()[0] if os_release.strip() else "")
    for f in failures:
        print("FAIL: " + f, file=sys.stderr)
    if failures:
        print("%d problem(s) in the image" % len(failures), file=sys.stderr)
        return 1
    print("OK: the image has everything it must have (%d checks)" % (len(MUST_EXIST) + len(MUST_NOT_EXIST)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
