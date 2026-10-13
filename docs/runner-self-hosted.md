# Runner GitHub self-hosted sul server di casa

Obiettivo: far girare la build della ISO sul server dell'utente invece che su GitHub, così la ISO finisce
direttamente sul NAS e non ci sono limiti di dimensione. Questo documento è solo ricerca: **non installa niente
e non cambia nessun workflow**. Le fonti sono le pagine ufficiali di GitHub Docs lette il 2026-10-13; dove non
ho potuto verificare lo scrivo.

## Prima di tutto: il rischio vero

GitHub sconsiglia i runner self-hosted sui repo pubblici. Dalla pagina "Adding self-hosted runners":
«We recommend that you only use self-hosted runners with private repositories. Forks of a public repository
could run dangerous code on your runner through a pull request.» Dalla guida alla sicurezza (secure use):
chiunque possa fare un fork e aprire una pull request può compromettere il runner, compresi i secret e il
`GITHUB_TOKEN`; e i runner non offrono garanzie di essere macchine pulite ed effimere, quindi un codice ostile
può restarvi in modo persistente.

`Quezka/quackos` è pubblico, e la build parte anche da `pull_request` (vedi `on:` di `.github/workflows/build.yml`).
**Il punto che molti sbagliano:** un workflow di una pull request da fork viene letto dal ramo della PR. Chi
apre la PR può quindi modificare il file e scrivere `runs-on: [self-hosted, quackos]`, togliendo l'`if:` che
avevamo messo. Un `if:` nel workflow, da solo, NON protegge il runner: lo proteggono le impostazioni del
repo e la macchina stessa. Perciò sotto ci sono tre livelli.

## Livello 1: impostazioni del repo (da fare PRIMA di registrare il runner)

Repo `Quezka/quackos` → Settings → Actions → General:

