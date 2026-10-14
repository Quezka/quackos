# Desktop di QuackOS (progetto 0.2.0): togliere KDE, scrivere il nostro

Obiettivo dell'autore (14 ottobre 2026): niente Plasma. Un desktop nostro, **uguale a macOS** per aspetto e comportamento.
Questo documento è il piano. Lavoro sul ramo `de-work`; `main` resta la 0.1.x (Plasma) finché il nuovo desktop non sta in piedi.

## Cosa significa «un DE nostro»

| Pezzo | Cosa fa | Chi lo scrive |
|---|---|---|
| **Compositor** | disegna e sposta le finestre, input, schermi | prima **labwc** (esistente), poi forse il nostro |
| **Shell** | barra in alto, dock, launcher, centro di controllo, notifiche, sfondo, blocco schermo | **noi** (PySide6 + QML) |
| **Login** | schermata di accesso | SDDM con tema nostro; più avanti un greeter nostro |
| **App di base** | Impostazioni, file manager, terminale, anteprima immagini | **noi**, una alla volta; nel frattempo quelle che ci sono |

## Scelte (e perché)

- **Compositor: labwc 0.8.3** (Debian 13). Basato su wlroots, piccolo, configurabile con file di testo, temi dei bordi con
  pulsanti a sinistra, sessione Wayland vera, Xwayland per le app X11. Scrivere un compositor da zero (wlroots in C, Smithay
  in Rust) significa anni di driver, input, multi-monitor: lo rimandiamo.
- **Shell: PySide6 + QML con layer-shell.** Stesso stack e stessa architettura pulita delle altre app (`app-style-guide`).
  Le barre e il dock sono finestre `layer-shell` (pacchetti Debian verificati: `layer-shell-qt` 6.3.4,
  `qml6-module-org-kde-layershell`, `qt6-wayland`, `python3-pyside6.qtqml` 6.8.2). `layer-shell-qt` è una libreria piccola
  del progetto KDE, **non** Plasma: non porta dentro il desktop.
- **Quickshell non è in Debian 13**: non lo usiamo.
- **Niente asset Apple.** Stessi layout, animazioni e comportamenti; icone, sfondi e font nostri (Inter come font, già in uso).

## Cosa NON si può avere con labwc (onestà)

labwc ha angoli arrotondati e ombre (`cornerRadius`, `dropShadows`, già nel nostro tema), ma non fa **sfocatura dello sfondo** (blur) né
**animazioni di finestra** (genie, zoom). Con labwc possiamo arrivare a circa l'80% dell'aspetto. Per il 100% serve il **compositor nostro** (fase 4). La 0.1.2 ha già
«blur» nel tema di KWin: passando a labwc si perde finché non c'è il compositor nostro.

## Fasi

1. **Sessione minima** (sta in piedi da sola): labwc + sfondo + tema bordi (pulsanti a sinistra) + `quack-shell` che mostra
   la barra in alto con orologio e il dock con le app della suite. Sessione scelta da SDDM accanto a Plasma.
2. **Shell completa**: launcher (Spotlight), centro di controllo (Wi-Fi, volume, luminosità, Bluetooth), demone di
   **notifiche** (`org.freedesktop.Notifications`), menu globale, cambio app, blocco schermo, Mission Control.
3. **App nostre**: Impostazioni, file manager («Finder»), terminale. Poi **togliere i pacchetti KDE** dalla ISO (guadagno
   di dimensione: Plasma pesa centinaia di MB).
4. **Compositor nostro** (wlroots/Smithay): blur, animazioni, gesti del touchpad, ombre.

## Rischi da verificare prima di promettere

- layer-shell da QML in PySide6 su labwc: **non ancora provato** su una build vera.
- Menu globale fuori da KDE (dbusmenu per le app Qt/GTK): da provare; la nostra suite (PySide6) lo può esportare da sé.
- Portali (`xdg-desktop-portal-wlr` 0.7.1 per lo schermo, `xdg-desktop-portal-gtk` per i file): da verificare, senza
  `xdg-desktop-portal-kde`.
