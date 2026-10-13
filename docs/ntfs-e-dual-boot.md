# NTFS and dual boot

What is verified (read from the Debian 13 packages) and what is not.

## Verified from package files
- `udisks2` ships no NTFS defaults in `/etc`; its example config lists `ntfs_drivers=ntfs3,ntfs` and
  tries the drivers in order, so a refusal by the first driver falls back to the next.
- `ntfs-3g` provides `/usr/sbin/mount.ntfs` and the setuid `/usr/bin/ntfs-3g`; `ntfs3` needs no package.
- `calamares` and `calamares-settings-debian` ship no `partition.conf`, so Calamares uses its
  built-in defaults and the user picks erase / alongside / manual in the partition page.
- `os-prober` only mounts partitions read-only-by-intent through `grub-mount` to look for systems.

## What QuackOS sets
`/etc/udisks2/mount_options.conf`: NTFS goes through ntfs-3g only (`ntfs_drivers=ntfs`), with
`windows_names`. Needs `ntfs-3g` in `config/package-lists/base.list.chroot`.

## Not verified (needs real hardware)
- ntfs-3g refusing a Fast Startup volume: known ntfs-3g behaviour, not run here.
- Whether the KDE Device Notifier mounts internal disks only on click (believed, not run).
- Calamares' behaviour with Windows on the same disk, and GRUB's os-prober entry for Windows.
