"""Static checks for step 1 of the macOS-like layout: the menu bar on top (the real check is a look at the screen)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "config/includes.chroot_after_packages/usr/local/share/plasma/layout-templates/org.kde.plasma.desktop.defaultPanel/contents/layout.js"
LIST = ROOT / "config/package-lists/look.list.chroot"


class MenuBarTest(unittest.TestCase):
    def setUp(self):
        self.js = LAYOUT.read_text()

    def test_bar_on_top_with_global_menu_tray_and_clock(self):
        for needle in ('bar.location = "top"', 'bar.addWidget("org.kde.plasma.appmenu")',
                       'bar.addWidget("org.kde.plasma.systemtray")', 'bar.addWidget("org.kde.plasma.digitalclock")'):
            self.assertIn(needle, self.js)

    def test_bottom_panel_still_has_the_pinned_tasks(self):
        self.assertIn('var tasks = panel.addWidget("org.kde.plasma.icontasks")', self.js)
        self.assertIn('panel.location = "bottom"', self.js)

    def test_braces_balance(self):
        code = re.sub(r"//.*|/\*.*?\*/", "", self.js, flags=re.S)
        code = re.sub(r'"[^"\n]*"', '""', code)
        for a, b in ("{}", "()", "[]"):
            self.assertEqual(code.count(a), code.count(b))

    def test_gtk_menu_package_listed(self):
        lines = [l.strip() for l in LIST.read_text().splitlines() if l.strip() and not l.startswith("#")]
        self.assertEqual(lines, ["appmenu-gtk3-module"])


if __name__ == "__main__":
    unittest.main()
