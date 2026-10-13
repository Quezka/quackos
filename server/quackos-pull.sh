#!/usr/bin/env bash
# Mirrors the latest QuackOS release ISO from GitHub into a local folder. The SERVER pulls: nothing listens, no
# inbound port, no runner, no secret (the repo is public, so release files need no token).
#
#   QUACKOS_DEST   where to keep the files            (default /srv/quackos)
#   QUACKOS_KEEP   how many versions to keep          (default 2)
#   QUACKOS_REPO   GitHub repo                        (default Quezka/quackos)
#   QUACKOS_API    GitHub API base (tests only)       (default https://api.github.com)
#   GITHUB_TOKEN   optional: only to lift the 60 requests/hour API limit
#
# It downloads <iso> (or <iso>.part00, .part01, ... and joins them while streaming, so it never needs room for two
# copies), checks the SHA-256 published in the release, and only then makes the file visible. A bad or partial
# download is deleted and the old files stay as they were.
set -euo pipefail
umask 022

REPO="${QUACKOS_REPO:-Quezka/quackos}"
DEST="${QUACKOS_DEST:-/srv/quackos}"
KEEP="${QUACKOS_KEEP:-2}"
API="${QUACKOS_API:-https://api.github.com}"

die() { echo "quackos-pull: $*" >&2; exit 1; }
for tool in curl jq flock sha256sum; do command -v "$tool" >/dev/null || die "missing tool: $tool"; done
[[ "$KEEP" =~ ^[1-9][0-9]*$ ]] || die "QUACKOS_KEEP must be a positive number"

mkdir -p "$DEST"
exec 9>"$DEST/.lock"
flock -n 9 || { echo "quackos-pull: another run is in progress"; exit 0; }

auth=()
[ -n "${GITHUB_TOKEN:-}" ] && auth=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
release="$(curl -fsSL -H 'Accept: application/vnd.github+json' "${auth[@]}" "$API/repos/$REPO/releases/latest")" \
    || die "could not read the latest release of $REPO"

tag="$(jq -r '.tag_name // empty' <<<"$release")"
[[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "unexpected tag '$tag'"
version="${tag#v}"
iso="quackos-${version}-amd64.iso"

if [ -f "$DEST/$iso" ] && [ -f "$DEST/$iso.sha256" ]; then
    echo "quackos-pull: already have $iso"
else
    sha_url="$(jq -r --arg n "$iso.sha256" '.assets[] | select(.name == $n) | .browser_download_url' <<<"$release")"
    [ -n "$sha_url" ] || die "the release has no $iso.sha256"
    expected="$(curl -fsSL "$sha_url" | awk '{print $1}')"
    [[ "$expected" =~ ^[0-9a-f]{64}$ ]] || die "the published checksum is not a SHA-256"

    mapfile -t urls < <(jq -r --arg n "$iso" '[.assets[] | select(.name == $n or (.name | startswith($n + ".part")))]
                                            | sort_by(.name) | .[].browser_download_url' <<<"$release")
    [ "${#urls[@]}" -gt 0 ] || die "the release has no $iso"

    tmp="$DEST/.incoming-$version"
    done_ok=0
    trap '[ "$done_ok" = 1 ] || rm -f "$tmp" "$tmp.sum"' EXIT
    echo "quackos-pull: downloading $iso (${#urls[@]} file(s))"
    { for u in "${urls[@]}"; do curl -fsSL "$u"; done; } | tee "$tmp" | sha256sum | awk '{print $1}' > "$tmp.sum"
    actual="$(cat "$tmp.sum")"
    [ "$actual" = "$expected" ] || die "SHA-256 mismatch (expected $expected, got $actual): nothing was published"
    mv "$tmp" "$DEST/$iso"
    printf '%s  %s\n' "$expected" "$iso" > "$DEST/$iso.sha256"
    rm -f "$tmp.sum"
    done_ok=1
    echo "quackos-pull: OK $iso $(stat -c %s "$DEST/$iso") bytes, sha256 $expected"
fi

# stable names for the download page, and a small JSON for scripts/pages
ln -sfn "$iso" "$DEST/quackos-latest-amd64.iso"
ln -sfn "$iso.sha256" "$DEST/quackos-latest-amd64.iso.sha256"
jq -n --arg v "$version" --arg f "$iso" --argjson b "$(stat -c %s "$DEST/$iso")" \
      --arg s "$(awk '{print $1}' "$DEST/$iso.sha256")" --arg t "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '{version: $v, file: $f, bytes: $b, sha256: $s, mirrored_at: $t}' > "$DEST/latest.json.tmp"
mv "$DEST/latest.json.tmp" "$DEST/latest.json"

# keep only the newest $KEEP versions
mapfile -t old < <(cd "$DEST" && ls -1 quackos-[0-9]*-amd64.iso 2>/dev/null | sort -V | head -n -"$KEEP")
for f in "${old[@]}"; do
    [ -n "$f" ] || continue
    echo "quackos-pull: removing old $f"
    rm -f "$DEST/$f" "$DEST/$f.sha256"
done
