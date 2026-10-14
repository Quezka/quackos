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
from quackshell.domain import desktop_entry, dock, windows as win  # noqa: E402
from quackshell.infra import toplevels, xdg  # noqa: E402

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
        items = svc.items()
        self.assertEqual([i.entry for i in items], [e])
        svc.open(items[0])
        self.assertEqual(launched, [e])
        none = DockService(lambda: {"x.desktop": e}, lambda: None, launched.append)
        self.assertEqual(none.items(), [])  # defaults are not installed here

    def test_running_apps_get_a_dot_and_a_click_raises_instead_of_launching(self):
        q = desktop_entry.DesktopEntry("io.github.quezka.Quire.desktop", "Quire", "q", "/opt/quire/Quire")
        launched, raised = [], []
        svc = DockService(lambda: {q.desktop_id: q}, lambda: [q.desktop_id], launched.append, raised.append)
        items = svc.items([win.Window(7, "t", "io.github.quezka.Quire")])
        self.assertEqual((items[0].running, items[0].pinned), (1, True))
        svc.open(items[0])
        self.assertEqual((launched, raised), ([], [7]))

    def test_unpinned_running_apps_follow_the_pins_and_unknown_ones_are_grouped(self):
        q = desktop_entry.DesktopEntry("q.desktop", "Quire", "q", "quire")
        k = desktop_entry.DesktopEntry("k.desktop", "Kate", "k", "kate")
        svc = DockService(lambda: {"q.desktop": q, "k.desktop": k}, lambda: ["q.desktop"], lambda e: None)
        items = svc.items([win.Window(1, app_id="kate"), win.Window(2, app_id="weird"), win.Window(3, app_id="weird")])
        self.assertEqual([(i.entry.name, i.pinned, i.running) for i in items],
                         [("Quire", True, 0), ("Kate", False, 1), ("weird", False, 2)])


class WindowsTest(unittest.TestCase):
    E = [desktop_entry.DesktopEntry("io.github.quezka.Quire.desktop", "Quire", "q", "/opt/quire/Quire"),
         desktop_entry.DesktopEntry("org.kde.dolphin.desktop", "Files", "d", "dolphin %u"),
         desktop_entry.DesktopEntry("fx.desktop", "Firefox", "f", "firefox-esr %u", wm_class="Navigator")]

    def test_app_id_matches_the_id_its_last_segment_the_wm_class_or_the_command(self):
        for app_id, want in (("io.github.quezka.Quire", "Quire"), ("quire", "Quire"), ("Quire", "Quire"),
                             ("org.kde.dolphin", "Files"), ("dolphin", "Files"), ("navigator", "Firefox"),
                             ("firefox-esr", "Firefox")):
            self.assertEqual(win.entry_for(app_id, self.E).name, want, app_id)
        self.assertIsNone(win.entry_for("nothing", self.E))
        self.assertIsNone(win.entry_for("", self.E))

    def test_active_name_is_the_focused_visible_window(self):
        ws = [win.Window(1, "a", "dolphin"), win.Window(2, "page", "navigator", activated=True)]
        self.assertEqual(win.active_name(ws, self.E), "Firefox")
        self.assertEqual(win.active_name([win.Window(3, "t", "zzz", activated=True)], self.E), "zzz")
        self.assertEqual(win.active_name([win.Window(4, "t", "zzz", activated=True, minimized=True)], self.E), "")
        self.assertEqual(win.active_name([], self.E), "")

    def test_next_to_raise_prefers_minimized_then_cycles(self):
        a, b, c = win.Window(1), win.Window(2, activated=True), win.Window(3)
        self.assertIsNone(win.next_to_raise([]))
        self.assertEqual(win.next_to_raise([a, b, c]).id, 3)
        self.assertEqual(win.next_to_raise([a, c, b]).id, 1)
        self.assertEqual(win.next_to_raise([a, win.Window(9, minimized=True), b]).id, 9)
        self.assertEqual(win.next_to_raise([a, c]).id, 1)

    def test_state_array_flags(self):
        w = win.apply_state(win.Window(1, "t", "a"), {win.ACTIVATED})
        self.assertEqual((w.activated, w.minimized), (True, False))
        w = win.apply_state(w, {win.MINIMIZED})
        self.assertEqual((w.activated, w.minimized), (False, True))


