#!/usr/bin/env bash
# Publishes an ISO built by scripts/local-build.sh to the home server, which serves it on the LAN (http://quackos.lan/).
#   scripts/publish-iso.sh                       the newest ISO in out/
#   scripts/publish-iso.sh out/quackos-X-amd64.iso
#   QUACKOS_HOST=quackos@192.168.1.14 scripts/publish-iso.sh      when quackos.lan does not resolve
# The server is the LXC `quackos` (Caddy, LAN only; setup in docs/hosting.md). Nothing goes to GitHub: no releases
# until the desktop works. Only the 2 newest ISOs are kept there, like in out/.
set -euo pipefail
cd "$(dirname "$0")/.."

host="${QUACKOS_HOST:-quackos@quackos.lan}"
# the first connection to a new name records the server's key; a CHANGED key is still refused
ssh_opts=(-o StrictHostKeyChecking=accept-new)
export RSYNC_RSH="ssh ${ssh_opts[*]}"
iso="${1:-$(ls -1t out/quackos-*-amd64.iso 2>/dev/null | head -n1)}"
[ -n "$iso" ] && [ -f "$iso" ] || { echo "no ISO to publish: run scripts/local-build.sh first" >&2; exit 1; }
name="$(basename "$iso")"
[ -f "$iso.sha256" ] || { echo "missing $iso.sha256" >&2; exit 1; }

echo "checking the local checksum..."
( cd "$(dirname "$iso")" && sha256sum -c "$name.sha256" )

echo "uploading $name to $host ..."
rsync -ah --partial --info=progress2 "$iso" "$iso.sha256" "$host:/srv/quackos/"

echo "checking the checksum on the server..."
ssh "${ssh_opts[@]}" "$host" "cd /srv/quackos && sha256sum -c '$name.sha256'"

version="${name#quackos-}"; version="${version%-amd64.iso}"
bytes="$(stat -c %s "$iso")"
sha="$(cut -d' ' -f1 "$iso.sha256")"
# latest.json and the stable names; then keep only the 2 newest ISOs (and their checksums)
printf '{"version":"%s","file":"%s","bytes":%s,"sha256":"%s","published_at":"%s"}\n' \
    "$version" "$name" "$bytes" "$sha" "$(date -u +%FT%TZ)" |
    ssh "${ssh_opts[@]}" "$host" "cd /srv/quackos && cat > latest.json.tmp && mv latest.json.tmp latest.json &&
        ln -sfn '$name' quackos-latest-amd64.iso && ln -sfn '$name.sha256' quackos-latest-amd64.iso.sha256 &&
        ls -1t quackos-*-amd64.iso | tail -n +3 | while read -r old; do rm -f \"\$old\" \"\$old.sha256\"; done; ls -lh"

echo "done: http://${host#*@}/$name"
