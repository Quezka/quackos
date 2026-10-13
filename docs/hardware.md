# Hardware coverage

Sizes are the `Size` field (compressed .deb) of the Debian 13 "trixie" indexes; the ISO grows by about that much.
ISO ~2.07 GB, GitHub limit 2.147 GB. Everything below was read from the package indexes and package file lists;
nothing was run on real hardware.

## Matrix: what the image has

| Area | In the image | Size | Missing / limit |
|---|---|---|---|
| Intel GPU | Mesa (iris/anv) via libgl1-mesa-dri, mesa-vulkan-drivers; `firmware-intel-graphics` (i915 DMC/GuC/HuC) | 6.4 MB | Recent Xe laptops: firmware is in the same package. |
| Intel video decode | `intel-media-va-driver` (Gen8+) | 3.4 MB | Pre-Broadwell needs `i965-va-driver` (315 KB), not added. |
| AMD GPU | `firmware-amd-graphics` (amdgpu + radeon), via `firmware-linux` | 15.1 MB | Nothing. |
| NVIDIA GPU | nouveau (kernel + Mesa), **no firmware** | 0 | Maxwell and newer need signed firmware for acceleration: `firmware-nvidia-graphics` 39.5 MB (Maxwell..Ada) and, for Turing+ with the GSP, `firmware-nvidia-gsp` 37.2 MB. Without them: modesetting works, rendering is software. Proprietary `nvidia-driver` is in *non-free*, which the image does not enable: cannot ship. |
| Wi-Fi Intel | `firmware-iwlwifi` (also Intel Bluetooth `ibt-*`) | 16.7 MB | |
| Wi-Fi/BT Realtek | `firmware-realtek` (rtw87/88/89, rtlwifi, rtl_bt, rtl_nic) | 2.9 MB | |
| Wi-Fi/BT Atheros/Qualcomm | `firmware-atheros` (ath6k/10k/11k, qca BT) | 29.5 MB | ath12k (Wi-Fi 7) not checked. |
| Wi-Fi Broadcom | `firmware-brcm80211` (brcmfmac, cypress) added in 0.1.1 | 5.4 MB | Old BCM43xx needing `broadcom-sta-dkms` (non-free) or `b43`: not shipped. |
| Wi-Fi/BT MediaTek | none | 19.6 MB (`firmware-mediatek`) | MT7921/MT7922 are in many 2022+ AMD laptops: **biggest remaining gap**, see budget. |
| Misc firmware | `firmware-linux` = `-free`, `firmware-misc-nonfree` (4.3 MB), amd-graphics | | |
| Microcode | `intel-microcode` 12.8 MB, `amd64-microcode` 0.28 MB | | |
| Audio | PipeWire + WirePlumber; `firmware-sof-signed` + `alsa-ucm-conf` added in 0.1.1 | 1.4 MB + 92 KB | Skylake and older Intel use plain HDA, no firmware. |
| Touchpad/TrackPoint/keyboard | libinput (KWin, `xserver-xorg-input-libinput`) | | |
| Brightness/volume keys, battery | powerdevil, plasma-pa, `upower` (Depends of kde-plasma-desktop), `power-profiles-daemon` | 56 KB | |
| Bluetooth | bluez, bluedevil, libspa-0.2-bluetooth (via pipewire-audio) | | Adapter firmware ships in the Wi-Fi packages above. |
| Fingerprint | none | fprintd 126 KB + libfprint-2-2 297 KB + libpam-fprintd 16 KB | 0.1.2: `libpam-fprintd` changes the login PAM stack, untestable without a reader. |
| HiDPI | nothing to install; Plasma scales per screen | | Fractional scaling default: not verified. |
| Sensors (2-in-1) | `iio-sensor-proxy` added in 0.1.1 | 36 KB | |
| VM: QEMU/KVM | `qemu-guest-agent` 0.56 MB, `spice-vdagent` 61 KB | | virtio-gpu/virtio-net are kernel drivers. |
| VM: VMware | `open-vm-tools` 0.70 MB | | `open-vm-tools-desktop` 157 KB + gtkmm/atkmm/cairomm/glibmm libs for clipboard/resize: 0.1.2. |
| VM: VirtualBox | kernel modules only (vboxguest/vboxsf/vboxvideo, believed in-tree, not checked) | | `virtualbox-guest-utils` / `-x11` are **not in trixie** (not found in main, contrib or non-free): no auto-resize or shared clipboard from VBoxClient. |
| VM: Hyper-V | kernel `hv_*` drivers | | `hyperv-daemons` 1.38 MB: 0.1.2. |

## 0.1.1 subset (budget 25 MB): about 8.5 MB
| Package | Size | Why |
|---|---|---|
| firmware-brcm80211 | 5.4 MB | Broadcom Wi-Fi in many Dell/Apple laptops |
| firmware-sof-signed | 1.4 MB | no audio on Tiger Lake+ Intel laptops without it |
| alsa-ucm-conf | 92 KB | routing profiles SOF needs |
| open-vm-tools | 0.70 MB | VMware guests |
| qemu-guest-agent | 0.56 MB | QEMU/KVM/Proxmox guests |
| spice-vdagent | 61 KB | clipboard and auto-resize in SPICE |
| iio-sensor-proxy | 36 KB | 2-in-1 rotation |

If the budget allows, `firmware-mediatek` (19.6 MB) would bring the total to about 28 MB: your call.

## 0.1.2
| Package | Size | Why |
|---|---|---|
| firmware-mediatek | 19.6 MB | MT7921/22 Wi-Fi and BT in recent AMD laptops |
| firmware-nvidia-graphics | 39.5 MB | nouveau acceleration on Maxwell..Ada (e.g. a GTX 1050 Ti is Pascal); needs an ISO split or a size cut elsewhere |
| firmware-nvidia-gsp | 37.2 MB | Turing+ GSP; same issue |
| open-vm-tools-desktop | 157 KB + libs | VMware clipboard/resize |
| hyperv-daemons | 1.38 MB | Hyper-V guests |
| fprintd, libfprint-2-2, libpam-fprintd | 0.44 MB | fingerprint readers |
| firmware-libertas | 3.6 MB | old Marvell Wi-Fi |
| firmware-ti-connectivity | 1.5 MB | TI Wi-Fi/BT, rare |
| i965-va-driver | 315 KB | pre-Broadwell Intel video decode |
| thermald | 246 KB | Intel thermal management, only if laptops overheat |

## Cannot be verified without hardware
Whether each card actually associates, which audio driver the 6.12 kernel picks per laptop (HDA/SOF/AVS),
suspend/resume, fingerprint readers, HiDPI behaviour, VirtualBox in-tree guest modules, NVIDIA behaviour with and
without firmware, and the real ISO growth (indexes give compressed sizes, shared dependencies are not subtracted).
