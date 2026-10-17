# VargaMesh MiniPool für Linux (Docker Compose) — VMESH-only SOLO

Dieses Open-Source-Projekt enthält die **eigene VargaMesh-Mainnet-Node, Stratum V1 für Bitaxe/ASICs und ein responsives Mining-Dashboard**. Keine Bitcoin-Node, keine BTC-Auszahlungen, keine Docker-Börse, kein Node.js/npm erforderlich.

**Linux x86_64 / amd64**. Offizieller VargaMesh-Core v0.2.0 ist bei der Image-Erstellung fest auf die offizielle GitHub-Release-Datei und auf zwei SHA-256-Prüfsummen gepinnt. Die Blockchain wird beim ersten Start synchronisiert; das dauert je nach Netzwerk und Festplatte. **Kein Test eines tatsächlich akzeptierten ASIC-Mainnet-Blocks abgeschlossen.** Vorsicht bei produktivem Einsatz.

## Voraussetzungen

- Linux x86_64 mit Docker Engine und Docker Compose v2
- Genügend SSD-Platz, RAM und Internetverbindung für die VMESH-Blockchain
- Zugriff auf GitHub, um einmalig den verifizierten Core herunterzuladen
- Öffentliche VMESH-Wallet-Adresse \`vm1...\` für den ASIC, **niemals Seed Phrase / Private Key**

## Schnellstart – lokale Installation

\`\`\`bash
git clone https://github.com/ati1993de/vargamesh-minipool.git
cd vargamesh-minipool
bash start-docker.sh
\`\`\`

Das Skript prüft Docker/Compose, erzeugt bei Bedarf \`.env\` und startet \`docker compose up -d --build\`. Die Node synchronisiert im Docker-Volume \`vmesh_chain\`. Die Pool-Konfiguration und der Block-Audit-Log bleiben im Volume \`vmesh_config\` bestehen.

- Dashboard **auf dem Linux-Host**: http://127.0.0.1:8686
- Stratum **auf dem Linux-Host**: \`127.0.0.1:3938\`
- Logs: \`docker compose logs --tail=100 -f\`
- Status: \`docker compose ps\`

**Standardmäßig kein öffentlicher Zugang!** Der Pool ist zwar im Container auf Port 3938 erreichbar, Docker veröffentlicht ihn anfangs aber ausschließlich auf \`127.0.0.1\`.

## Bitaxe / ASIC im Heimnetz verbinden

Für einen Bitaxe im selben vertrauenswürdigen LAN setze in \`.env\` deine **tatsächliche private IPv4-Adresse des Linux-Hosts** ein:

\`\`\`env
STRATUM_BIND_IP=192.168.178.55
MINIPOOL_SHARE_DIFFICULTY=1024
\`\`\`

Das ist nur ein Beispiel. Ist die IP \`192.168.178.55\` bereits dein **Windows-PC**, muss hier die andere IP deines **Linux-Servers** eingetragen werden.

\`\`\`bash
docker compose -f compose.yaml -f compose.lan.yaml up -d --build
\`\`\`

Im Bitaxe unter **Primary Pool**:

| Option | Wert |
|---|---|
| Host | Private LAN-IP des Linux-Servers |
| Port | \`3938\` |
| Protokoll | Stratum V1, ohne TLS im vertrauenswürdigen LAN |
| Benutzer | \`vm1DEINE_GUELTIGE_ADRESSE.bitaxe01\` |
| Passwort | \`x\` |
| Schwierigkeit | \`1024\` |

Verwende eine Firewall-Regel, die Port 3938 **nur für den Bitaxe bzw. das private LAN** zulässt. **Nicht** den Stratum-Port ungeschützt auf dem öffentlichen VPS freigeben; für entfernte Miner WireGuard/VPN nutzen.

## Optional: Dashboard mit Nginx Proxy Manager (NPM)

*NPM* ist hier **Nginx Proxy Manager** – nicht das Node.js-Paketwerkzeug. MiniPool benötigt weder JavaScript-Paketverwaltung noch einen Node.js-Webserver.

1. In NPM eine **Access List** erstellen und Authentifizierung aktivieren; HTTPS für die gewünschte Subdomain einrichten.
2. Das tatsächliche Docker-Netzwerk deines bereits installierten NPM ermitteln: \`docker network ls\`. NPM und MiniPool müssen demselben Docker-Netzwerk angehören.
3. In \`.env\` eintragen (Beispiele anpassen):

   \`\`\`env
   NPM_DOCKER_NETWORK=npm_proxy
   MINIPOOL_DASHBOARD_ALLOWED_HOSTS=pool.example.com
   \`\`\`

4. \`docker compose -f compose.yaml -f compose.npm.yaml up -d --build\` ausführen.
5. In NPM Proxy Host: Domain \`pool.example.com\`, Forward Hostname \`vmesh-minipool\`, Scheme \`http\`, Port \`8686\`, HTTPS aktivieren. Nicht direkt den ungeschützten Port 8686 öffentlich freigeben.

**Datenschutz:** Das Dashboard zeigt öffentliche Wallet-Adressen der Miner, Worker-Namen, Shares und Logmeldungen. Nur hinter HTTPS und Authentifizierung veröffentlichen. NPM schützt **nicht den Stratum-Port**; diesen nur privat oder per VPN betreiben.

## Updates und Datensicherheit

\`\`\`bash
git pull --ff-only
docker compose up -d --build
docker compose logs -f
\`\`\`

Die Volumes bleiben erhalten, solange du nicht \`docker compose down -v\` ausführst. **Nie \`down -v\` ohne Sicherung**, das entfernt Blockchain- und Konfigurationsdaten. Zum Stoppen: \`docker compose down\` (Volumes bleiben erhalten). Für LAN oder NPM denselben Compose-Dateisatz wie beim Start verwenden.

Der VMESH-RPC-Port \`29667\` wird **nie** auf dem Host veröffentlicht. Die eigene Core-Node und MiniPool teilen den Container-Loopback (\`127.0.0.1\`) und nutzen die Cookie-Authentifizierung. Die Node muss synchronisiert sein, bevor der Pool VMESH-Jobs erstellt. BIP310-Version-Rolling und AxeOS-Blockhöhe sind kompatibel; die 1-%-VMESH-Entwicklergebühr bleibt Bestandteil der VMESH-Child-Coinbase.

## Bestehender VPS mit VMESH-Mainnet-Services?

**Nicht einfach auf deinen produktiven Mainnet-VPS loslassen**, wenn dort bereits VMESH-Pools und Nodes laufen. Standardports \`3938\` und \`8686\` müssen frei sein; Docker startet eine **zusätzliche** VMESH-Node mit eigenen Blockchain-Daten und benötigt mehr Speicher. Für den Mainnet-VPS wäre alternativ ein eigenständiger MiniPool am bestehenden Node per lokalem RPC sinnvoll – das ist ein anderer sicherer Deployment-Modus.

## Fehleranalyse

\`\`\`bash
docker compose ps
docker compose logs --tail=150 minipool
docker compose exec minipool python3 -c "from minipool.rpc import VMeshRPC; print(VMeshRPC('/data/.cookie').call('getblockchaininfo'))"
\`\`\`

- \`Node synchronizing\`: abwarten; noch keine Mining-Jobs.
- \`Connection refused\`: Core startet erst oder eine andere Instanz blockiert einen Port.
- \`404\`/Core-Downloadfehler: offizielle GitHub-Release-Verfügbarkeit prüfen.
- \`permission denied\`: Docker-Volumes sollten für Container-User UID 10001 beschreibbar sein.
- Kein Miner: Firewall, Docker-Host-LAN-IP, Stratum-V1-Einstellungen und Fallback-Konfiguration prüfen.
