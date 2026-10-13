# Changelog

## [0.1.0] - 2026-10-13

- First definition of QuackOS: Debian 13 + KDE Plasma 6 live image (live-build), Calamares installer, QuackOS identity,
  artwork, boot splash, `quack` command, and the Quezka suite (Stagno, Quire, Ligature, Gantry, Bivouac, Natter, DuckNet CLI) preinstalled from GitHub releases with SHA-256 verification.
- CI builds the ISO in a Debian 13 container, boots it in QEMU, and publishes it on tags.
