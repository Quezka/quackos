#!/usr/bin/env bash
# Builds the QuackOS ISO on THIS machine, whatever the distro, inside a Debian 13 container (like the CI does).
#   scripts/local-build.sh            gzip squashfs: ~3x faster, ISO a bit bigger: for testing
#   QUACKOS_COMPRESSION=xz scripts/local-build.sh     what a release uses
# Needs docker (apt install docker.io) and ~25 GB free. If you are not in the `docker` group it asks for your
# password through pkexec. The ISO lands in ./out/ and is yours.
#
# Cleanup (automatic, after every build, even a failed one):
#   - the build tree in the docker volume `quackos-build` (chroot, ISO tree: several GB) is removed, but its package
#     cache is KEPT so the next build is fast, until you create an empty file `.quackos-works` in the repo (meaning
#     "we have a working build"): then the cache goes too;
#   - dangling docker images are pruned (the debian:trixie base image is kept);
#   - only the 2 newest ISOs stay in ./out/.
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

status=0
"${docker[@]}" run --rm --privileged --env-file "$env_file" \
    -v quackos-build:/build -v "$PWD":/work:ro -v "$PWD/out":/out \
    -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
    debian:trixie bash /work/scripts/container-build.sh || status=$?

# host side of the cleanup
"${docker[@]}" image prune -f >/dev/null 2>&1 || true
# a failed build can leave a half-written ISO behind
[ "$status" -eq 0 ] || rm -f out/*.partial
# keep the two newest ISOs (and their checksums)
ls -1t out/quackos-*-amd64.iso 2>/dev/null | tail -n +3 | while read -r old; do
    rm -f "$old" "$old.sha256"
done
if [ "$status" -ne 0 ]; then
    echo "build FAILED (exit $status)" >&2
    exit "$status"
fi
ls -lh out/quackos-*-amd64.iso
