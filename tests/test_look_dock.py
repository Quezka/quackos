"""Static checks for step 2 of the macOS-like layout: the bottom panel as a floating dock."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUT = ROOT / "config/includes.chroot_after_packages/usr/local/share/plasma/layout-templates/org.kde.plasma.desktop.defaultPanel/contents/layout.js"


class DockTest(unittest.TestCase):
    def setUp(self):
        self.js = LAYOUT.read_text()

    def test_dock_is_floating_centered_and_at_the_bottom(self):
        for needle in ('panel.location = "bottom"', "panel.floating = true", 'panel.alignment = "center"', 'panel.lengthMode = "fit"'):
            self.assertIn(needle, self.js)

    def test_launcher_moved_to_the_bar_and_dock_has_trash(self):
        self.assertIn('bar.addWidget("org.kde.plasma.kickoff")', self.js)
        self.assertNotIn('panel.addWidget("org.kde.plasma.kickoff")', self.js)
        self.assertIn('panel.addWidget("org.kde.plasma.trash")', self.js)

    def test_pinned_apps_still_there_in_order(self):
        order = ["Stagno", "Quire", "Ligature", "Gantry", "Bivouac", "Natter"]
        pos = [self.js.index(f"io.github.quezka.{a}.desktop") for a in order]
        self.assertEqual(pos, sorted(pos))


if __name__ == "__main__":
    unittest.main()
