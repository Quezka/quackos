"""server/quackos-pull.sh against a fake GitHub (local HTTP server): single file, split parts, bad checksum, repeat, prune."""
import hashlib
import http.server
import json
import os
import subprocess
import tempfile
import threading
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPT = os.path.join(ROOT, "server", "quackos-pull.sh")


class FakeGitHub:
    """Serves /repos/Quezka/quackos/releases/latest and the asset files from memory."""

    def __init__(self):
        self.files, self.tag, self.sha_override = {}, "v1.0.0", None
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                if self.path == "/repos/Quezka/quackos/releases/latest":
                    base = "http://127.0.0.1:%d/dl/" % outer.port
                    body = json.dumps({"tag_name": outer.tag, "assets": [
                        {"name": n, "browser_download_url": base + n} for n in outer.files]}).encode()
                elif self.path.startswith("/dl/") and self.path[4:] in outer.files:
                    body = outer.files[self.path[4:]]
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def release(self, version, content, parts=1, sha=None):
        iso = "quackos-%s-amd64.iso" % version
        self.tag = "v" + version
        self.files = {}
        if parts == 1:
            self.files[iso] = content
        else:
            size = -(-len(content) // parts)
            for i in range(parts):
                self.files["%s.part%02d" % (iso, i)] = content[i * size:(i + 1) * size]
        digest = sha or hashlib.sha256(content).hexdigest()
        self.files[iso + ".sha256"] = ("%s  %s\n" % (digest, iso)).encode()

    def close(self):
        self.server.shutdown()


class PullTest(unittest.TestCase):
    def setUp(self):
        self.gh = FakeGitHub()
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = os.path.join(self.tmp.name, "srv")

    def tearDown(self):
        self.gh.close()
        self.tmp.cleanup()

    def pull(self, keep=2):
        env = dict(os.environ, QUACKOS_API="http://127.0.0.1:%d" % self.gh.port, QUACKOS_DEST=self.dest, QUACKOS_KEEP=str(keep))
        return subprocess.run(["bash", SCRIPT], env=env, capture_output=True, text=True)

    def listing(self):
        return sorted(n for n in os.listdir(self.dest) if not n.startswith("."))

    def test_single_file(self):
        data = os.urandom(300_000)
        self.gh.release("1.0.0", data)
        r = self.pull()
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.dest, "quackos-1.0.0-amd64.iso"), "rb") as f:
            self.assertEqual(f.read(), data)
        info = json.load(open(os.path.join(self.dest, "latest.json")))
        self.assertEqual((info["version"], info["bytes"], info["sha256"]), ("1.0.0", len(data), hashlib.sha256(data).hexdigest()))
        self.assertEqual(os.readlink(os.path.join(self.dest, "quackos-latest-amd64.iso")), "quackos-1.0.0-amd64.iso")

    def test_split_parts_are_joined_in_order(self):
        data = os.urandom(500_001)
        self.gh.release("1.0.0", data, parts=3)
        r = self.pull()
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.dest, "quackos-1.0.0-amd64.iso"), "rb") as f:
            self.assertEqual(f.read(), data)

    def test_a_wrong_checksum_publishes_nothing_and_leaves_no_leftovers(self):
        self.gh.release("1.0.0", os.urandom(1000), sha="0" * 64)
        r = self.pull()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("mismatch", r.stderr)
        self.assertEqual(self.listing(), [])
        self.assertEqual([n for n in os.listdir(self.dest) if n.startswith(".incoming")], [])

    def test_a_bad_checksum_does_not_replace_the_good_previous_version(self):
        good = os.urandom(1000)
        self.gh.release("1.0.0", good)
        self.assertEqual(self.pull().returncode, 0)
        self.gh.release("1.1.0", os.urandom(1000), sha="f" * 64)
        self.assertNotEqual(self.pull().returncode, 0)
        self.assertEqual(os.readlink(os.path.join(self.dest, "quackos-latest-amd64.iso")), "quackos-1.0.0-amd64.iso")

    def test_second_run_does_not_download_again(self):
        self.gh.release("1.0.0", os.urandom(1000))
        self.assertEqual(self.pull().returncode, 0)
        self.gh.files = {k: v for k, v in self.gh.files.items() if k.endswith(".sha256")}   # the ISO is gone from the server
        r = self.pull()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("already have", r.stdout)

    def test_only_the_newest_versions_are_kept(self):
        for v in ("1.0.0", "1.1.0", "1.2.0", "1.10.0"):
            self.gh.release(v, os.urandom(500))
            self.assertEqual(self.pull(keep=2).returncode, 0)
        isos = [n for n in self.listing() if n.endswith(".iso") and "latest" not in n]
        self.assertEqual(isos, ["quackos-1.10.0-amd64.iso", "quackos-1.2.0-amd64.iso"])       # version sort, not text sort

    def test_a_weird_tag_is_refused(self):
        self.gh.release("1.0.0", os.urandom(100))
        self.gh.tag = "v1.0.0; rm -rf /"
        r = self.pull()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unexpected tag", r.stderr)

    def test_a_non_checksum_file_is_refused(self):
        self.gh.release("1.0.0", os.urandom(100))
        self.gh.files["quackos-1.0.0-amd64.iso.sha256"] = b"<html>not a checksum</html>\n"
        r = self.pull()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.listing(), [])

    def test_units_match_the_script(self):
        service = open(os.path.join(ROOT, "server", "quackos-pull.service")).read()
        self.assertIn("ExecStart=/usr/local/bin/quackos-pull", service)
        self.assertIn("NoNewPrivileges=true", service)
        self.assertIn("ReadWritePaths=/srv/quackos", service)
        timer = open(os.path.join(ROOT, "server", "quackos-pull.timer")).read()
        self.assertIn("Persistent=true", timer)


if __name__ == "__main__":
    unittest.main()
