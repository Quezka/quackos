# 🦆 QuackOS — guida utente

Questa guida dice solo cose verificate. Dove una cosa **non è stata provata** c'è scritto «non verificato».

**Stato (v0.1.0):** la ISO si avvia fino alla schermata di login in una macchina virtuale (test automatico in CI).
Il desktop grafico, l'installazione con Calamares, Secure Boot e l'avvio da una chiavetta su un PC vero **non sono
ancora verificati**: se qualcosa non va, è colpa nostra, non tua. Vedi [Segnalare i bug](#segnalare-i-bug).

## 1. Scaricare e controllare la ISO

Dalla pagina delle release: <https://github.com/Quezka/quackos/releases>.

- Scarica `quackos-<versione>-amd64.iso` e il file `.sha256`.
- Se la ISO è spezzata in parti (`.part00`, `.part01`… per il limite di 2 GiB di GitHub), scaricale tutte e riuniscile:
  `cat quackos-<versione>-amd64.iso.part* > quackos-<versione>-amd64.iso`
- Controlla l'integrità: `sha256sum -c quackos-<versione>-amd64.iso.sha256` (nella stessa cartella). Deve dire `OK`.

## 2. Scriverla su una chiavetta

⚠️ **Scrivere la ISO cancella tutto quello che c'è sulla chiavetta.** Controlla bene quale dispositivo scegli.
La ISO è ibrida (`iso-hybrid`): va scritta *così com'è*, come immagine di disco, non copiata come file.

### Linux

- **KDE ISO Image Writer** (se c'è il pacchetto `isoimagewriter`): scegli la ISO e la chiavetta.
- **`dd`** (da terminale; sostituisci `/dev/sdX` con la chiavetta, **il disco intero, senza numero**):

  ```sh
  lsblk                                   # trova la chiavetta, es. /dev/sdb
  sudo dd if=quackos-<versione>-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync
  sync
  ```

  Sbagliare `of=` può cancellare il disco di sistema.
- **balenaEtcher**: scegli la ISO, la chiavetta, «Flash».

### Windows

- **Rufus**: seleziona la ISO; se chiede la modalità, scegli **«Immagine DD»** (non «Immagine ISO»).
- **balenaEtcher**: come sopra.

### macOS

- **balenaEtcher**, oppure da terminale `diskutil list`, poi `diskutil unmountDisk /dev/diskN` e
  `sudo dd if=quackos-<versione>-amd64.iso of=/dev/rdiskN bs=4m`.

Quale di questi strumenti funzioni bene con la ISO di QuackOS **non è verificato** (non è stata provata su nessuna
chiavetta reale): se ne trovi uno che non va, dillo nelle issue.

## 3. Avviare dalla chiavetta

1. Spegni il PC, inserisci la chiavetta, accendi.
2. Subito dopo l'accensione premi il tasto del menu di avvio, che dipende dal produttore: spesso `F12`, `F10`,
   `F9`, `Esc` o `F8`. In alternativa entra nel BIOS/UEFI (`Canc`, `F2`, `F1`…) e metti la chiavetta come primo
   dispositivo di avvio.
3. Scegli la voce della chiavetta. Se compaiono due voci, una con «UEFI», prendi quella UEFI se il PC è recente.

La ISO è configurata per avviarsi sia da UEFI (`grub-efi`) sia da BIOS tradizionale (`syslinux`). L'avvio UEFI è
provato solo in macchina virtuale; **l'avvio BIOS e quello su hardware vero non sono verificati**.

### Secure Boot

**Non verificato.** La ISO usa il `shim-signed` di Debian, quindi in teoria dovrebbe avviarsi con Secure Boot
attivo, ma nessuno l'ha provato. Se non parte, disattiva Secure Boot nel UEFI e riprova, poi dicci cosa è successo.

## 4. Il sistema live

Il sistema parte da chiavetta senza toccare il disco.

- **Utente:** `quack`. **Password:** `live`. (Sono i valori di default di `live-config` di Debian.)
- L'accesso è automatico: dovresti arrivare direttamente al desktop senza digitare nulla.
- `quack` è nel gruppo `sudo` senza password.
- La lingua di avvio è l'italiano.
- La sessione di default è **Plasma su X11**, perché funziona su più hardware (GPU vecchie, VM).

### Parametri di avvio utili

Si aggiungono alla riga di comando del kernel dal menu di avvio (nel menu GRUB: tasto `e`, aggiungi in fondo alla
riga che inizia con `linux`, poi `F10`/`Ctrl+X`; nel menu syslinux: `Tab` e scrivi in fondo). Si perdono al riavvio.

| Parametro | Cosa fa |
|---|---|
| `quackos.wayland` | usa la sessione Plasma Wayland invece di X11 (il default) |
| `nomodeset` | parametro standard di Linux: niente driver grafici avanzati; prova se lo schermo resta nero o a righe |
| `noautologin` | parametro di `live-config`: disattiva l'accesso automatico e mostra il login (`quack` / `live`) |

Altri parametri di `live-config` (`username=`, `hostname=`, `locales=`, `keyboard-layouts=`, `timezone=`) esistono
ma non sono stati provati su QuackOS.

## 5. Installare con Calamares

⚠️ **Non verificato:** l'installazione non è mai stata eseguita fino in fondo. Per ora provala in una macchina
virtuale o su un PC di prova, **non sul computer con i tuoi dati** senza un backup. Non si sa ancora come si
comporta con il dual boot con Windows.

1. Dal sistema live apri l'installer di Calamares (voce «Installa» nel menu applicazioni o sul desktop).
2. Segui i passi: lingua, fuso orario, tastiera, partizionamento, utente e password.
3. Al termine riavvia e togli la chiavetta.

Il partizionamento è il passo che può cancellare dati: leggi bene cosa propone Calamares prima di confermare.

## 6. Primo avvio e aggiornamenti

- Nel sistema installato accedi con l'utente e la password che hai scelto in Calamares (non `quack`/`live`).
- Apri un terminale e scrivi `quack` per il «rapporto dello stagno».
- Aggiornare tutto il sistema:

  ```sh
  quack update
  ```

  Chiede la password (via `pkexec`) ed esegue `apt-get update`, `apt-get full-upgrade` e `apt-get autoremove`.
- Le app della suite (Stagno, Quire, Ligature, Gantry, Bivouac, Natter) si aggiornano anche da sole.

## Segnalare i bug

<https://github.com/Quezka/quackos/issues>

Più informazioni dai, più facile è: versione di QuackOS, hardware o macchina virtuale, cosa hai provato, cosa è
successo, e se sei in live o su sistema installato. Se il sistema live parte, nel terminale puoi allegare l'output di
`/usr/local/lib/quackos/debug-report` (se presente nella tua versione).
