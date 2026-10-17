# Public Linux VPS deployment — VMESH-only Stratum + web dashboard

This guide explains how to publish **both** VargaMesh MiniPool's SOLO Stratum server and its browser dashboard to the internet using Docker Compose. It works with the integrated official **VargaMesh Core** full node. **No Bitcoin node, merged BTC mining, Node.js, or npm are needed.**

> **Important security notice:** Publishing the built-in web dashboard directly on TCP 8686 exposes miner wallet addresses, worker names, pool activity, and errors to anyone who can reach it. The dashboard has **no password authentication and no HTTPS server**. The Stratum V1 server on TCP 3938 is unencrypted, does not authenticate miners beyond their self-declared public VMESH wallet address, and is not hardened for arbitrary public traffic or connection-flooding. Use these public bindings only if you accept those risks. For an internet-facing service, prefer a reverse proxy with HTTPS + access control for the web UI, and network-layer rate limiting / upstream firewall protection for Stratum. This project remains a developer preview without an independently validated real ASIC-discovered VMESH mainnet block.

## 1. What is exposed?

| Service | Docker host listen address | TCP port | Internet access |
|---|---|---|---|
| VMESH Stratum V1 | `0.0.0.0` | `3938` | Public miners / ASICs |
| MiniPool web dashboard | `0.0.0.0` | `8686` | Public read-only HTTP |
| VMESH Core JSON-RPC | `127.0.0.1` **inside container** | `29667` | **Never publish** |
| VMESH peer-to-peer | Outbound from dedicated node | `29666` | Outbound only in this setup |

**`0.0.0.0` means “listen on all interfaces”. It is NOT an address you put into a browser or Bitaxe.** Connect to the VPS public IPv4 or a DNS hostname instead.

## 2. Update the existing VPS installation safely

On the VPS where you already ran `bash start-docker.sh`:

```bash
cd ~/vargamesh-minipool
git pull --ff-only
```

If the repository lives under another path, `cd` into that path first. **Do not remove Docker volumes or run `docker compose down -v`.** Your dedicated Core blockchain data is held in `vargamesh-minipool_vmesh_chain`; it survives an ordinary container recreation.

## 3. Explicitly enable both public ports

Edit `.env`:

```bash
nano .env
```

