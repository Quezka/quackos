# Scelte di progetto

## Perché Debian + KDE + live-build + Calamares

- **Debian 13 stabile**: aggiornamenti di sicurezza veri, `apt` e pacchetti ovunque, e le app della suite
  (Qt/PySide6 impacchettate con PyInstaller) girano su Debian e Ubuntu senza problemi.
- **KDE Plasma 6**: il più personalizzabile, ed è Qt come Stagno, Quire e le altre.
- **live-build**: lo strumento ufficiale di Debian per le ISO live; tutta l'immagine è un albero di file
  (`config/`) che sta bene in git. Niente immagini binarie a mano.
- **Calamares**: l'installer grafico usato da tante distro, con il pacchetto `calamares-settings-debian` per
  partizioni, utenti e bootloader.

## Cosa c'è dentro `config/`

| Percorso | Cosa fa |
|---|---|
| `auto/config` | opzioni di live-build: base, bootloader, nome ISO, parametri di avvio |
| `config/package-lists/` | i pacchetti (base, desktop, installer, live) |
| `config/hooks/live/0100…0900` | identità, grafica, **suite**, Calamares, pulizia finale (in ordine) |
| `config/includes.chroot_after_packages/` | file copiati nell'immagine: `os-release`, prompt, `quack`, tema, Plymouth, branding |
| `suite/apps.list` | le app da scaricare dalle release di GitHub (nome, repo, regex del .deb) |

`VERSION` e `suite/apps.list` sono le uniche fonti: `auto/config` li copia nell'albero all'avvio della build.

## La suite

L'hook `0400-quackos-suite` legge `suite/apps.list`, interroga le release di GitHub, scarica ogni `.deb` e
**controlla il SHA-256 pubblicato da GitHub**: se manca o non coincide la build si ferma. Poi installa tutto in una
sola transazione `apt` (le dipendenze condivise si risolvono insieme).

Per aggiungere un'app: una riga in `suite/apps.list`. Il `.deb` deve chiamarsi come previsto dalla regex.
Fuori per ora: Cairn, Bastion e Marginalia (server o progetti locali senza release installabile).

## Lezioni (cose che sono andate storte davvero)

- **La build usa `--apt-recommends false`**, per tenere piccola la ISO. Ma molti pacchetti hanno come *Recommends* cose
  indispensabili: `live-config` → `user-setup` (senza, l'utente live non esiste: «password errata»), `xserver-xorg-core` →
  Mesa, `kde-plasma-desktop` → `kwin-wayland`/`kwin-x11`, `sddm` → `libpam-systemd`, `calamares` → `squashfs-tools`,
  `network-manager` → `wpasupplicant`. Ognuno è elencato a mano, e `tests/test_quackos.py` impedisce di toglierli.
- **Un banner di login non prova che si possa entrare**: il test di avvio ora controlla anche che l'utente `quack` esista,
  che l'autologin sia impostato e che gli strumenti dell'installer ci siano.
- **Wayland o X11**: `live-config` sceglie la sessione `plasma.desktop`, che in Plasma 6 è Wayland. La live usa X11 (più
  compatibile con hardware vecchio); `quackos.wayland` sulla riga di avvio riporta Wayland.
- **L'installer**: Debian ha già `calamares-install-debian` (sudo + xhost + pkexec) e un'icona automatica «Install Debian»;
  noi sostituiamo il suo `.desktop`. Non mettere cartelle `lib/`, `bin/`, `sbin/` nell'albero dei file: in Debian 13 sono
  link simbolici verso `/usr` e li romperebbero.

## Dimensione

Ogni app della suite porta il proprio Qt (sono PyInstaller): ~55 MB compressi l'una, Stagno 168 MB perché include
Chromium. Insieme a KDE la ISO si avvicina a **2 GiB**, che è il limite dei file delle release di GitHub. Il workflow
**divide** la ISO in parti se serve (si ricompone con `cat`). Se vuoi restare sotto: togliere pacchetti da
`desktop.list.chroot` o le app meno usate dalla lista.

## Cosa è verificato

In CI (13 ottobre 2026): la ISO si costruisce in un container Debian 13 (circa 15 minuti, filesystem 1,78 GB, ISO 1,9 GiB), la suite arriva dalle release con checksum verificato, e l'immagine **parte in QEMU fino al login testuale** con il banner «QuackOS 0.1.0».

La CI **non avvia più la ISO** (scelta dell'autore: si prova direttamente sull'hardware). Dopo la build, `scripts/image-check.py`
apre la ISO senza avviarla e controlla che dentro ci siano i file che ci sono mancati (utente live, sessione X11, installer,
sfondo, driver Mesa, le app). In una prova precedente in QEMU (non più nella CI) il desktop partiva con l'accesso automatico
e la barra con le app fissate.

## Cosa NON è verificato (onestà)

- Il **desktop grafico** (SDDM, KDE, sfondo, splash Plymouth), **Calamares** che installa davvero e le app che si aprono
  dentro la distro: il test di avvio si ferma al login testuale.
- Lo sfondo di default di Plasma ("Next") viene sostituito sovrascrivendo i suoi file (`0200-quackos-artwork`): se
  Plasma cambia nome o struttura, resta lo sfondo originale e non si rompe nulla.
- Il test di avvio in QEMU controlla solo il login testuale; non guarda il desktop grafico.
- Secure Boot: l'ISO usa `shim-signed` di Debian, quindi dovrebbe avviarsi, ma non è provato.

## Idee per dopo

- Un repository apt di QuackOS (le app aggiornate con `apt upgrade` invece che col loro aggiornamento interno).
- Un'app di benvenuto al primo avvio, con la scelta del tema e il collegamento a DuckNet.
- Pannello di Plasma con le app della suite già fissate.
- DNS di sistema che risolve `.duck` tramite `dns.quezka.uk` (solo quel dominio; gli altri col DNS normale).
- Immagine ARM per Raspberry Pi.
