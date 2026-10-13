# QuackOS

Quezka's Linux distro: Debian 13 + KDE Plasma 6 + Calamares, built with live-build, with the user's whole app suite
preinstalled. Same author as Quire/Ligature/DuckNet; shared memory note: `quackos-project` in the claude-memory repo.

- Entry points: `auto/config` (all live-build options), `build.sh`, hooks in `config/hooks/live/NNNN-*.hook.chroot` (run in order; 0900 cleanup last), files for the image in `config/includes.chroot_after_packages/`.
- Single sources: `VERSION` and `suite/apps.list`; `auto/config` copies them into the image tree (those copies are gitignored). Never edit the copies.
- The suite hook downloads each app's latest GitHub release `.deb` and REFUSES unverified downloads (SHA-256 from the GitHub API). Keep that.
- Tests (`python3 -m unittest discover -s tests`) are static: no root, no ISO. A real build only happens in CI (`debian:trixie` container) or on a Debian 13 box with ~15 GB free. This laptop cannot build it (no live-build, nearly full disk).
- Package names and `lb config` flags were written from documentation and have NOT been verified by a real build: expect CI iterations. Check `docs/design.md` "Cosa NON è verificato".
- GitHub release assets are limited to 2 GiB: the release job splits the ISO if needed.
