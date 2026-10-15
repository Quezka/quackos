# Server delle ISO (casa)

Niente release su GitHub finché il desktop non funziona: le ISO si compilano sul portatile e si pubblicano sul server di casa.

```sh
scripts/local-build.sh      # compila in un container Debian 13, ISO in out/ (si pulisce da sola)
scripts/publish-iso.sh      # manda l'ISO più recente al server e controlla il checksum lì
```

Si scarica da **http://quackos.lan/** (solo dalla rete di casa): `quackos-latest-amd64.iso` punta sempre all'ultima, `latest.json`
dice versione, dimensione, checksum e data. Sul server restano le 2 ISO più recenti. Il dashboard (`QUACKOS_URL`) mostra la stessa informazione.

## Com'è fatto (2026-10-15)

- Proxmox `nas`, container **106 `quackos`** (Debian 13, 1 core, 512 MB, disco 2 GB, avvio automatico, ordine 8), IP 192.168.1.14 (DHCP:
  conviene riservarlo nel router; il nome `quackos.lan` lo risolve il router).
- Le ISO stanno in `/var/lib/vz/quackos` del Proxmox, montata nel container come `/srv/quackos` (non riempie il disco del container).
- **Caddy** serve `/srv/quackos` in HTTP sulla porta 80 (`file_server browse`), solo LAN.
- L'utente `quackos` (senza password) accetta solo la chiave ssh del portatile e ha scrittura in `/srv/quackos`.
- `scripts/publish-iso.sh` usa `rsync` (si può riprendere) e poi `ssh`: `QUACKOS_HOST=quackos@192.168.1.14` se il nome non si risolve.

## Rifarlo da zero

```sh
pct create 106 local:vztmpl/debian-13-standard_13.6-1_amd64.tar.zst --hostname quackos --cores 1 --memory 512 --swap 256 \
  --rootfs local-lvm:2 --net0 name=eth0,bridge=vmbr0,ip=dhcp,firewall=1 --unprivileged 1 --onboot 1 --startup order=8,up=20 \
  --mp0 /var/lib/vz/quackos,mp=/srv/quackos     # prima: mkdir -p /var/lib/vz/quackos && chown 101000:101000 /var/lib/vz/quackos
# dentro: apt install caddy openssh-server rsync; useradd -m -u 1000 quackos; chiave in ~quackos/.ssh/authorized_keys;
# Caddyfile: ":80 { root * /srv/quackos \n file_server browse }"
```

`server/quackos-pull.sh` (lo script che scarica le release da GitHub) non serve finché non ci sono release.
