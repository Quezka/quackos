"""Static checks of the macOS-like look: packages, config files, the hook."""
import configparser
import os
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
INC = os.path.join(ROOT, "config", "includes.chroot_after_packages")


def ini(*parts):
    cp = configparser.RawConfigParser(strict=False)
    cp.optionxform = str
    cp.read(os.path.join(INC, *parts), encoding="utf-8")
    return cp


def packages(name):
    with open(os.path.join(ROOT, "config", "package-lists", name)) as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


class AppearanceTest(unittest.TestCase):
    def test_fonts_use_inter(self):
        self.assertIn("fonts-inter", packages("appearance.list.chroot"))
        g = ini("etc", "skel", ".config", "kdeglobals")["General"]
        for key in ("font", "menuFont", "toolBarFont", "smallestReadableFont"):
            self.assertTrue(g[key].startswith("Inter,"), key)
        self.assertEqual(ini("etc", "sddm.conf.d", "quackos.conf")["Theme"]["Font"], "Inter,10")

if __name__ == "__main__":
    unittest.main()
