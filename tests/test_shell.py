"""Tests of the desktop shell (shell/quackshell): the pure layers run anywhere; the Qt smoke test only where PySide6 is."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shell"))

from quackshell.app.dock_service import DockService  # noqa: E402
from quackshell.domain import desktop_entry, dock  # noqa: E402
from quackshell.infra import xdg  # noqa: E402

QUIRE = """# comment
[Desktop Entry]
Type=Application
Name=Quire
Name[it]=Quire (it)
Name[ru_RU]=Квайр
Exec=/opt/quire/Quire %U
Icon=io.github.quezka.Quire
Terminal=false

[Desktop Action new]
Name=Other group
Exec=ignored
"""


class DesktopEntryTest(unittest.TestCase):
    def test_parse_takes_only_the_main_group_and_picks_the_locale(self):
        e = desktop_entry.parse(QUIRE, "q.desktop", ["it_IT"])
        self.assertEqual((e.name, e.icon, e.exec_line), ("Quire (it)", "io.github.quezka.Quire", "/opt/quire/Quire %U"))
        self.assertEqual(desktop_entry.parse(QUIRE, "q.desktop", ["ru_RU"]).name, "Квайр")
        self.assertEqual(desktop_entry.parse(QUIRE, "q.desktop", []).name, "Quire")

    def test_not_an_application_is_ignored(self):
        self.assertIsNone(desktop_entry.parse("[Desktop Entry]\nType=Link\nURL=x\n", "l.desktop"))
        self.assertIsNone(desktop_entry.parse("[Desktop Entry]\nType=Application\nName=x\n", "n.desktop"))

    def test_argv_drops_field_codes_and_expands_the_others(self):
        e = desktop_entry.DesktopEntry("a.desktop", "App", "appicon", '"/opt/my app/run" --flag %F %i %c 100%% %u')
        self.assertEqual(desktop_entry.argv(e), ["/opt/my app/run", "--flag", "--icon", "appicon", "App", "100%"])

    def test_argv_of_a_plain_command(self):
        e = desktop_entry.DesktopEntry("a.desktop", "App", "", "systemsettings")
        self.assertEqual(desktop_entry.argv(e), ["systemsettings"])


class DockTest(unittest.TestCase):
    def entry(self, i, hidden=False):
        return desktop_entry.DesktopEntry(i, i, "", "x", hidden=hidden)

    def test_resolve_keeps_order_and_skips_missing_hidden_and_repeated(self):
        entries = {i: self.entry(i, hidden=(i == "h")) for i in ("a", "b", "h")}
        got = dock.resolve(["b", "zzz", "h", "a", "b"], entries)
        self.assertEqual([e.desktop_id for e in got], ["b", "a"])

    def test_default_pins_are_the_suite_then_the_system_tools(self):
        suite = ["Stagno", "Quire", "Ligature", "Gantry", "Bivouac", "Natter"]
        self.assertEqual(list(dock.DEFAULT_PINS[:6]), [f"io.github.quezka.{a}.desktop" for a in suite])
        self.assertEqual(len(set(dock.DEFAULT_PINS)), len(dock.DEFAULT_PINS))

    def test_magnification_peaks_under_the_pointer_and_fades(self):
        self.assertAlmostEqual(dock.magnification(0), 1.55)
        self.assertGreater(dock.magnification(0), dock.magnification(70))
        self.assertGreater(dock.magnification(70), dock.magnification(200))
        self.assertAlmostEqual(dock.magnification(1000), 1.0, places=3)
        self.assertEqual(dock.magnification(None), 1.0)

    def test_service_uses_user_pins_over_the_default_and_launches(self):
        e = self.entry("x.desktop")
        launched = []
        svc = DockService(lambda: {"x.desktop": e}, lambda: ["x.desktop"], launched.append)
        self.assertEqual(svc.items(), [e])
        svc.open(e)
        self.assertEqual(launched, [e])
        none = DockService(lambda: {"x.desktop": e}, lambda: None, launched.append)
        self.assertEqual(none.items(), [])  # defaults are not installed here


class XdgTest(unittest.TestCase):
    def test_earlier_directory_wins_and_nested_ids_use_dashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, sysd = Path(tmp, "home"), Path(tmp, "sys")
            for base, name in ((home, "Mine"), (sysd, "Theirs")):
                (base / "applications").mkdir(parents=True)
                (base / "applications" / "a.desktop").write_text(f"[Desktop Entry]\nType=Application\nName={name}\nExec=x\n")
            (sysd / "applications" / "kde").mkdir()
            (sysd / "applications" / "kde" / "b.desktop").write_text("[Desktop Entry]\nType=Application\nName=B\nExec=x\n")
            (sysd / "applications" / "broken.desktop").write_bytes(b"\xff\xfe[")
            got = xdg.installed_entries({"XDG_DATA_HOME": str(home), "XDG_DATA_DIRS": str(sysd), "LANG": "C"})
            self.assertEqual(got["a.desktop"].name, "Mine")
            self.assertIn("kde-b.desktop", got)

    def test_user_pins_must_be_a_list_of_strings(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"XDG_CONFIG_HOME": tmp}
            self.assertIsNone(xdg.user_pins(env))
            Path(tmp, "quackos").mkdir()
            conf = Path(tmp, "quackos", "dock.json")
            conf.write_text('["a.desktop", "b.desktop"]')
            self.assertEqual(xdg.user_pins(env), ["a.desktop", "b.desktop"])
            conf.write_text('{"a": 1}')
            self.assertIsNone(xdg.user_pins(env))
            conf.write_text("not json")
            self.assertIsNone(xdg.user_pins(env))

    def test_locales(self):
        self.assertEqual(xdg.locales({"LANG": "it_IT.UTF-8"}), ["it_IT"])
        self.assertEqual(xdg.locales({"LANG": "C"}), [])
        self.assertEqual(xdg.locales({}), [])


class LayeringTest(unittest.TestCase):
    """The same rule as the apps: domain imports nothing of ours or of Qt; app only the domain."""

    def imports(self, folder):
        out = set()
        for path in (ROOT / "shell/quackshell" / folder).glob("*.py"):
            for line in path.read_text().splitlines():
                if line.startswith(("import ", "from ")):
                    out.add(line)
        return out

    def test_domain_is_pure(self):
        for line in self.imports("domain"):
            self.assertNotRegex(line, r"PySide6|\.\.(app|infra|presentation)|quackshell", line)

    def test_app_does_not_touch_qt_infra_or_presentation(self):
        for line in self.imports("app"):
            self.assertNotRegex(line, r"PySide6|\.\.(infra|presentation)", line)


class SessionFilesTest(unittest.TestCase):
    INC = ROOT / "config/includes.chroot_after_packages"

    def test_session_is_registered_and_executables_are_executable(self):
        desktop = (self.INC / "usr/share/wayland-sessions/quackos.desktop").read_text()
        self.assertIn("Exec=/usr/local/bin/quackos-session", desktop)
        for name in ("quackos-session", "quackos-shell"):
            path = self.INC / "usr/local/bin" / name
            self.assertTrue(os.access(path, os.X_OK), name)
            self.assertEqual(subprocess.run(["sh", "-n", str(path)]).returncode, 0, name)
        self.assertIn("labwc -C /usr/share/quackos/labwc", (self.INC / "usr/local/bin/quackos-session").read_text())

    def test_labwc_rc_is_valid_xml_with_traffic_lights_on_the_left(self):
        import xml.dom.minidom
        rc = self.INC / "usr/share/quackos/labwc/rc.xml"
        doc = xml.dom.minidom.parse(str(rc))
        layout = doc.getElementsByTagName("layout")[0].firstChild.data
        left, sep, right = layout.partition(":")
        self.assertEqual((left, sep, right), ("close,iconify,max", ":", ""))
        xml.dom.minidom.parse(str(self.INC / "usr/share/quackos/labwc/menu.xml"))

    def test_theme_has_every_button_image_labwc_asks_for(self):
        theme = self.INC / "usr/share/themes/QuackOS/labwc"
        self.assertTrue((theme / "themerc").is_file())
        for name in ("close", "iconify", "max", "max_toggled"):
            for suffix in ("-active", "-inactive", "_hover-active", "_hover-inactive"):
                self.assertTrue((theme / f"{name}{suffix}.svg").is_file(), f"{name}{suffix}.svg")

    def test_autostart_starts_what_the_session_needs(self):
        text = (self.INC / "usr/share/quackos/labwc/autostart").read_text()
        for needle in ("swaybg", "quackos-shell", "mako", "polkit-kde-authentication-agent-1", "dbus-update-activation-environment"):
            self.assertIn(needle, text)
        self.assertTrue((self.INC / "usr/share/quackos/labwc/environment").is_file())

    def test_every_program_of_the_session_is_in_a_package_list(self):
        lists = "\n".join(p.read_text() for p in (ROOT / "config/package-lists").glob("*.list.chroot"))
        for pkg in ("labwc", "swaybg", "mako-notifier", "fuzzel", "foot", "swaylock", "swayidle", "wlopm", "grim", "slurp",
                    "wl-clipboard", "brightnessctl", "xwayland", "qml6-module-org-kde-layershell", "qt6-wayland",
                    "python3-pyside6.qtquick", "xdg-desktop-portal-wlr", "xdg-desktop-portal-gtk"):
            self.assertRegex(lists, rf"(?m)^{pkg}$", pkg)

    def test_auto_config_stages_the_shell_into_the_image(self):
        text = (ROOT / "auto/config").read_text()
        self.assertIn("cp -r shell/quackshell", text)
        self.assertIn("/usr/lib/quackos/shell/", (ROOT / ".gitignore").read_text())


@unittest.skipUnless(os.environ.get("QUACKSHELL_TEST_PYTHON"), "set QUACKSHELL_TEST_PYTHON to a python with PySide6 to run the QML smoke test")
class QmlSmokeTest(unittest.TestCase):
    def test_bar_and_dock_load_offscreen_without_qml_warnings(self):
        code = (
            "import sys; sys.path.insert(0, %r)\n"
            "from PySide6.QtCore import QTimer\n"
            "from PySide6.QtGui import QGuiApplication\n"
            "import quackshell.presentation.shell as sh\n"
            "orig = QGuiApplication.exec\n"
            "def quick(self=None):\n    QTimer.singleShot(800, QGuiApplication.instance().quit)\n    return orig()\n"
            "QGuiApplication.exec = staticmethod(quick)\n"
            "sys.exit(sh.main(['x']))\n" % str(ROOT / "shell")
        )
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen", QUACKSHELL_PLAIN="1")
        r = subprocess.run([os.environ["QUACKSHELL_TEST_PYTHON"], "-W", "ignore", "-c", code], env=env,
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotRegex(r.stderr, r"qml|QML|TypeError|ReferenceError")


if __name__ == "__main__":
    unittest.main()
