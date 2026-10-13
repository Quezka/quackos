#!/usr/bin/env python3
"""Takes screenshots of a running QEMU through its QMP socket and writes them as PNG (no dependencies).

    qemu_screenshot.py <qmp-socket> <out-prefix> <seconds> [<seconds> ...]

Waits until each given number of seconds since start has passed, then saves <out-prefix>-<seconds>s.png.
"""
import socket
import struct
import sys
import time
import zlib


def ppm_to_png(ppm_path, png_path):
    with open(ppm_path, "rb") as f:
        data = f.read()
    # P6\n<w> <h>\n255\n<bytes>
    parts = data.split(b"\n", 3)
    width, height = (int(x) for x in parts[1].split())
    pixels = parts[3]
    raw = b"".join(b"\x00" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))

    def chunk(tag, body):
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    with open(png_path, "wb") as f:
        f.write(png)


def main():
    sock_path, prefix, *times = sys.argv[1:]
    sock = socket.socket(socket.AF_UNIX)
    for _ in range(60):
        try:
            sock.connect(sock_path)
            break
        except OSError:
            time.sleep(1)
    reader = sock.makefile("rw")
    reader.readline()                                            # greeting
    for command in ({"execute": "qmp_capabilities"},):
        reader.write(__import__("json").dumps(command) + "\n")
        reader.flush()
        reader.readline()
    start = time.time()
    for t in (int(x) for x in times):
        time.sleep(max(0, start + t - time.time()))
        ppm = "%s-%ds.ppm" % (prefix, t)
        reader.write(__import__("json").dumps({"execute": "screendump", "arguments": {"filename": ppm}}) + "\n")
        reader.flush()
        reader.readline()
        time.sleep(1)
        ppm_to_png(ppm, "%s-%ds.png" % (prefix, t))
        print("saved %s-%ds.png" % (prefix, t), flush=True)


if __name__ == "__main__":
    main()
