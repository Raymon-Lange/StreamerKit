# Promote to Hive — baseball

Use this checklist when moving baseball from local dev to the hive lab for the first time. Work through every step in order. Each step must be complete before starting the next.

---

## Prerequisites

Before starting:
- [ ] App is working in local dev
- [ ] `/hive-ops-deploy` has been run and all gaps are resolved
- [ ] App repo is pushed to GitHub with a working CI/CD pipeline

---

## Step 1 — Provision the LXC on Proxmox

Each app gets its own LXC.

1. Log in to the Proxmox web UI (`https://proxmox.lab`)
2. Create a new LXC container:
   - **Template**: Ubuntu 22.04
   - **CPU**: 2 cores minimum
   - **RAM**: 1 GB
   - **Disk**: 8 GB (not including app data under `./data/`)
   - **Hostname**: `baseball`
   - **IP**: Assign a static IP on the LAN (`TBD/24`, gateway `192.168.86.1`)
3. Start the container and open a console

**Generate a deploy SSH key (on your local machine):**

```bash
ssh-keygen -t ed25519 -C "baseball-deploy" -f ~/.ssh/baseball_deploy -N ""
```

This creates:
- `~/.ssh/baseball_deploy` — private key (goes to GitHub secrets)
- `~/.ssh/baseball_deploy.pub` — public key (goes on the LXC)

**Bootstrap the LXC:**

```bash
# Update packages
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Create the deploy user
useradd -m -s /bin/bash deploy
usermod -aG docker deploy

# Add the deploy public key
mkdir -p /home/deploy/.ssh
echo "$(cat ~/.ssh/baseball_deploy.pub)" >> /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

Verify SSH access before continuing:
```bash
ssh -i ~/.ssh/baseball_deploy deploy@TBD "echo connected"
```

Add the entry to your local `~/.ssh/config` for convenience:
```
Host baseball
    HostName <tailscale-ip>
    User deploy
    IdentityFile ~/.ssh/baseball_deploy
    IdentitiesOnly yes
```

**Verify the LXC is ready before moving on:**

```bash
ssh -i ~/.ssh/baseball_deploy deploy@TBD "echo connected"
ssh -i ~/.ssh/baseball_deploy deploy@TBD "docker run --rm hello-world"
ssh -i ~/.ssh/baseball_deploy deploy@TBD "uname -a && free -h && df -h /"
```

- [ ] SSH key pair generated at `~/.ssh/baseball_deploy`
- [ ] LXC provisioned and started
- [ ] Docker installed and working as `deploy` user (`docker run --rm hello-world`)
- [ ] `deploy` user created and in `docker` group
- [ ] SSH confirmed: returns `connected`

---

## Step 2 — Create Docker networks on the LXC

Run once per LXC. These are the shared hive networks all apps use.

```bash
ssh deploy@TBD
docker network create frontend
docker network create backend
```

Verify:
```bash
docker network ls | grep -E "frontend|backend"
```

- [ ] `frontend` network exists
- [ ] `backend` network exists

---

## Step 3 — Install and auth Tailscale

Tailscale enables GitHub Actions to deploy to this LXC from anywhere on the tailnet.

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate (copy the URL and open in browser)
tailscale up --ssh=false

# Confirm the node is up and note the Tailscale IP
tailscale ip -4
```

Add the Tailscale IP to your local `~/.ssh/config`:

```
Host baseball
    HostName <tailscale-ip>
    User deploy
    IdentityFile ~/.ssh/baseball_deploy
    IdentitiesOnly yes
```

- [ ] Tailscale installed and authenticated
- [ ] Node appears in Tailscale admin console
- [ ] Tailscale IP noted: `100.x.x.x`
- [ ] SSH config entry updated with Tailscale IP

---

## Step 4 — Add DNS entry in Pi Hole

This makes the app reachable by hostname on the LAN.

1. Open the Pi Hole admin UI (`http://pihole.lab/admin`)
2. Go to **Local DNS → DNS Records**
3. Add a new record:
   - **Domain**: `streamerkit.lab`
   - **IP**: LXC LAN IP (`TBD`) — use LAN IP, not Tailscale IP
4. Save

Verify from another machine on the network:
```bash
nslookup streamerkit.lab
```

- [ ] DNS record `streamerkit.lab → TBD` created in Pi Hole
- [ ] `nslookup streamerkit.lab` resolves to the correct LXC IP

---

## Step 5 — Configure local nginx on the LXC

Each app LXC runs its own nginx to proxy from port 80 to the Docker container port.

```bash
ssh deploy@TBD
apt install -y nginx
```

Create the nginx config at `/etc/nginx/sites-available/baseball`:

```nginx
server {
    listen 80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /nginx_status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
```

Enable and start:
```bash
ln -s /etc/nginx/sites-available/baseball /etc/nginx/sites-enabled/
nginx -t
systemctl enable nginx
systemctl start nginx
```

Verify nginx proxies to the container:
```bash
curl -I http://localhost
```

- [ ] nginx installed and running
- [ ] nginx config created and enabled
- [ ] `curl -I http://localhost` returns a response from the app

---

## Step 6 — Central proxy and Cloudflare DNS

> **N/A** — baseball is LAN-only (`streamerkit.lab`). No public domain, no SSL cert, no Cloudflare DNS record required. Skip Steps 6 and 7.

---

## Step 7 — (Skipped — LAN-only app)

---

## Step 8 — Add GitHub Actions secrets

The deploy pipeline needs secrets to SSH into the LXC via Tailscale.

1. Go to `https://github.com/Raymon-Lange/baseball` → **Settings → Secrets and variables → Actions**
2. Add the following secrets:

