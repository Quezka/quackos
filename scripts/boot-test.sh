#!/usr/bin/env bash
# Boots the built ISO's kernel in QEMU to a text login and checks it says QuackOS. A smoke test: it proves
# the image boots, live-boot finds the squashfs, and the identity files are in place. Usage:
#   scripts/boot-test.sh out/quackos-X.Y.Z-amd64.iso
set -euo pipefail
iso="${1:?usage: boot-test.sh <iso>}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

xorriso -osirrox on -indev "$iso" -extract /live "$work/live" >/dev/null 2>&1
kernel="$(ls "$work"/live/vmlinuz* | head -n1)"
initrd="$(ls "$work"/live/initrd.img* | head -n1)"

accel=tcg
[ -w /dev/kvm ] && accel=kvm
echo "booting with $accel"

log="$work/serial.log"
timeout 480 qemu-system-x86_64 -accel "$accel" -m 3072 -smp 2 -display none -no-reboot \
    -cdrom "$iso" -kernel "$kernel" -initrd "$initrd" \
    -append "boot=live components username=quack hostname=quackos console=ttyS0 quackos.debug quackos.debug_delay=25 systemd.unit=multi-user.target" \
    -serial "file:$log" &
qemu=$!

# The image prints a debug report (quackos.debug) about 25 s after boot: wait for it, it tells us whether
# the live user was really created. A login banner alone proved nothing (it was there while `quack` was missing).
ok=0
for _ in $(seq 1 90); do
    sleep 5
    if grep -q "END OF REPORT" "$log" 2>/dev/null; then ok=1; break; fi
    kill -0 "$qemu" 2>/dev/null || break
done
kill "$qemu" 2>/dev/null || true

# keep the whole serial console as a file the workflow uploads: when a boot hangs it is the only evidence
cp "$log" "${BOOT_LOG_OUT:-boot-serial.log}" 2>/dev/null || true
echo "---- last 120 lines of the console ----"
sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' "$log" | tr -d '\r' | grep -v '^$' | tail -n 120 || true
if [ "$ok" -ne 1 ]; then echo "FAIL: the system never printed its debug report (did not finish booting)" >&2; exit 1; fi
grep -q "login:" "$log" || { echo "FAIL: no login prompt" >&2; exit 1; }
grep -q "QuackOS" "$log" || { echo "FAIL: the login banner does not say QuackOS" >&2; exit 1; }
grep -q "uid=1000(quack)" "$log" || { echo "FAIL: the live user 'quack' was not created, so nobody could log in" >&2; exit 1; }
grep -q "MISSING:" "$log" && { echo "FAIL: tools the installer needs are missing:" >&2; grep "MISSING:" "$log" >&2; exit 1; }
grep -q "^Session=plasmax11.desktop" "$log" || { echo "FAIL: the live autologin is not set to the X11 Plasma session" >&2; exit 1; }
grep -q "^User=quack" "$log" || { echo "FAIL: autologin is not set for quack" >&2; exit 1; }
grep -q "^quack:" "$log" || { echo "FAIL: no passwd entry for quack" >&2; exit 1; }
echo "OK: booted to a QuackOS login prompt and the live user 'quack' exists"
