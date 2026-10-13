#!/usr/bin/env python3
"""Checks that every package in config/package-lists exists in Debian 13 (main, contrib, non-free-firmware).

Needs the internet (downloads the package indexes, ~15 MB). Run it before pushing a change to the lists;
the CI runs it too, so a wrong name fails in a minute instead of after a long image build.
"""
import glob
import lzma
import os
import re
import sys
import urllib.request

SUITE = "trixie"
AREAS = ("main", "contrib", "non-free-firmware")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def debian_packages():
    names = set()
    for area in AREAS:
        url = "https://deb.debian.org/debian/dists/%s/%s/binary-amd64/Packages.xz" % (SUITE, area)
        with urllib.request.urlopen(url, timeout=60) as response:
            text = lzma.decompress(response.read()).decode()
        names |= set(re.findall(r"^Package: (\S+)", text, re.M))
    return names


def wanted():
    for path in sorted(glob.glob(os.path.join(ROOT, "config", "package-lists", "*.list.chroot"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    yield os.path.basename(path), line


def main():
    available = debian_packages()
    missing = [(f, p) for f, p in wanted() if p not in available]
    for f, p in missing:
        print("MISSING in Debian %s: %s (%s)" % (SUITE, p, f), file=sys.stderr)
    if not missing:
        print("all %d package names exist in Debian %s" % (len(list(wanted())), SUITE))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
