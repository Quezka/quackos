# Costruire la ISO

## In locale (Debian 13, o un container)

```sh
sudo apt install live-build debootstrap squashfs-tools xorriso curl jq git
sudo ./build.sh            # lascia l'immagine in out/
sudo ./build.sh --clean    # prima cancella i residui di una build precedente
```

Servono circa **15 GB liberi** e una buona mezz'ora (la prima volta scarica tutto da Debian e da GitHub).
Il risultato è `out/quackos-<versione>-amd64.iso` più il suo `.sha256`.

Su Ubuntu o altre distro non costruirla direttamente: le versioni di `live-build` sono diverse. Usa un container:

```sh
docker run --rm -it --privileged -v "$PWD":/work -w /work debian:trixie bash
# dentro: apt update && apt install -y live-build debootstrap squashfs-tools xorriso curl jq git && ./build.sh
```

## In locale, con un container (Ubuntu e altre distro)

```sh
sudo apt install docker.io qemu-system-x86
scripts/local-build.sh                       # ISO in out/ (gzip: per le prove; QUACKOS_COMPRESSION=xz per una release)
scripts/try-iso.sh out/quackos-*-amd64.iso quackos.session=quackos
```

`local-build.sh` usa un volume docker (`quackos-build`) che ricorda i pacchetti scaricati: la seconda build è molto più
veloce. `try-iso.sh` avvia la ISO in QEMU con i parametri di avvio che scegli e una console seriale nel terminale
(utente `quack`, password `live`). Parametri utili: `quackos.session=quackos` (il nuovo desktop), `quackos.session=plasmax11`,
`quackos.wayland`, `noautologin` (mostra il login con il menu delle sessioni).

## Con la CI (consigliato)

`.github/workflows/build.yml` fa tutto: test statici, build in `debian:trixie`, avvio in QEMU, caricamento della ISO
come artefatto (7 giorni). Con un tag `vX.Y.Z` uguale al file `VERSION`, la pubblica sulle release.

## Provarla

```sh
qemu-system-x86_64 -enable-kvm -m 4096 -smp 2 -cdrom out/quackos-0.1.0-amd64.iso -boot d
```

Oppure su chiavetta: `sudo dd if=quackos-….iso of=/dev/sdX bs=4M status=progress conv=fsync`
(controlla bene `/dev/sdX`: `dd` cancella senza chiedere).

## Modificare

- Pacchetti: righe in `config/package-lists/*.list.chroot`.
- App della suite: `suite/apps.list`.
- Grafica: gli SVG in `config/includes.chroot_after_packages/usr/share/quackos/branding/`.
- Lingua/tastiera/fuso della live: variabili `QUACKOS_LOCALE`, `QUACKOS_KEYMAP`, `QUACKOS_TIMEZONE` prima di `lb config`.
- Nuova versione: cambia `VERSION`, aggiungi il testo al `CHANGELOG.md`, tag `vX.Y.Z`.

## Test

`python3 -m unittest discover -s tests`: controlli statici (script, liste di pacchetti, manifest della suite,
grafica, branding, comando `quack`). Non servono root né la ISO.