1. **Approval for running fork pull request workflows from contributors** → scegli
   **«Require approval for all external contributors»**. Oggi il repo è su `first_time_contributors`
   (letto con `gh api repos/Quezka/quackos/actions/permissions/fork-pr-contributor-approval`), che NON basta:
   chi ha già una PR accettata non richiede più approvazione. Da riga di comando, se preferisci:
   `gh api -X PUT repos/Quezka/quackos/actions/permissions/fork-pr-contributor-approval -f approval_policy=all_external_contributors`
   (il valore `all_external_contributors` l'ho dedotto dal nome dell'opzione nell'interfaccia, non l'ho
   verificato nella documentazione dell'API: controlla la risposta del comando).
2. Il documento di GitHub nota che queste approvazioni **non valgono per i workflow `pull_request_target`**,
   che girano nel contesto del ramo base: il nostro `build.yml` non li usa, e non vanno aggiunti.
3. Le impostazioni "Run workflows from fork pull requests / Send write tokens / Send secrets" compaiono
   **solo per i repo privati**, non per questo.
4. Actions permissions → «Allow Quezka, and select non-Quezka, actions»: elenca solo le azioni che usiamo
   (`actions/checkout@*`, `actions/upload-artifact@*`, ecc.; per i lockfile serve il jolly `@*`, non il tag).

## Livello 2: il workflow e i gruppi di runner

- **Runner group: non disponibile.** I gruppi di runner con accesso limitato a certi repo esistono per le
  **organizzazioni** (pagina "Managing access to self-hosted runners using groups"). `Quezka` è un account
  **utente** (`gh api users/Quezka` → `type: User`): la documentazione non dice che i gruppi valgano per i
  repo personali, quindi non posso proporli come difesa. Per averli servirebbe creare un'organizzazione e
  spostare il repo (non l'ho verificato e cambia anche gli URL).
- **Label dedicata:** registra il runner con una label sua, per esempio `quackos`, e nel workflow usa
  `runs-on: [self-hosted, quackos]` solo nel job che costruisce la ISO. La label serve a non catturare
  per sbaglio altri job, NON come sicurezza.
- **Condizione sul job**, solo per la ISO:

  ```yaml
  iso:
    runs-on: [self-hosted, quackos]
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v') && github.actor == 'Quezka'
  ```

  I tag possono essere creati solo da chi ha accesso in scrittura al repo, quindi un fork non può far partire
  questo job con un tag del repo principale. Limite: `github.actor` è chi ha avviato l'evento; con un
  re-run è chi lo rilancia. Che GitHub valuti l'`if:` di un job prima di assegnarlo a un runner (e quindi non
  lo occupi) è il comportamento normale, ma non l'ho trovato scritto nelle pagine che ho letto.
- **Separa i workflow:** metti la build self-hosted in un file diverso da quello che gira sulle PR
  (`release-iso.yml` con `on: push: tags: ['v*']` e nient'altro). Così le PR non toccano mai quel file
  nella cosa che conta, e ricordati che una PR può comunque *aggiungere* un file nuovo: il livello 1 resta
  obbligatorio.

## Livello 3: la macchina

- **Un LXC o una VM solo per questo**, non il NAS e non una macchina con dati. GitHub raccomanda di non
  tenere dati sensibili sul runner e di limitarne l'accesso di rete ai servizi sensibili.
- **Effimero**, se riesci: GitHub dice che i runner just-in-time eseguono «at most one job» e poi spariscono;
  avvertono però che riusare lo stesso hardware può esporre informazioni, quindi serve un'automazione che
  ricrei un ambiente pulito (snapshot Proxmox ripristinato dopo ogni build). Il flag `--ephemeral` di
  `config.sh` fa deregistrare il runner dopo un job (lo riportano i documenti di autoscaling di GitHub, non
  la pagina di installazione); con un solo job per tag va bene, ma poi va riregistrato.
- **Rete:** firewall dal container verso internet (serve per GitHub e Debian) e verso un'unica destinazione
  sul NAS per consegnare la ISO. Niente accesso a Gitea, Nextcloud, Proxmox, quire-server o al resto della LAN.
- **Nessun secret** del server dentro la macchina. Per consegnare la ISO usa una chiave SSH dedicata, valida
  solo per un utente senza shell che scrive in una cartella sola.
- **Utente senza privilegi** per il servizio, niente `sudo`, niente Docker del host. La build di live-build
  ha bisogno di root nel chroot: il container deve essere un LXC privilegiato o una VM, e proprio per questo
  va trattato come usa-e-getta. (Verifica da fare: se `lb build` gira in un LXC non privilegiato.)

## Registrazione (passi ufficiali)

Serve essere il proprietario del repo. In Settings → Actions → Runners → **New self-hosted runner** scegli
Linux e x64 e lancia i comandi che la pagina mostra: scaricano il runner, lanciano `config` con l'URL e un
token valido **un'ora** e poi `run`. Quando il terminale scrive «Connected to GitHub» e «Listening for
Jobs» il runner è pronto. Il token non va salvato né messo in un repo o in una chat.

Opzioni utili di `./config.sh` (da una guida di terzi, non dalla pagina ufficiale: controlla con
`./config.sh --help` sulla versione scaricata): `--labels quackos`, `--ephemeral`, `--unattended`,
`--disableupdate` (GitHub chiede comunque di aggiornare il runner entro 30 giorni da ogni versione nuova).

**Come servizio systemd** (pagina "Configuring the self-hosted runner application as a service"), nella cartella
del runner, con il runner fermo:

```sh
sudo ./svc.sh install runner   # "runner" = nome dell'utente senza privilegi
sudo ./svc.sh start
sudo ./svc.sh status
```

Per fermarlo: `sudo ./svc.sh stop`, e `sudo ./svc.sh uninstall` per toglierlo. Su Debian con `needrestart` la
pagina consiglia di escludere il servizio, così non viene riavviato durante un job.

## Rischi che restano comunque

- Un repo pubblico con un runner self-hosted resta contro il consiglio ufficiale: se le impostazioni del
  livello 1 vengono cambiate o c'è un errore, un fork può eseguire codice sul server. Il livello 3 serve
  proprio a rendere quell'incidente poco dannoso.
- Chi ha accesso in scrittura al repo (oggi solo l'utente) può far girare qualsiasi cosa sul runner.
  Se un giorno si aggiungono collaboratori, riesaminare tutto.
- Un tag sbagliato fa partire una build e una release pubblica: il runner non cambia questo.
- La build ha accesso a internet: un pacchetto compromesso nei sorgenti di Debian o in un `.deb` della suite
  si esegue nel container. Il controllo SHA-256 dei `.deb` (`scripts/fetch-suite.py`) resta importante.

## Alternativa da valutare (nessuna superficie d'attacco in ingresso)

Lasciare la build su GitHub e far **tirare** la ISO al server: uno script sul server, con un token GitHub in
sola lettura che resta solo lì, controlla le release o gli artefatti e scarica il file sul NAS. Non apre
porte, non esegue codice di terzi a casa. Il limite è che la ISO deve stare comunque su GitHub (2 GiB per
file, e gli artefatti durano 7 giorni): dopo la riduzione dei firmware potrebbe starci in un solo file.

## Cosa non ho potuto verificare

- Il comportamento esatto di `if:` a livello di job rispetto all'assegnazione al runner.
- Che i runner group non valgano per gli account utente (la documentazione non li cita).
- Il valore `all_external_contributors` dell'API per l'approvazione delle PR.
- Se `lb build` funziona in un LXC non privilegiato.
- Le opzioni di `config.sh` sulla versione attuale del runner.
