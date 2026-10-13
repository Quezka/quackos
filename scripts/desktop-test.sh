#!/usr/bin/env bash
# Boots the ISO's live system with a virtual display, takes screenshots, and collects a debug report from the
# serial console. Not a pass/fail test: it exists so a human can LOOK at what the desktop does.
#   scripts/desktop-test.sh out/quackos-X.Y.Z-amd64.iso out/desktop
set -uo pipefail
iso="${1:?usage: desktop-test.sh <iso> <out-dir>}"
out="${2:?usage: desktop-test.sh <iso> <out-dir>}"
mkdir -p "$out"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

xorriso -osirrox on -indev "$iso" -extract /live "$work/live" >/dev/null 2>&1
kernel="$(ls "$work"/live/vmlinuz* | head -n1)"
initrd="$(ls "$work"/live/initrd.img* | head -n1)"
accel=tcg; [ -w /dev/kvm ] && accel=kvm

qemu-system-x86_64 -accel "$accel" -m 4096 -smp 2 -vga virtio -display none -no-reboot \
    -cdrom "$iso" -kernel "$kernel" -initrd "$initrd" \
    -append "boot=live components quiet splash username=quack hostname=quackos locales=it_IT.UTF-8 keyboard-layouts=it console=ttyS0 quackos.debug" \
    -serial "file:$out/serial.log" -qmp "unix:$work/qmp.sock,server,nowait" &
qemu=$!

python3 "$(dirname "$0")/qemu_screenshot.py" "$work/qmp.sock" "$out/screen" 20 60 120 180 240 || true
sleep 5
kill "$qemu" 2>/dev/null || true
wait "$qemu" 2>/dev/null || true
echo "---- debug report from the guest ----"
sed -n '/QUACKOS DEBUG REPORT/,/END OF REPORT/p' "$out/serial.log" | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g' | tr -d '\r' | head -250
