# Changelog

## [0.1.1] - 2026-10-13

- Fix: the live user `quack` was never created, so the login said "wrong password". `live-config` only *recommends* `user-setup`, and the image is built without recommends. The other recommended packages a working desktop needs are now listed too (Plasma sessions, Mesa, X.org, firmware, Wi-Fi, `squashfs-tools` for the installer...), and the CI boot test fails if the user, the autologin or the installer tools are missing.
- The live session now logs into Plasma on **X11** (works on much more hardware than Wayland); boot with `quackos.wayland` to get Wayland.
- The "Install QuackOS" icon now uses Debian's own Calamares launcher (the old one could not open a window), branded as QuackOS.
- NTFS: `ntfs-3g` is installed and udisks2 is set to use **only** it, so a Windows volume left hibernated (Fast Startup) is refused instead of being written to (`docs/ntfs-e-dual-boot.md`). Not yet tested on real hardware.
- Real-laptop hardware (ThinkPad, Skylake): i915 firmware (`firmware-intel-graphics`, only a Recommends before, so it was missing), `power-profiles-daemon`, Intel VA-API video decode.
- Fix: the desktop background was black. Plasma 6.3's default wallpaper (Id "Next") lives in a package that is not in the image; QuackOS now ships its own wallpaper package with that Id and the build fails if it cannot be rendered.
- Installed system: signed GRUB (`grub-efi-amd64-signed`, for Secure Boot) and `quiet splash` on the kernel command line.
- Calamares branding fixed against Calamares 3.3.14 (real key names, `sidebar: widget`, slideshow timer, Plymouth password prompt callbacks).
- Plasma panel with the Quezka suite and everyday apps pinned (layout template under `/usr/local/share`; not yet seen on screen).
- Italian user guide (`docs/guida-utente.md`).
- Faster CI: gzip compression for test builds (xz only for releases), jobs run in parallel, docs-only changes skip the ISO build.

## [0.1.0] - 2026-10-13

- First definition of QuackOS: Debian 13 + KDE Plasma 6 live image (live-build), Calamares installer, QuackOS identity,
  artwork, boot splash, `quack` command, and the Quezka suite (Stagno, Quire, Ligature, Gantry, Bivouac, Natter, DuckNet CLI) preinstalled from GitHub releases with SHA-256 verification.
- CI builds the ISO in a Debian 13 container, boots it in QEMU, and publishes it on tags.