| Secret name | Value |
|---|---|
| `SSH_HOST` | Tailscale IP of the LXC (`100.x.x.x`) |
| `SSH_USER` | `deploy` |
| `SSH_PRIVATE_KEY` | Contents of `~/.ssh/baseball_deploy` (the private key) |
| `TS_OAUTH_CLIENT_ID` | Tailscale OAuth client ID (from Tailscale admin → OAuth clients) |
| `TS_OAUTH_SECRET` | Tailscale OAuth secret |

To copy the private key:
```bash
cat ~/.ssh/baseball_deploy
```
Paste the entire output including the `-----BEGIN` and `-----END` lines.

To get the Tailscale OAuth credentials:
1. Go to [Tailscale admin console](https://login.tailscale.com/admin) → **Settings → OAuth clients**
2. Create a new client with `devices:write` scope and tag `tag:ci`
3. Copy the client ID and secret

- [ ] `SSH_HOST` secret added
- [ ] `SSH_USER` secret added
- [ ] `SSH_PRIVATE_KEY` secret added
- [ ] `TS_OAUTH_CLIENT_ID` secret added
- [ ] `TS_OAUTH_SECRET` secret added

---

## Step 9 — Deploy the app

```bash
ssh deploy@TBD

# Clone the app repo
git clone https://github.com/Raymon-Lange/baseball.git /home/deploy/baseball
cd /home/deploy/baseball

# Create the data directory for the ranking cache
mkdir -p ./data/.cache

# Set up the env file
cp .env.example .env
nano .env    # fill in all values marked "changeme"

# Pull and start
docker compose pull
docker compose up -d
docker compose ps
```

- [ ] Repo cloned to `/home/deploy/baseball`
- [ ] `./data/.cache` directory created
- [ ] `.env` created and all values filled in
- [ ] `docker compose up -d` runs without errors
- [ ] All containers are up: `docker compose ps`

---

## Step 10 — Deploy monitoring agents

Every app LXC runs node_exporter, cadvisor, and nginx_exporter so the monitoring stack can scrape it.

```bash
ssh baseball

mkdir -p /home/deploy/agents
cat > /home/deploy/agents/docker-compose.yml << 'EOF'
services:

  node_exporter:
    image: prom/node-exporter:latest
    restart: unless-stopped
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    restart: unless-stopped
    privileged: true
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8080:8080"

  nginx_exporter:
    image: nginx/nginx-prometheus-exporter:latest
    restart: unless-stopped
    command:
      - '--nginx.scrape-uri=http://localhost/nginx_status'
    network_mode: host
    ports:
      - "9113:9113"
EOF

cd /home/deploy/agents
docker compose up -d
docker compose ps
```

Verify each agent from the monitoring LXC:
```bash
curl -s http://TBD:9100/metrics | head -5
curl -s http://TBD:8080/metrics | head -5
curl -s http://TBD:9113/metrics | head -5
```

- [ ] Agents running: `docker compose -f /home/deploy/agents/docker-compose.yml ps`
- [ ] node_exporter reachable on port 9100
- [ ] cadvisor reachable on port 8080
- [ ] nginx_exporter reachable on port 9113

---

## Step 11 — Register in Prometheus

Add the new LXC to the Prometheus scrape config on `monitoring.lab`, then reload.

```bash
ssh monitoring
nano /home/deploy/monitoring/prometheus/prometheus.yml
```

Make three additions (replace `TBD` with the real LXC IP once assigned):

**1. `node` job — add target and relabel entry:**
```yaml
static_configs:
  - targets:
      - "TBD:9100"          # ← add baseball
relabel_configs:
  - source_labels: [__address__]
    regex: "TBD:.*"
    target_label: instance
    replacement: "baseball"
```

**2. `cadvisor` job — add target:**
```yaml
static_configs:
  - targets:
      - "TBD:8080"          # ← add baseball
```

**3. `nginx` job — add target and relabel entry:**
```yaml
static_configs:
  - targets:
      - "TBD:9113"          # ← add baseball
relabel_configs:
  - source_labels: [__address__]
    regex: "TBD:.*"
    target_label: instance
    replacement: "baseball"
```

Reload Prometheus:
```bash
cd /home/deploy/monitoring
docker compose restart prometheus
```

Verify the new targets are UP:
```bash
docker compose exec prometheus \
  wget -qO- 'http://localhost:9090/api/v1/targets' | grep "baseball"
```

- [ ] `prometheus.yml` updated with baseball targets (node, cadvisor, nginx)
- [ ] Prometheus reloaded
- [ ] baseball targets show `state="up"` in Prometheus

---

## Step 12 — Verify

```bash
# Check container health
docker compose -f /home/deploy/baseball/docker-compose.yml ps

# Confirm LAN access
curl -I http://streamerkit.lab

# Confirm API health endpoint
curl http://streamerkit.lab/health
```

- [ ] All containers healthy: `docker compose ps`
- [ ] App is accessible at `http://streamerkit.lab` on LAN
- [ ] `/health` endpoint returns 200

---

## Step 13 — CI/CD

Confirm the GitHub Actions deploy pipeline works end-to-end:

1. Push a small change to the `main` branch (or merge a PR)
2. Watch the Actions run at `https://github.com/Raymon-Lange/baseball/actions`
3. Confirm the deploy completes and the app is still healthy

- [ ] CI/CD pipeline completes successfully on push to `main`
- [ ] App is still healthy after automated deploy

---

## Reference

| Resource | Location |
|---|---|
| App repo | `https://github.com/Raymon-Lange/baseball` |
| App URL (LAN) | `http://streamerkit.lab` |
| Proxmox UI | `https://proxmox.lab` |
| Pi Hole UI | `http://pihole.lab/admin` |
| Tailscale admin | `https://login.tailscale.com/admin` |
| hive-ops standards | `hive-ops/standards/` |
| LXC IP | `TBD` (update when assigned) |