- Hardware: touchpad, scaling, suono (PipeWire), rete (NetworkManager) funzionano oggi grazie a Plasma; vanno rifatti nella shell.
- Il portatile di sviluppo ha **2 GB liberi** e non può costruire la ISO: i test sono statici e le prove reali avvengono in CI
  o sull'hardware dell'autore (ThinkPad).

## Regole che valgono ancora

Ogni nome di pacchetto si verifica sull'indice vero di Debian prima di scriverlo (`Packages.xz`); `--apt-recommends false` →
ogni Recommends necessario si elenca a mano; un tag `vX.Y.Z` è una release pubblica: serve il «sì» dell'autore ogni volta.
Stringhe in italiano, russo e inglese; test per ogni pezzo di logica pura.

## Stato della fase 1 (14 ottobre 2026, ramo `de-work`)

Scritto e **testato in modo statico** (84 test, più un test di avvio QML senza schermo con PySide6 6.11 locale):
- `shell/quackshell/`: shell in architettura pulita (`domain` puro → `app` → `infra`, `presentation` = Qt/QML). Barra in alto
  (logo che apre il launcher, orologio) e dock con ingrandimento al passaggio del mouse; le app fissate sono le 6 della
  suite + Dolphin, Konsole, Impostazioni (lista propria in `~/.config/quackos/dock.json`). Senza layer-shell parte in
  finestre normali (`QUACKSHELL_PLAIN=1`), così si prova anche dentro un altro desktop.
- Sessione `QuackOS` per SDDM (`/usr/share/wayland-sessions/quackos.desktop`) → `quackos-session` → labwc con la nostra
  configurazione (`/usr/share/quackos/labwc/`): tema con i tre pulsanti colorati a sinistra, scorciatoie con Super come Command
  (Super+Spazio launcher fuzzel, Super+Q chiude, Super+L blocca), tap e scroll naturale sul touchpad, menu sul desktop con
  Esci / Riavvia / Spegni, notifiche con mako, sfondo con swaybg, blocco/spegnimento schermo con swayidle.
- Pacchetti in `config/package-lists/quackshell.list.chroot`, tutti verificati sull'indice di Debian 13.

**Non provato su una sessione vera:** gli attributi `LayerShell.Window.*` in QML (nomi dedotti dalle proprietà C++ della
libreria, perché il `.qmltypes` del pacchetto è vuoto), l'avvio di labwc dalla sessione SDDM, il polkit agent dentro labwc,
la barra che riserva davvero lo spazio. La finestra del dock è alta 128 px: la parte trasparente sopra il vetro assorbe i
click (da sistemare con una maschera di input).

**Non c'è ancora:** nome dell'app attiva e menu globale nella barra, pallini delle app aperte nel dock, centro di controllo,
notifiche nostre, Mission Control, schermata di blocco nostra: sono la fase 2 (servono i protocolli `foreign-toplevel`).

## Fase 2, primo pezzo (0.2.0-dev1)

- **Elenco finestre** con il protocollo `wlr-foreign-toplevel-management` (labwc lo parla): `infra/toplevels.py` (stato dai
  messaggi del compositor, puro e testato in `Tracker`; il client Wayland è sottile sopra pywayland). I binding si rigenerano
  con `scripts/gen-protocols.py` dall'XML in `shell/protocols/`.
- **Barra:** accanto al logo c'è il nome dell'app in primo piano. **Dock:** pallino sotto le app aperte, le app aperte non
  fissate compaiono dopo quelle fissate, un clic su un'app aperta la porta in primo piano (prima una finestra minimizzata,
  poi la successiva), su un'app chiusa la avvia.
- **Clic che passano:** provato e **scartato**. Una maschera di input (`QWindow.setMask`) faceva sì che Qt non ridisegnasse
  più fuori dalla maschera: il dock aveva riquadri neri (visto in QEMU). La parte trasparente sopra il vetro, alta circa 50 px,
  intercetta quindi i clic; da risolvere in un altro modo (finestra che si ridimensiona, o compositor nostro).
- **Ancora nessun test contro un compositor vero** per il client Wayland: la logica è testata, il collegamento no.
- Manca ancora: menu globale (dbusmenu), centro di controllo, notifiche nostre, Mission Control.
