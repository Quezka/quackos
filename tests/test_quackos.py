"""Static checks of the QuackOS image definition (no root and no ISO needed)."""
import os
import re
import shutil
import stat
import subprocess
import unittest
import xml.dom.minidom

ROOT = os.path.join(os.path.dirname(__file__), "..")
INC = os.path.join(ROOT, "config", "includes.chroot_after_packages")


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def files(folder, suffix=""):
    out = []
    for base, _dirs, names in os.walk(os.path.join(ROOT, folder)):
        out += [os.path.join(base, n) for n in names if n.endswith(suffix)]
    return sorted(out)


class ImageDefinitionTest(unittest.TestCase):
    def test_version_is_semver(self):
        self.assertRegex(read("VERSION").strip(), r"^\d+\.\d+\.\d+$")

    def test_auto_config_defines_the_image(self):
        cfg = read("auto", "config")
        for needle in ("--distribution trixie", "--binary-images iso-hybrid", "--debian-installer none",
                       "username=quack", "boot=live", "QUACKOS_${VERSION}", "cp VERSION", "cp suite/apps.list"):
            self.assertIn(needle, cfg)

    def test_scripts_are_executable_and_parse(self):
        scripts = ([os.path.join(ROOT, "build.sh")] + files("auto") + files("config/hooks")
                   + [os.path.join(INC, "usr", "local", "bin", "quack"), os.path.join(INC, "usr", "local", "lib", "quackos", "debug-report")]
                   + files("config/includes.chroot_after_packages/usr/lib/live/config") + files("scripts", ".sh"))
        for path in scripts:
            self.assertTrue(os.stat(path).st_mode & stat.S_IXUSR, path + " is not executable")
            self.assertEqual(subprocess.run(["bash", "-n", path]).returncode, 0, path)

    def test_hooks_have_the_right_names_and_order(self):
        names = [os.path.basename(p) for p in files("config/hooks/live")]
        self.assertEqual(names, sorted(names))
        for n in names:
            self.assertRegex(n, r"^\d{4}-[a-z0-9-]+\.hook\.chroot$")
        self.assertTrue(names[-1].startswith("0900-"), "cleanup (initramfs, apt clean) must run last")

    def test_package_lists_are_clean(self):
        seen = set()
        for path in files("config/package-lists", ".list.chroot"):
            for line in read(os.path.relpath(path, ROOT)).splitlines():
                if not line.strip() or line.startswith("#"):
                    continue
                self.assertRegex(line, r"^[a-z0-9][a-z0-9+.\-]+$", "%s: %r" % (path, line))
                self.assertNotIn(line, seen, "duplicate package " + line)
                seen.add(line)
        for essential in ("live-boot", "live-config", "calamares", "sddm", "kde-plasma-desktop", "plymouth",
                          "firefox-esr", "librsvg2-bin", "imagemagick", "jq", "curl", "python3-venv"):
            self.assertIn(essential, seen, essential)

    def test_recommends_that_the_image_cannot_live_without_are_listed(self):
        # The image is built with apt-recommends OFF, so anything that is only a Recommends of a package we
        # install must be listed by hand. Each of these was once missing and broke something real:
        listed = set()
        for path in files("config/package-lists", ".list.chroot"):
            listed |= {line.strip() for line in read(os.path.relpath(path, ROOT)).splitlines()
                       if line.strip() and not line.startswith("#")}
        must = {
            "user-setup": "live-config creates the live user with it: without it, login says wrong password",
            "keyboard-configuration": "live-config keyboard setup", "locales": "live-config locale setup",
            "libpam-systemd": "SDDM / logind sessions", "dbus-user-session": "user sessions",
            "kwin-wayland": "the default Plasma 6 session", "kwin-x11": "the X11 Plasma session (fallback)",
            "xserver-xorg": "X11 sessions", "libgl1-mesa-dri": "Mesa: KWin cannot draw without it",
            "libglx-mesa0": "Mesa GLX", "xwayland": "X11 apps under Wayland (Firefox, apps)",
            "kscreen": "display settings", "powerdevil": "power management", "systemsettings": "KDE settings",
            "firmware-linux": "firmware for real hardware", "firmware-iwlwifi": "Intel Wi-Fi",
            "sudo": "live-config sudo setup",
            "squashfs-tools": "Calamares unpacks the live filesystem with unsquashfs: without it nothing installs",
            "rsync": "Debian's Calamares wrapper", "x11-xserver-utils": "xhost, used by calamares-install-debian",
            "wpasupplicant": "WPA Wi-Fi in NetworkManager", "systemd-timesyncd": "the clock",
        }
        for package, why in must.items():
            self.assertIn(package, listed, "%s is missing (%s)" % (package, why))

    def test_image_tree_does_not_clobber_the_usrmerge_symlinks(self):
        # In Debian 13 /lib, /bin, /sbin and /lib64 are symlinks into /usr: a real directory with one of those names
        # in the include tree would replace the symlink and break the whole system.
        for name in ("lib", "lib64", "bin", "sbin"):
            self.assertFalse(os.path.exists(os.path.join(INC, name)), "includes/%s would clobber the /%s symlink" % (name, name))

    def test_live_session_defaults_to_x11(self):
        script = read("config", "includes.chroot_after_packages", "usr", "lib", "live", "config", "0086-quackos-session")
        self.assertIn(". /usr/lib/live/config.sh", script)
        self.assertIn("quackos.wayland", script)
        # run the very sed the script uses on what live-config's 0085-sddm writes
        command = re.search(r"sed -i '([^']+)' /etc/sddm\.conf", script).group(1)
        written = "[Autologin]\nUser=quack\nSession=plasma.desktop\n"
        out = subprocess.run(["sed", command], input=written, capture_output=True, text=True).stdout
        self.assertEqual(out, "[Autologin]\nUser=quack\nSession=plasmax11.desktop\n")
        # and it must run AFTER live-config's own sddm component
        self.assertGreater("0086-quackos-session", "0085-sddm")

    def test_installer_launcher_replaces_debians(self):
        # Debian's calamares-desktop-icon autostart copies this exact file to the live desktop
        path = os.path.join("config", "includes.chroot_after_packages", "usr", "share", "applications",
                            "calamares-install-debian.desktop")
        text = read(path)
        self.assertIn("Name=Install QuackOS", text)
        self.assertIn("Exec=calamares-install-debian", text)       # Debian's wrapper: sudo + xhost + pkexec
        self.assertIn("Icon=quackos", text)
        self.assertNotIn("pkexec /usr/bin/calamares", text)
        self.assertIn("/usr/share/icons/hicolor/scalable/apps/quackos.svg", read("config", "hooks", "live", "0200-quackos-artwork.hook.chroot"))

    def test_ntfs_is_safe_by_default(self):
        conf = read("config", "includes.chroot_after_packages", "etc", "udisks2", "mount_options.conf")
        drivers = re.search(r"^ntfs_drivers=(\S+)$", conf, re.M).group(1)
        # ntfs-3g refuses hibernated (Fast Startup) volumes; udisks falls back to the next driver, so ntfs3 must not be listed
        self.assertEqual(drivers, "ntfs")
        self.assertIn("ntfs-3g", self.listed())

    def test_secure_boot_and_splash_on_the_installed_system(self):
        self.assertIn("grub-efi-amd64-signed", self.listed())
        self.assertIn("shim-signed", self.listed())
        cfg = read("config", "includes.chroot_after_packages", "etc", "default", "grub.d", "quackos.cfg")
        self.assertIn('GRUB_DISTRIBUTOR="QuackOS"', cfg)
        self.assertIn("splash", cfg)

    def test_calamares_branding_uses_keys_calamares_knows(self):
        # verified against libcalamaresui 3.3.14 (trixie) and Debian's own branding.desc: these are the real key names
        desc = read("config", "includes.chroot_after_packages", "usr", "share", "calamares", "branding", "quackos", "branding.desc")
        for key in ("SidebarBackground:", "SidebarText:", "SidebarTextCurrent:", "SidebarBackgroundCurrent:", "sidebar: widget", "navigation: widget"):
            self.assertIn(key, desc)
        for wrong in ("sidebarBackground", "sidebarTextSelect", "sidebarTextHighlight", "sidebar: left"):
            self.assertNotIn(wrong, desc)

    def test_plasma_panel_pins_only_apps_that_exist(self):
        layout = read("config", "includes.chroot_after_packages", "usr", "local", "share", "plasma", "layout-templates",
                      "org.kde.plasma.desktop.defaultPanel", "contents", "layout.js")
        self.assertEqual(layout.count("{"), layout.count("}"))
        self.assertEqual(layout.count("("), layout.count(")"))
        self.assertEqual(layout.count("["), layout.count("]"))
        pinned = re.findall(r'"applications:([^"]+)"', layout)
        suite = ["io.github.quezka.%s.desktop" % n for n in ("Stagno", "Quire", "Ligature", "Gantry", "Bivouac", "Natter")]
        for desktop in suite:
            self.assertIn(desktop, pinned)
        # the others come from Debian packages that must be in the lists
        self.assertIn("firefox-esr.desktop", pinned)
        for package in ("firefox-esr", "dolphin", "konsole"):
            self.assertIn(package, self.listed())

    def listed(self):
        out = set()
        for path in files("config/package-lists", ".list.chroot"):
            out |= {line.strip() for line in read(os.path.relpath(path, ROOT)).splitlines()
                    if line.strip() and not line.startswith("#")}
        return out

    def test_suite_manifest(self):
        apps = {}
        for line in read("suite", "apps.list").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            name, repo, pattern = line.split(None, 2)
            re.compile(pattern)
            self.assertRegex(repo, r"^Quezka/[\w.-]+$")
            apps[name] = (repo, pattern)
        for must in ("stagno", "quire", "ligature", "gantry", "bivouac", "natter"):
            self.assertIn(must, apps)
        self.assertEqual(apps["stagno"][0], "Quezka/ducknet")      # Stagno's .deb lives in the DuckNet repo
        # the .deb names the apps' own release workflows really produce
        self.assertTrue(re.search(apps["stagno"][1], "stagno_0.4.0_amd64.deb"))
        self.assertTrue(re.search(apps["natter"][1], "natter_0.7.0_all.deb"))
        self.assertFalse(re.search(apps["quire"][1], "Quire-0.32.2-windows-x64-setup.exe"))

    def test_suite_download_verifies_checksums(self):
        script = read("scripts", "fetch-suite.py")
        self.assertIn("refusing to install it unverified", script)
        self.assertIn("refusing to use it", script)
        self.assertIn("python3 scripts/fetch-suite.py", read("build.sh"))

    def test_ducknet_hook_uses_the_stagno_version(self):
        hook = read("config", "hooks", "live", "0400-quackos-ducknet.hook.chroot")
        self.assertIn("suite-versions.txt", hook)
        self.assertIn("set -euo pipefail", hook)

    def test_os_release(self):
        text = read("config", "includes.chroot_after_packages", "usr", "share", "quackos", "os-release.template")
        fields = dict(line.split("=", 1) for line in text.strip().splitlines())
        self.assertEqual(fields["ID"], "quackos")
        self.assertEqual(fields["ID_LIKE"], "debian")
        self.assertIn("@VERSION@", fields["VERSION_ID"])
        self.assertEqual(fields["NAME"], '"QuackOS"')

    def test_artwork_is_well_formed(self):
        svgs = files("config/includes.chroot_after_packages/usr/share/quackos/branding", ".svg")
        self.assertGreaterEqual(len(svgs), 4)
        for svg in svgs:
            xml.dom.minidom.parse(svg)

    def test_every_rendered_artwork_has_a_source(self):
        hook = read("config", "hooks", "live", "0200-quackos-artwork.hook.chroot")
        for source in set(re.findall(r"\brender (\S+) \d+ \d+", hook)):
            self.assertTrue(os.path.isfile(os.path.join(INC, "usr", "share", "quackos", "branding", source + ".svg")), source)

    def test_plymouth_theme(self):
        theme = os.path.join(INC, "usr", "share", "plymouth", "themes", "quackos")
        self.assertIn("ModuleName=script", read(os.path.relpath(os.path.join(theme, "quackos.plymouth"), ROOT)))
        script = read(os.path.relpath(os.path.join(theme, "quackos.script"), ROOT))
        self.assertIn("Plymouth.SetBootProgressFunction", script)
        for image in re.findall(r'Image\("([^"]+)"\)', script):       # each one is rendered by the artwork hook
            self.assertIn(image, read("config", "hooks", "live", "0200-quackos-artwork.hook.chroot"))

    def test_calamares_branding(self):
        desc = read("config", "includes.chroot_after_packages", "usr", "share", "calamares", "branding", "quackos", "branding.desc")
        for key in ("componentName: quackos", "productName:", "slideshow:", "bootloaderEntryName:"):
            self.assertIn(key, desc)
        self.assertIn("branding: quackos", read("config", "hooks", "live", "0500-quackos-calamares.hook.chroot"))

    def test_no_generated_files_are_tracked(self):
        git = shutil.which("git")
        if not git or not os.path.isdir(os.path.join(ROOT, ".git")):
            self.skipTest("not a git checkout")
        tracked = subprocess.run([git, "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
        for path in tracked:
            self.assertFalse(path.endswith((".iso", ".log")), path)
            self.assertNotIn("usr/share/quackos/version", path)
            self.assertNotIn("usr/share/quackos/apps.list", path)


class FetchSuiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("fetch_suite", os.path.join(ROOT, "scripts", "fetch-suite.py"))
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def release(self, **asset):
        base = {"name": "stagno_1.0.0_amd64.deb", "browser_download_url": "https://x/a.deb", "digest": "sha256:" + "a" * 64}
        base.update(asset)
        return {"tag_name": "v1.0.0", "assets": [{"name": "Stagno-1.0.0-windows-x64-setup.exe", "browser_download_url": "u", "digest": "sha256:" + "b" * 64}, base]}

    def test_manifest_is_parsed(self):
        apps = self.mod.parse_manifest(read("suite", "apps.list"))
        self.assertIn("stagno", [name for name, _repo, _pattern in apps])

    def test_picks_the_matching_asset_and_its_digest(self):
        pattern = self.mod.re.compile(r"^stagno_.*_amd64\.deb$")
        name, url, digest = self.mod.pick_asset(self.release(), pattern)
        self.assertEqual((name, url, digest), ("stagno_1.0.0_amd64.deb", "https://x/a.deb", "a" * 64))

    def test_refuses_an_asset_without_a_checksum(self):
        pattern = self.mod.re.compile(r"^stagno_.*_amd64\.deb$")
        for digest in (None, "", "md5:abc", "sha256:xyz"):
            with self.assertRaises(self.mod.SuiteError, msg=repr(digest)):
                self.mod.pick_asset(self.release(digest=digest), pattern)

    def test_refuses_a_release_without_the_file(self):
        with self.assertRaises(self.mod.SuiteError):
            self.mod.pick_asset(self.release(), self.mod.re.compile(r"^nothing$"))


class QuackCommandTest(unittest.TestCase):
    QUACK = os.path.join(INC, "usr", "local", "bin", "quack")

    def run_quack(self, *args):
        return subprocess.run(["bash", self.QUACK, *args], capture_output=True, text=True)

    def test_say(self):
        r = self.run_quack("say", "hello", "pond")
        self.assertEqual(r.returncode, 0)
        self.assertIn("hello pond", r.stdout)
        self.assertIn("<(o )___", r.stdout)

    def test_help_lists_every_command(self):
        out = self.run_quack("help").stdout
        for command in ("say", "update", "dns", "version", "help"):
            self.assertIn("quack " + command, out)

    def test_unknown_command_fails(self):
        r = self.run_quack("nonsense")
        self.assertEqual(r.returncode, 2)
        self.assertIn("unknown command", r.stderr)

    def test_dns_mentions_the_duck_server(self):
        self.assertIn("dns.quezka.uk", self.run_quack("dns").stdout)


if __name__ == "__main__":
    unittest.main()
