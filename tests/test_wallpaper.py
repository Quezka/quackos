"""The default Plasma wallpaper must exist in the image: a missing "Next" wallpaper means a black desktop."""
import json
import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
INC = os.path.join(ROOT, "config", "includes.chroot_after_packages")
HOOK = os.path.join(ROOT, "config", "hooks", "live", "0200-quackos-artwork.hook.chroot")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class WallpaperTest(unittest.TestCase):
    def test_wallpaper_package_has_the_id_plasma_asks_for(self):
        meta = json.loads(read(os.path.join(INC, "usr", "share", "wallpapers", "Next", "metadata.json")))
        self.assertEqual(meta["KPackageStructure"], "Wallpaper/Images")
        self.assertEqual(meta["KPlugin"]["Id"], "Next")
        self.assertTrue(meta["KPlugin"]["License"])

    def test_hook_renders_images_into_the_wallpaper_folder(self):
        hook = read(HOOK)
        self.assertIn("W=/usr/share/wallpapers/Next", hook)
        self.assertIn('"$W/contents/images/$size.png"', hook)
        sizes = re.search(r"for size in ([0-9x ]+); do", hook).group(1).split()
        self.assertIn("1366x768", sizes)  # the author's laptop
        self.assertIn("1920x1080", sizes)

    def test_hook_fails_instead_of_silently_skipping(self):
        hook = read(HOOK)
        self.assertIn("set -euo pipefail", hook)
        self.assertNotIn("2>/dev/null | while", hook)  # the old `find ... 2>/dev/null` swallowed a missing folder
        self.assertRegex(hook, r"metadata\.json.*missing.*exit 1")
        self.assertRegex(hook, r"was not rendered.*exit 1")
        self.assertRegex(hook, r"another wallpaper has Id Next.*exit 1")

    def test_sddm_background_points_into_the_wallpaper(self):
        hook = read(HOOK)
        self.assertIn("/usr/share/backgrounds/quackos/quackos.png", hook)
        self.assertRegex(hook, r'ln -sf "\$W/contents/images/1920x1080\.png" /usr/share/backgrounds/quackos/quackos\.png')

    def test_stock_wallpaper_packages_stay_out(self):
        lists = ""
        pl = os.path.join(ROOT, "config", "package-lists")
        for n in os.listdir(pl):
            lists += read(os.path.join(pl, n))
        for name in ("breeze-wallpaper", "plasma-workspace-wallpapers"):
            self.assertNotRegex(lists, r"(?m)^%s\s*$" % name)


if __name__ == "__main__":
    unittest.main()
