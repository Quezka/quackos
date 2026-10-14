#!/usr/bin/env bash
# Runs INSIDE the Debian 13 container started by scripts/local-build.sh (the repo is mounted read-only on /work, the
# persistent volume on /build, the output folder on /out). Not meant to be run by hand.
set -euo pipefail

cleanup() {
    status=$?
    # What a build leaves behind and no later build needs: the chroot (3+ GB), the ISO tree, live-build's state
    rm -rf /build/chroot /build/binary /build/.build /build/live-image-* /build/*.iso /build/out /build/config/packages.chroot
    # What the next build DOES reuse: /build/cache (debootstrap tarball and downloaded packages). It goes only when the
    # author has declared a build that works (an empty file `.quackos-works` in the repo): then it is just clutter.
    if [ -e /work/.quackos-works ]; then
        rm -rf /build/cache
        echo "cleanup: .quackos-works exists, the package cache was removed too"
    else
        echo "cleanup: build tree removed, package cache kept ($(du -sh /build/cache 2>/dev/null | cut -f1))"
    fi
    exit "$status"
}
trap cleanup EXIT

apt-get update
apt-get install -y --no-install-recommends live-build debootstrap squashfs-tools xorriso rsync \
    ca-certificates curl jq git sudo python3
# fresh sources every time; the cache and the previous state are kept out of the sync
rsync -a --delete --exclude=/.git --exclude=/out --exclude=/cache --exclude=/chroot --exclude=/binary \
    --exclude=/.build --exclude="/live-image-*" --exclude="/*.iso" /work/ /build/
cd /build
lb clean >/dev/null 2>&1 || true
./build.sh
cp out/quackos-*-amd64.iso out/quackos-*-amd64.iso.sha256 /out/
chown "$HOST_UID:$HOST_GID" /out/quackos-*-amd64.iso /out/quackos-*-amd64.iso.sha256
