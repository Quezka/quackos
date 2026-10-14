# Changelog

## [Unreleased] - desktop of our own (branch de-work)

- A second session, "QuackOS", next to Plasma: the labwc compositor with our own shell (top bar and magnifying dock, PySide6/QML on layer-shell), traffic-light window buttons on the left, Super as Command. Plasma stays the default for now; the plan is in `docs/de-design.md`. Not tested on a real screen yet.

## [0.1.2] - 2026-10-14

- macOS-like look: a thin menu bar on top with the global menu, a floating centred dock at the bottom (with the Quezka suite pinned and the trash), Inter as the interface font, Bibata cursors, window buttons on the left, blur. The first time it is seen on a screen is on real hardware: nothing in CI renders it.
- Smaller ISO: live-build no longer auto-installs every firmware package (about 110 MB of switch, datacenter-GPU, server-NIC, TV-tuner and old Wi-Fi firmware nobody needs); the firmware we want is listed by hand, including Mediatek and Nvidia graphics.
- The CI no longer boots the ISO in QEMU; it opens the image and checks 41 paths instead (`scripts/image-check.py`).
- `server/quackos-pull.sh`, a systemd service and timer so the home server mirrors the release ISO from GitHub (`docs/server-mirror.md`), and `docs/runner-self-hosted.md` on why a self-hosted runner on a public repo is risky.
- Hardware matrix (`docs/hardware.md`) and an ISO size report script.

## [0.1.1] - 2026-10-13

- Fix: the live user `quack` was never created, so the login said "wrong password". `live-config` only *recommends* `user-setup`, and the image is built without recommends. The other recommended packages a working desktop needs are now listed too (Plasma sessions, Mesa, X.org, firmware, Wi-Fi, `squashfs-tools` for the installer...), and the CI boot test fails if the user, the autologin or the installer tools are missing.
- The live session now logs into Plasma on **X11** (works on much more hardware than Wayland); boot with `quackos.wayland` to get Wayland.
- The "Install QuackOS" icon now uses Debian's own Calamares launcher (the old one could not open a window), branded as QuackOS.
- NTFS: `ntfs-3g` is installed and udisks2 is set to use **only** it, so a Windows volume left hibernated (Fast Startup) is refused instead of being written to (`docs/ntfs-e-dual-boot.md`). Not yet tested on real hardware.
- Real-laptop hardware (ThinkPad, Skylake): i915 firmware (`firmware-intel-graphics`, only a Recommends before, so it was missing), `power-profiles-daemon`, Intel VA-API video decode.
- Fix: the desktop background was black. Plasma 6.3's default wallpaper (Id "Next") lives in a package that is not in the image; QuackOS now ships its own wallpaper package with that Id and the build fails if it cannot be rendered.
- General hardware coverage (`docs/hardware.md`): Broadcom Wi-Fi firmware, Sound Open Firmware for Intel laptops from Tiger Lake on, ALSA UCM profiles, screen rotation sensor, and guest tools for QEMU/KVM, SPICE and VMware. Mediatek Wi-Fi, NVIDIA firmware and fingerprint readers wait for 0.1.2.
- Installed system: signed GRUB (`grub-efi-amd64-signed`, for Secure Boot) and `quiet splash` on the kernel command line.
- Calamares branding fixed against Calamares 3.3.14 (real key names, `sidebar: widget`, slideshow timer, Plymouth password prompt callbacks).
- Plasma panel with the Quezka suite and everyday apps pinned (layout template under `/usr/local/share`; not yet seen on screen).
- Italian user guide (`docs/guida-utente.md`).
- Faster CI: gzip compression for test builds (xz only for releases), jobs run in parallel, docs-only changes skip the ISO build.

## [0.1.0] - 2026-10-13

- First definition of QuackOS: Debian 13 + KDE Plasma 6 live image (live-build), Calamares installer, QuackOS identity,
  artwork, boot splash, `quack` command, and the Quezka suite (Stagno, Quire, Ligature, Gantry, Bivouac, Natter, DuckNet CLI) preinstalled from GitHub releases with SHA-256 verification.
- CI builds the ISO in a Debian 13 container, boots it in QEMU, and publishes it on tags.
