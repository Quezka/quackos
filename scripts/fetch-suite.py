#!/usr/bin/env python3
"""Downloads the Quezka app suite (.deb files) into config/packages.chroot/ for live-build to install.

Reads suite/apps.list, asks the GitHub API for each repo's latest release, picks the asset matching the regex
and VERIFIES it against the SHA-256 GitHub publishes for it. Anything missing or mismatching is an error:
QuackOS never installs an unverified download. Set GITHUB_TOKEN to avoid API rate limits.
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "config", "packages.chroot")
VERSIONS = os.path.join(ROOT, "config", "includes.chroot_after_packages", "usr", "share", "quackos", "suite-versions.txt")


class SuiteError(Exception):
    pass


def parse_manifest(text):
    apps = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, repo, pattern = line.split(None, 2)
        apps.append((name, repo, re.compile(pattern.strip())))
    return apps


def pick_asset(release, pattern):
    """The release asset matching `pattern`, with a checksum, or SuiteError."""
    for asset in release.get("assets", []):
        if pattern.search(asset["name"]):
            digest = (asset.get("digest") or "").removeprefix("sha256:")
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise SuiteError("GitHub gave no SHA-256 for %s: refusing to install it unverified" % asset["name"])
            return asset["name"], asset["browser_download_url"], digest
    raise SuiteError("no asset matching %s in release %s" % (pattern.pattern, release.get("tag_name")))


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def request(url, accept=None):
    headers = {"User-Agent": "quackos-build"}
    if accept:
        headers["Accept"] = accept
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = "Bearer " + token
    return urllib.request.Request(url, headers=headers)


def main():
    with open(os.path.join(ROOT, "suite", "apps.list"), encoding="utf-8") as f:
        apps = parse_manifest(f.read())
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.endswith(".deb"):
            os.remove(os.path.join(OUT, old))
    versions = []
    for name, repo, pattern in apps:
        print("== %s (%s)" % (name, repo), flush=True)
        with urllib.request.urlopen(request("https://api.github.com/repos/%s/releases/latest" % repo,
                                            "application/vnd.github+json"), timeout=60) as r:
            release = json.load(r)
        filename, url, digest = pick_asset(release, pattern)
        target = os.path.join(OUT, os.path.basename(filename))
        with urllib.request.urlopen(request(url), timeout=600) as r, open(target, "wb") as out:
            while chunk := r.read(1 << 20):
                out.write(chunk)
        if sha256_of(target) != digest:
            os.remove(target)
            raise SuiteError("%s does not match the SHA-256 GitHub published: refusing to use it" % filename)
        print("   %s ok (%s)" % (filename, release["tag_name"]))
        versions.append("%s %s" % (name, release["tag_name"]))
    os.makedirs(os.path.dirname(VERSIONS), exist_ok=True)
    with open(VERSIONS, "w", encoding="utf-8") as f:
        f.write("\n".join(versions) + "\n")


if __name__ == "__main__":
    try:
        main()
    except SuiteError as e:
        sys.exit("fetch-suite: %s" % e)
