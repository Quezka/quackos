# 🦆 QuackOS

Una distro Linux **fighissima**, fatta da Quezka. Base **Debian 13 "trixie"**, desktop **KDE Plasma 6**,
installer **Calamares**, e dentro tutta la suite di app dell'autore, già installate:

| App | Cos'è |
|---|---|
| **Stagno** | il browser di DuckNet (`duck://`, DUCK/1) |
| **Quire** | appunti, calendario e attività, con sincronizzazione |
| **Ligature** | diagrammi ER e UML con generazione SQL |
| **Gantry** | editor di diagrammi di Gantt (compatibile GanttProject) |
| **Bivouac** | studio per le CTF |
| **Natter** | WhatsApp Web come app |
| **`ducknet`** | server, DNS, relay e host di DuckNet da riga di comando |

Le app si aggiornano da sole (Impostazioni → Cerca aggiornamenti), quindi la ISO non invecchia male.
Per il web normale c'è Firefox ESR: Stagno parla solo DuckNet.

## Com'è fatta

- **Identità**: `os-release` con `ID=quackos`, `ID_LIKE=debian` (i programmi che conoscono Debian la trattano da Debian).
- **Look**: tema scuro Breeze con l'indaco degli altri programmi, sfondo con la papera sullo stagno, splash di avvio
  (Plymouth) e branding di Calamares. Emoji a colori, perché le papere sono emoji.
- **Lingue**: italiano, russo e inglese; la live parte in italiano (`QUACKOS_LOCALE` per cambiarlo).
- **`quack`**: il coltellino svizzero: `quack` (rapporto dello stagno), `quack say`, `quack update`, `quack dns`.
- **Prompt 🦆**: verde se l'ultimo comando è andato bene, rosso se no.

## Costruirla

Serve root, una Debian 13 (anche in container o VM) e circa 15 GB liberi: vedi [docs/building.md](docs/building.md).

```sh
sudo ./build.sh        # produce out/quackos-<versione>-amd64.iso
```

La CI di GitHub la costruisce ad ogni push, la fa avviare in QEMU per verificare che arrivi al login, e pubblica la
ISO sulle release quando si crea un tag `vX.Y.Z`.

## Provarla

Utente live: `quack`, password `live`. Dal desktop: **Installa QuackOS**.

## Documentazione

- [Scelte di progetto e limiti](docs/design.md)
- [Costruire e modificare la ISO](docs/building.md)

## Stato

0.1.0: la ISO si costruisce in CI e **parte in QEMU fino al login** (banner «QuackOS 0.1.0»). Il desktop grafico e
l'installer Calamares non sono ancora stati verificati.