class TrackerTest(unittest.TestCase):
    def setUp(self):
        self.seen = []
        self.t = toplevels.Tracker(self.seen.append)

    def test_a_window_appears_only_when_done_arrives(self):
        self.t.opened(1)
        self.t.title(1, "Doc")
        self.t.app_id(1, "quire")
        self.assertEqual(self.seen, [])
        self.t.done(1)
        self.assertEqual([(w.title, w.app_id) for w in self.seen[-1]], [("Doc", "quire")])

    def test_state_accepts_the_raw_array_and_a_list(self):
        import struct
        self.t.opened(1)
        self.t.state(1, struct.pack("II", 2, 3))
        self.t.done(1)
        self.assertTrue(self.seen[-1][0].activated)
        self.t.state(1, [1])
        self.t.done(1)
        self.assertEqual((self.seen[-1][0].activated, self.seen[-1][0].minimized), (False, True))

    def test_order_is_the_order_of_first_appearance_and_closing_removes(self):
        for i in (1, 2, 3):
            self.t.opened(i)
            self.t.done(i)
        self.t.title(1, "changed")
        self.t.done(1)
        self.assertEqual([w.id for w in self.seen[-1]], [1, 2, 3])
        self.t.closed(2)
        self.assertEqual([w.id for w in self.seen[-1]], [1, 3])
        count = len(self.seen)
        self.t.closed(99)          # unknown, or closed before done: nothing to tell
        self.assertEqual(len(self.seen), count)


class ProtocolFilesTest(unittest.TestCase):
    def test_generated_bindings_match_the_xml_and_import_the_core_from_pywayland(self):
        out = ROOT / "shell/quackshell/infra/protocols/wlr_foreign_toplevel_management_unstable_v1"
        xml = (ROOT / "shell/protocols/wlr-foreign-toplevel-management-unstable-v1.xml").read_text()
        self.assertIn('name="wlr_foreign_toplevel_management_unstable_v1"', xml)
        for f in ("zwlr_foreign_toplevel_manager_v1.py", "zwlr_foreign_toplevel_handle_v1.py", "__init__.py"):
            text = (out / f).read_text()
            self.assertNotIn("from ..wayland", text, f)
        self.assertIn("from pywayland.protocol.wayland import WlSeat",
                      (out / "zwlr_foreign_toplevel_handle_v1.py").read_text())


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

    def test_session_script_logs_and_retries_with_the_software_renderer(self):
        text = (self.INC / "usr/local/bin/quackos-session").read_text()
        for needle in ("quackos-session.log", "WLR_RENDERER=pixman", "WLR_NO_HARDWARE_CURSORS=1", "labwc -C /usr/share/quackos/labwc"):
            self.assertIn(needle, text)
        self.assertLess(text.index('try "default renderer"'), text.index('try "software renderer"'))

    def test_boot_parameter_picks_the_autologin_session(self):
        text = (self.INC / "usr/lib/live/config/0086-quackos-session").read_text()
        self.assertIn("quackos.session=*)", text)
        self.assertEqual(subprocess.run(["sh", "-n", str(self.INC / "usr/lib/live/config/0086-quackos-session")]).returncode, 0)
        # a name with a slash or a space must never reach sed
        self.assertIn("*[!a-zA-Z0-9_.-]*)", text)

    def test_build_and_try_scripts_exist_and_parse(self):
        for name in ("local-build.sh", "try-iso.sh"):
            path = ROOT / "scripts" / name
            self.assertTrue(os.access(path, os.X_OK), name)
            self.assertEqual(subprocess.run(["bash", "-n", str(path)]).returncode, 0, name)
        self.assertIn("--privileged", (ROOT / "scripts/local-build.sh").read_text())

    def test_local_build_cleans_up_but_keeps_the_cache_until_a_build_works(self):
        inner = (ROOT / "scripts/container-build.sh").read_text()
        self.assertIn("trap cleanup EXIT", inner)            # runs on failure too
        for gone in ("/build/chroot", "/build/binary", "/build/.build"):
            self.assertIn(gone, inner)
        self.assertIn("/work/.quackos-works", inner)
        self.assertIn("rm -rf /build/cache", inner)
        self.assertLess(inner.index("rm -rf /build/chroot"), inner.index("rm -rf /build/cache"))
        outer = (ROOT / "scripts/local-build.sh").read_text()
        self.assertIn("image prune", outer)
        self.assertIn("tail -n +3", outer)                   # only the 2 newest ISOs stay
        self.assertEqual(subprocess.run(["bash", "-n", str(ROOT / "scripts/container-build.sh")]).returncode, 0)
        self.assertIn("/.quackos-works", (ROOT / ".gitignore").read_text())

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
                    "python3-pyside6.qtquick", "python3-pywayland", "xdg-desktop-portal-wlr", "xdg-desktop-portal-gtk"):
            self.assertRegex(lists, rf"(?m)^{pkg}$", pkg)

    def test_dev_versions_are_published_as_prereleases(self):
        wf = (ROOT / ".github/workflows/build.yml").read_text()
        self.assertIn("--prerelease", wf)
        self.assertIn("*-*)", wf)

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
