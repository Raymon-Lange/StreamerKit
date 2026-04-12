# Proxmox Deployment Plan Checkpoint

Last updated: 2026-04-12

## Status

- Point 1: decided and locked
- Point 2-4: drafted, pending final confirmation
- Point 5: paused for shared-host networking/port strategy
- Point 6-8: not yet reviewed

## Decisions Made

- Platform: Proxmox **LXC** (not VM)
- Runtime in LXC: Docker Engine + Docker Compose
- Image source: GitHub Container Registry (**GHCR**)
- Deployment style: pull prebuilt image (`image:`), no local `build:` in production
- Tag strategy: prefer immutable tags (version or commit-SHA), avoid `latest` for prod

## Draft Plan So Far

### Point 1 (Container Strategy)

- Use Proxmox LXC with GHCR image pulls.
- LXC Docker requirements include `nesting=1,keyctl=1`.
- Start unprivileged LXC; only switch if Docker compatibility issues require it.

### Point 2 (Prepare Runtime Host)

- Debian 12 LXC baseline sizing discussed: 2 vCPU / 4 GB RAM / 30-40 GB disk.
- Configure static IP and DNS.
- Install Docker + Compose plugin and core packages.
- Prepare directories:
  - `/opt/baseball-app`
  - `/opt/baseball-data/cache`
  - `/opt/baseball-data/env`
- Authenticate to GHCR with PAT (`read:packages`) for pulls.

### Point 3 (Deploy App Code/Config)

- Keep deployment files in `/opt/baseball-app` (compose, optional deploy script).
- Production compose should reference GHCR image by tag.
- Runtime `.env` contains:
  - `LEAGUE_ID`
  - `TEAM_ID`
  - `ESPN_S2`
  - `ESPN_SWID`
  - optional `API_KEY`
- Persist cache via volume mount:
  - `/opt/baseball-data/cache:/app/.cache`

### Point 4 (Production Container Config)

- Use production command (no reload), e.g. uvicorn host `0.0.0.0`.
- No source bind mount in production.
- Add restart policy and healthcheck.
- Add log rotation and rollback-by-tag process.

## Open Questions (Needed Before Finalizing Points 5-8)

1. Reverse proxy approach: shared proxy already running (Nginx/Traefik/Caddy) or app-specific proxy?
2. App isolation model: one LXC per app, or multiple apps per LXC?
3. Domain/hostname for this API?
4. Current port inventory and reserved ranges on host/network?
5. Network model (bridge/VLAN) and whether each app gets its own IP?
6. Security baseline (firewall model, VPN/admin access, fail2ban/WAF, secret handling)?
7. Deploy workflow (manual vs GitHub Actions) and GHCR credential storage approach?
8. Observability standards (logs/metrics/uptime checks)?
9. Backup/restore policy (what to back up and target RPO/RTO)?
10. Tag policy (immutable-only in prod, or allow floating tags in non-prod)?

## Resume Checklist (Next Session)

1. Answer the open questions above.
2. Finalize Point 5 (ports, reverse proxy, TLS, firewall exposure).
3. Finalize Point 6 (security hardening controls).
4. Finalize Point 7 (ops: monitoring, logging, backup, update workflow).
5. Finalize Point 8 (validation and go-live checklist).
6. Generate final production artifacts:
  - `compose.yaml` for GHCR deploy
  - optional proxy config
  - concise runbook with deploy + rollback commands

