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

labwc non fa **sfocatura dello sfondo** (blur), **animazioni di finestra** (genie, zoom) né **ombre morbide** di livello macOS.
Con labwc possiamo arrivare a circa l'80% dell'aspetto. Per il 100% serve il **compositor nostro** (fase 4). La 0.1.2 ha già
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
