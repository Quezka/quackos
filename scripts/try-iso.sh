#!/usr/bin/env bash
# Boots a QuackOS ISO in QEMU with the kernel parameters you choose (no need to edit the boot menu), and gives a
# serial console in this terminal (log in as quack / live) next to the graphical window.
#   scripts/try-iso.sh out/quackos-0.2.0-dev1-amd64.iso quackos.session=quackos
# Needs: apt install qemu-system-x86 (and your user able to open /dev/kvm).
set -euo pipefail
iso="${1:?usage: try-iso.sh ISO [kernel parameters...]}"; shift || true
command -v qemu-system-x86_64 >/dev/null || { echo "qemu is missing: apt install qemu-system-x86" >&2; exit 1; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
xorriso -osirrox on -indev "$iso" -extract /live/vmlinuz "$tmp/vmlinuz" -extract /live/initrd.img "$tmp/initrd.img" >/dev/null 2>&1
kvm=(); [ -w /dev/kvm ] && kvm=(-enable-kvm -cpu host)
exec qemu-system-x86_64 "${kvm[@]}" -m "${QEMU_MEM:-4096}" -smp 2 \
    -cdrom "$iso" -kernel "$tmp/vmlinuz" -initrd "$tmp/initrd.img" \
    -append "boot=live components username=quack hostname=quackos console=ttyS0 $*" \
    -device virtio-vga -display gtk -serial mon:stdio
