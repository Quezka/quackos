#!/usr/bin/env bash
# Builds the QuackOS ISO into ./out/. Needs root (live-build uses chroot and mounts) and about
# 15 GB of free disk. Best run inside a Debian 13 container or VM; see docs/building.md.
#   sudo ./build.sh            full build
#   sudo ./build.sh --clean    remove the build tree first
set -euo pipefail
cd "$(dirname "$0")"

if [ "$(id -u)" -ne 0 ]; then
    echo "QuackOS needs root to build: run  sudo ./build.sh" >&2
    exit 1
fi
for tool in lb debootstrap mksquashfs xorriso; do
    command -v "$tool" >/dev/null || { echo "Missing '$tool'. On Debian: apt install live-build debootstrap squashfs-tools xorriso" >&2; exit 1; }
done
if [ "${1:-}" = "--clean" ]; then
    lb clean --purge || true
fi

VERSION="$(cat VERSION)"
lb config
lb build

mkdir -p out
iso="$(ls -1 ./*.iso | head -n1)"
final="out/quackos-${VERSION}-amd64.iso"
mv "$iso" "$final"
( cd out && sha256sum "$(basename "$final")" > "$(basename "$final").sha256" )
echo "Done: $final ($(du -h "$final" | cut -f1))"