Add or update these **exact** variables (replace the example address with your VPS's real public IPv4 or DNS name):

```dotenv
MINIPOOL_STRATUM_BIND_IP=0.0.0.0
MINIPOOL_WEB_BIND_IP=0.0.0.0
MINIPOOL_DASHBOARD_ALLOWED_HOSTS=YOUR_PUBLIC_IPV4,pool.example.com
MINIPOOL_SHARE_DIFFICULTY=1024
```

- **Stratum bind:** Docker publishes `0.0.0.0:3938` on the Linux host.
- **Web bind:** Docker publishes `0.0.0.0:8686` on the Linux host.
- **Dashboard allowed hosts:** This must contain the **public hostname and/or the public IPv4 actually used by visitors**. Separate multiple names with commas, without ports or `http://`. If you only use an IP, remove `,pool.example.com`; if you only use a domain, remove the example IP.
- **Share difficulty:** `1024` remains the default for Bitaxe. Do not change it only to suppress a share validation problem.

**The Host-header allowlist is not user authentication.** It rejects unexpected HTTP Host names, but any visitor who knows the allowed public hostname can view the dashboard.

If you want to keep the web dashboard private, leave `MINIPOOL_WEB_BIND_IP=127.0.0.1` and instead configure the optional Nginx Proxy Manager (NPM) HTTPS access-control setup in [the Docker guide](DOCKER.de.md).

## 4. Recreate the container without deleting the blockchain

Run the normal Compose configuration (do **not** add `compose.lan.yaml` for this public setup):

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=90 minipool
```

Or run `bash start-docker.sh` after editing `.env`. That script now displays the configured host binds and warns about publicly exposed services.

Check actual host publication:

```bash
docker compose port minipool 3938
docker compose port minipool 8686
```

Expected, if both settings are enabled:

```text
0.0.0.0:3938
0.0.0.0:8686
```

The container's own log `Stratum listening at 0.0.0.0:3938` alone **does not** confirm external access; Docker's published **host** addresses determine that.

## 5. Allow the right ports through the VPS firewall

You need **inbound TCP 3938 and TCP 8686** permitted by your VPS provider/cloud firewall and any host firewall/forwarding policy.

- For a public VPS, configure provider security groups / firewall rules specifically for TCP 3938 and 8686.
- Check whether a firewall is already active before changing it: `sudo ufw status verbose`, `sudo nft list ruleset`. **Do not flush or overwrite existing firewall rules**, especially SSH access.
- **Docker's published ports can bypass normal UFW INPUT filtering** through NAT/forwarding. Do not assume that `ufw deny 8686` blocks a published Docker port; enforce the restriction at the provider firewall and/or the appropriate Docker forwarding firewall chains.
- Port `29667` (Core RPC) must stay private. Never publish it.
- If you are using an authenticated HTTPS reverse proxy, keep `MINIPOOL_WEB_BIND_IP=127.0.0.1` instead and expose only HTTPS (`443`) for web access.
- For public mining, consider allowlisting miner IP addresses, upstream rate limiting and monitoring for abnormal connection counts; the built-in Stratum server has no TLS or dedicated abuse controls.

The Docker bind update **does not itself modify the VPS provider firewall**.

## 6. Test from outside the VPS

From your PC / phone on a different network:

**Public web dashboard:**

```text
http://YOUR_PUBLIC_IPV4:8686/
```

**Public read-only API:**

```text
http://YOUR_PUBLIC_IPV4:8686/api/status
```

If you get HTTP **403**, the `Host` header (domain or public IP) is probably missing from `MINIPOOL_DASHBOARD_ALLOWED_HOSTS`.

**Bitaxe / other compatible SHA-256d ASIC:**

| AxeOS pool field | Example |
|---|---|
| Pool hostname | `YOUR_PUBLIC_IPV4` or `pool.example.com` |
| Pool TCP port | `3938` |
| Stratum protocol | V1 |
| Username | `vm1YOUR_VALID_WALLET_ADDRESS.bitaxe01` |
| Password | `x` |
| Share difficulty | `1024` (pool's default) |

Miner address and worker name are public identifiers; never put a seed phrase, private key, or account password into Stratum credentials.

When the dedicated VMESH Core is still in initial blockchain synchronization, Stratum can accept TCP connections but **will not issue valid mining jobs until Core reports that mainnet is synchronized**.

## 7. Nginx Proxy Manager (NPM) alternative for web

A safer public-web design is:

- Keep direct TCP `8686` bound to `127.0.0.1`.
- Use `compose.npm.yaml` and an existing shared NPM Docker network, with a configured **HTTPS Proxy Host and Access List**.
- Proxy to `http://vmesh-minipool:8686` on the shared network.
- Set `MINIPOOL_DASHBOARD_ALLOWED_HOSTS=pool.example.com`.
- Publicly expose **TCP 443 (web)** and, if required, **TCP 3938 (Stratum)**.

NPM reverse-proxy HTTP/WebSocket settings **do not proxy the raw Stratum TCP protocol**. NPM does not make the Stratum port secure or encrypted.

## 8. Updates, troubleshooting, and rollback

Normal update, preserving the existing volumes:

```bash
cd ~/vargamesh-minipool
git pull --ff-only
docker compose up -d --build
docker compose logs -f --tail=80
```

If you want to revert to private-only without deleting the node:

```dotenv
MINIPOOL_STRATUM_BIND_IP=127.0.0.1
MINIPOOL_WEB_BIND_IP=127.0.0.1
```

Then run `docker compose up -d` again.

Troubleshooting commands:

```bash
docker compose config
docker compose ps
docker compose port minipool 3938
docker compose port minipool 8686
docker compose logs --tail=200 minipool
curl -fS http://127.0.0.1:8686/api/status
```

Potential causes of connection problems: upstream cloud firewall; local forwarding firewall policy; invalid Host allowlist; DNS not resolving to the VPS; Core still synchronizing; another service already occupying host port 3938 or 8686.

**Fee:** 99% of the successful VMESH child block's Coinbase reward goes to the miner-supplied `vm1...` payout address, and 1% is routed to the existing VMESH developer output. This is a MiniPool implementation setting, not a mandatory VMESH network fee.
