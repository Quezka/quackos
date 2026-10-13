# Distribuire la ISO dal proprio server (il server scarica)

Il server di casa controlla ogni ora le release di GitHub, scarica la ISO nuova, ne verifica lo SHA-256 e la mette in
una cartella pronta da servire. **Nessuna porta aperta, nessun runner, nessun segreto**: il repo è pubblico e i file
delle release si scaricano senza token. (Un runner self-hosted su un repo pubblico è sconsigliato da GitHub, vedi
`docs/runner-self-hosted.md`.)

## Cosa fa `server/quackos-pull.sh`

- Legge `releases/latest` del repo, trova `quackos-<v>-amd64.iso` (o le parti `.part00`, `.part01`… e le unisce
  mentre scarica, senza bisogno di spazio doppio) e `quackos-<v>-amd64.iso.sha256`.
- Confronta lo SHA-256: se **non coincide** cancella tutto e non pubblica niente; la versione precedente resta com'era.
- Crea i nomi fissi `quackos-latest-amd64.iso` e `.sha256` (collegamenti) e `latest.json` (versione, byte, sha256, data).
- Tiene solo le ultime `QUACKOS_KEEP` versioni (2 di default), ordinate per numero di versione (1.10.0 > 1.2.0).
- Rifiuta tag strani, checksum che non sono un SHA-256 e usa un lucchetto: due esecuzioni insieme non si pestano.

Collaudato con un finto GitHub locale (`tests/test_server_pull.py`): file unico, file a più parti, checksum sbagliato,
ripetizione, pulizia, tag malevolo. **Non** è stato provato sul tuo server né con un vero download da 2 GB.

## Installazione (sul server, come root)

```sh
useradd --system --home /srv/quackos --shell /usr/sbin/nologin quackos
mkdir -p /srv/quackos && chown quackos:quackos /srv/quackos
install -m 755 server/quackos-pull.sh /usr/local/bin/quackos-pull
install -m 644 server/quackos-pull.service server/quackos-pull.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now quackos-pull.timer
# prova subito, a mano:
systemctl start quackos-pull.service && journalctl -u quackos-pull -n 20 --no-pager
ls -lh /srv/quackos
```

Servono `curl`, `jq`, `flock` e `sha256sum` (su Debian: `apt install curl jq util-linux coreutils`).
Se la cartella sta sul NAS (NFS/SMB), cambia `QUACKOS_DEST` e `ReadWritePaths=` nell'unità.

## Servirla (passo successivo, non ancora fatto)

Qualunque server web che serva `/srv/quackos` in sola lettura va bene (Caddy, nginx). Il link stabile da mettere sul sito
è `…/quackos-latest-amd64.iso` con accanto `…/quackos-latest-amd64.iso.sha256`.

**Cloudflare:** la vecchia sezione 2.8 dei loro termini è stata eliminata nel 2023, ma servire file grandi ospitati altrove
dal loro CDN, anche tramite Tunnel, potrebbe essere ancora limitato dalle condizioni specifiche del CDN. Non è verificato:
va letto nei *Service-Specific Terms* attuali prima di servire 2 GB dietro il tunnel. Alternative: R2 (servizio loro, dove i
file grandi sono previsti) o un dominio senza proxy.

## Se qualcosa non va

- `journalctl -u quackos-pull` mostra l'errore. «SHA-256 mismatch» = download corrotto: riprova all'ora dopo.
- Il limite dell'API di GitHub senza token è 60 richieste/ora: un controllo all'ora basta. Per alzarlo si può mettere
  `Environment=GITHUB_TOKEN=…` nell'unità (un token a sola lettura, mai nel repo).
