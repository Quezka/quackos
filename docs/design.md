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

## Dimensione

Ogni app della suite porta il proprio Qt (sono PyInstaller): ~55 MB compressi l'una, Stagno 168 MB perché include
Chromium. Insieme a KDE la ISO si avvicina a **2 GiB**, che è il limite dei file delle release di GitHub. Il workflow
**divide** la ISO in parti se serve (si ricompone con `cat`). Se vuoi restare sotto: togliere pacchetti da
`desktop.list.chroot` o le app meno usate dalla lista.

## Cosa NON è verificato (onestà)

- La ISO non è mai stata costruita né avviata dall'autore di questo codice: manca root, spazio e un ambiente Debian 13.
  La CI è il primo vero banco di prova, e probabilmente ci vorranno alcuni giri per sistemare i dettagli.
- Nomi esatti di pacchetti Debian 13 (`policykit-1`, `task-*-kde-desktop`, `calamares-settings-debian`…) e opzioni di
  `lb config` sono scritti dalla documentazione, non provati.
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
