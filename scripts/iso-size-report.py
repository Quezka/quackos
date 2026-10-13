#!/usr/bin/env python3
"""Estimates how much each config/package-lists/*.list.chroot weighs, from the Debian 13 package indexes.

It adds up the `Size` field (the compressed .deb) of the packages NAMED in each list. That is only an estimate:
- dependencies are NOT counted, so a metapackage such as kde-plasma-desktop shows almost nothing although it
  pulls in hundreds of MB;
- it is the size of the compressed .debs, not of the ISO (the squashfs, the suite .debs and the bootloader are
  not included, and a dependency shared by two lists is not subtracted).
Use it to compare lists and to weigh an addition, not to predict the ISO size.

Needs the internet (downloads the indexes, ~15 MB). Usage: scripts/iso-size-report.py [package ...]
Extra package names given on the command line are weighed too, as a list called "(arguments)".
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


def debian_sizes():
    """{package name: Size in bytes} for every package in the indexes."""
    sizes = {}
    for area in AREAS:
        url = "https://deb.debian.org/debian/dists/%s/%s/binary-amd64/Packages.xz" % (SUITE, area)
        with urllib.request.urlopen(url, timeout=60) as response:
            text = lzma.decompress(response.read()).decode()
        for stanza in text.split("\n\n"):
            name = re.search(r"^Package: (\S+)", stanza, re.M)
            size = re.search(r"^Size: (\d+)", stanza, re.M)
            if name and size:
                sizes.setdefault(name.group(1), int(size.group(1)))
    return sizes


def read_lists():
    """{list file name: [package names]}, in file order, without the comments."""
    lists = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "config", "package-lists", "*.list.chroot"))):
        with open(path, encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        lists[os.path.basename(path)] = names
    return lists


def mb(size):
    return "%.1f MB" % (size / 1_000_000)


def main(argv):
    sizes = debian_sizes()
    lists = read_lists()
    if argv:
        lists["(arguments)"] = list(argv)
    total = 0
    unknown = []
    for name, packages in lists.items():
        known = [(sizes[p], p) for p in packages if p in sizes]
        unknown += [(name, p) for p in packages if p not in sizes]
        subtotal = sum(size for size, _ in known)
        total += subtotal
        print("%-28s %9s  (%d packages)" % (name, mb(subtotal), len(packages)))
        for size, package in sorted(known, reverse=True)[:5]:
            print("    %9s  %s" % (mb(size), package))
    print("%-28s %9s" % ("TOTAL named .debs", mb(total)))
    for name, package in unknown:
        print("not in the %s indexes: %s (%s)" % (SUITE, package, name), file=sys.stderr)
    print("Estimate of the compressed .debs of the named packages only: no dependencies, not the ISO size.")
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
