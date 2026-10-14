#!/usr/bin/env bash
# Builds the QuackOS ISO on THIS machine, whatever the distro, inside a Debian 13 container (like the CI does).
#   scripts/local-build.sh            gzip squashfs: ~3x faster, ISO a bit bigger: for testing
#   QUACKOS_COMPRESSION=xz scripts/local-build.sh     what a release uses
# Needs docker (apt install docker.io) and ~25 GB free. If you are not in the `docker` group it asks for your
# password through pkexec. The build tree lives in the docker volume `quackos-build` (it keeps the downloaded
# packages, so the second build is much faster); the ISO lands in ./out/ and is yours.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v docker >/dev/null || { echo "docker is missing: apt install docker.io" >&2; exit 1; }
docker=(docker)
docker info >/dev/null 2>&1 || docker=(pkexec docker)

mkdir -p out
env_file="$(mktemp)"
trap 'rm -f "$env_file"' EXIT
chmod 600 "$env_file"
# the suite is downloaded from the GitHub API: a token avoids the anonymous rate limit
if command -v gh >/dev/null && token="$(gh auth token 2>/dev/null)" && [ -n "$token" ]; then
    echo "GITHUB_TOKEN=$token" >> "$env_file"
fi
echo "QUACKOS_COMPRESSION=${QUACKOS_COMPRESSION:-gzip}" >> "$env_file"

"${docker[@]}" run --rm --privileged --env-file "$env_file" \
    -v quackos-build:/build -v "$PWD":/work:ro -v "$PWD/out":/out \
    -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
    debian:trixie bash -c '
    set -euo pipefail
    apt-get update
    apt-get install -y --no-install-recommends live-build debootstrap squashfs-tools xorriso rsync \
        ca-certificates curl jq git sudo python3
    # fresh sources every time, but keep the package cache and the previous chroot download state
    rsync -a --delete --exclude=/.git --exclude=/out --exclude=/cache --exclude=/chroot --exclude=/binary \
        --exclude=/.build --exclude="/live-image-*" --exclude="/*.iso" /work/ /build/
    cd /build
    lb clean >/dev/null 2>&1 || true
    ./build.sh
    cp out/quackos-*-amd64.iso out/quackos-*-amd64.iso.sha256 /out/
    chown "$HOST_UID:$HOST_GID" /out/quackos-*-amd64.iso /out/quackos-*-amd64.iso.sha256
'
ls -lh out/quackos-*-amd64.iso
