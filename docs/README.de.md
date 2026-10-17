# VargaMesh MiniPool – VMESH SOLO Pool für Bitaxe und SHA-256d ASICs

**Eigene VMESH-Blöcke mit dem eigenen Computer und eigener VargaMesh-Node finden.** Kein BTC-Full-Node, keine BTC-Auszahlung, kein zentraler Mining-Account.

> **Entwickler-Vorschau v0.3.1:** Die lokalen Tests sind erfolgreich. Ein echter Mainnet-Blockfund mit einem ASIC wurde für diese Version noch nicht nachgewiesen.

## Linux Docker Compose – VMESH-Node direkt enthalten

**Neu in v0.3.0:** `bash start-docker.sh` erstellt ein Docker-Image mit dem offiziellen, SHA-256-verifizierten VMESH-Core v0.2.0 und startet die eigene VMESH-Mainnet-Node, SOLO-Stratum und das Dashboard zusammen. Die Blockchain verbleibt in Docker-Volumes. Optionaler LAN-Zugang für Bitaxe und Nginx Proxy Manager (NPM) für ein authentifiziertes HTTPS-Dashboard sind dokumentiert. Es ist **kein Bitcoin-Core** und **kein Node.js/npm** notwendig.

**[Vollständige Docker-/Linux-/NPM-Installationsanleitung](DOCKER.de.md)**

## Windows: VMESH-Node und SOLO-Pool mit einem Klick

1. Beim [offiziellen GitHub Release v0.3.1](https://github.com/ati1993de/vargamesh-minipool/releases/tag/v0.3.1) die Datei **VargaMesh-MiniPool-Windows-x64.zip** herunterladen, vollständig entpacken und **VargaMesh-MiniPool.exe** starten. Dort gibt es auch eine **SHA-256-Prüfsumme** und den Quellcode. Für neuere Entwickler-Versionen alternativ [GitHub Actions](https://github.com/ati1993de/vargamesh-minipool/actions/workflows/windows.yml) verwenden. Bei der Release-EXE ist kein Python erforderlich.
2. Auf **ONE CLICK: Install VMESH Node & Start Pool** klicken.
3. MiniPool lädt den **offiziellen VargaMesh Core v0.2.0** und überprüft die fest eingebauten SHA-256-Prüfsummen für Manifest und Core-Archiv. Die Node wird in einem separaten Benutzerordner installiert. **Kein Bitcoin-Core erforderlich.**
4. Die eigene VMESH-Mainnet-Node startet und synchronisiert. Den Fortschritt zeigt die Oberfläche an. **Erst nach vollständiger Synchronisierung startet der VMESH-SOLO-Stratum-Server automatisch.**
5. Die **öffentliche vm1... Wallet-Adresse** eingeben und **Copy Bitaxe settings** klicken. Diese Verbindungsdaten in den Bitaxe oder anderen ASIC eintragen. Keine Seed-Phrase oder Private Keys erforderlich.

**Sicherheit:** Die App installiert Core nur nach Nutzerklick. RPC ist ausschließlich lokal gebunden. Stratum für das Heimnetz nur durch die private Windows-Firewall freigeben. Die Windows-EXE ist unsigniert. Kein echter Mainnet-Blockfund mit ASIC ist für diesen Entwickler-Preview nachgewiesen. Die integrierte 1-%-VMESH-Gebühr wird direkt in der Coinbase-Transaktion abgezogen, nicht durch Blockchain-Konsens.

| Miner-Einstellung | Beispiel |
|---|---|
| Stratum | `stratum+tcp://192.168.1.50:3938` |
| Username | `vm1DEINE_GUELTIGE_VMESH_ADRESSE.bitaxe1` |
| Passwort | `x` |

**99% der gesamten VMESH-Coinbase-Auszahlung** gehen an die hinterlegte gültige VMESH-Adresse. Die feste **1% Entwicklergebühr** geht an `vm1qsfsgj70pdv86nguvexzvsflmcknz4lrsj87wx9`. Die Ausgabe wird direkt als zweite Coinbase-Ausgabe erstellt. Das ist **keine** Gebühr des VMESH-Konsensprotokolls.

## Download überprüfen

Beim [GitHub Release v0.2.3](https://github.com/ati1993de/vargamesh-minipool/releases/tag/v0.2.3) sowohl `VargaMesh-MiniPool-Windows-x64.zip` als auch `SHA256SUMS-MiniPool-Windows` herunterladen. Unter PowerShell mit `Get-FileHash -Algorithm SHA256 .\VargaMesh-MiniPool-Windows-x64.zip` den SHA-256-Wert ermitteln und mit der Prüfsummen-Datei vergleichen. Der offizielle VMESH-Node wird **separat und erst nach Nutzerklick** heruntergeladen und mit fest hinterlegten Prüfsummen geprüft.

## Warum funktioniert das ohne Bitcoin-Node?

VMESH benötigt auf Mainnet einen AuxPoW-Nachweis. MiniPool erstellt dafür einen synthetischen SHA-256d-Parent-Header mit VMESH-Commitment. Der Miner berechnet dessen SHA-256d-PoW. Ein Erfolg wird ausschließlich als VMESH-Block an `vargameshd` eingereicht. Es werden keine Bitcoin-Blöcke geschürft und keine BTC-Transaktionen erstellt.

## AxeOS „Block Header“ leer / „Failed to process mining notification“ (v0.2.3)

**Behoben:** AxeOS erwartet beim Auslesen der Stratum-V1-Coinbase eine BIP34-artig kodierte Blockhöhe **direkt am Anfang der ScriptSig**. Die synthetische Parent-Coinbase des MiniPools begann bisher mit `/VMESH/`. AxeOS interpretierte das erste Zeichen `/` als Länge `47` statt als echte Blockhöhenangabe und zeigte `Height`, `Difficulty`, `Scriptsig`, `Amount` teilweise leer, obwohl Mining-Shares bereits erfolgreich waren.

MiniPool v0.2.3 stellt jetzt eine **VMESH-Child-Blockhöhe in BIP34-kompatibler Form** an den Anfang der synthetischen Parent-Coinbase. **Das ist keine Bitcoin-Höhe!** Keine Änderung an der eigentlichen VMESH-Blockchain, der 99/1-VMESH-Coinbase-Aufteilung oder deiner synchronisierten Node. AxeOS kann für `Amount` weiterhin `0` anzeigen: Der Parent-Block schüttet keine BTC aus. Die echten VMESH-Rewards stehen im Child-Block und sind über den VMESH-Explorer prüfbar.

**„Using fallback pool“ ist separat:** Falls MiniPool als Fallback konfiguriert ist, kann AxeOS darüber trotzdem erfolgreich VMESH minen. Möchtest du ihn dauerhaft nutzen, stelle die MiniPool-LAN-IP als Primary Pool ein und prüfe die Fallback-Konfiguration.

## Bitaxe-Fix v0.2.3: Keine „Low difficulty“- und falschen Duplikatfehler mehr

Die vorherige Version hat bei der Berechnung des synthetischen Parent-Blockhashs `extranonce1` nicht gemäß **Stratum V1** eingesetzt. Deshalb berechneten der Bitaxe und MiniPool **unterschiedliche Hashes**: Selbst eigentlich gültige ASIC-Shares konnten als „Low difficulty share“ abgelehnt werden.

v0.2.3 verwendet nun korrekt `coinb1 + extranonce1 + extranonce2 + coinb2` — der Bitaxe und der Server berechnen damit die gleiche Parent-Coinbase. **Duplikate werden erst nach erfolgreicher Share-Schwierigkeitsprüfung registriert.** Die eingestellte Share Difficulty **1024 vorerst beibehalten**, MiniPool aktualisieren, den alten Pool schließen und Bitaxe neu verbinden. Dann prüfen, ob **akzeptierte Shares steigen**.

Die bereits vorhandene BIP310-Version-Rolling-Unterstützung bleibt erhalten. Die VMESH-Child-Chain und die **1-%-Entwicklergebühr** bleiben unverändert.

## Bitaxe-Fix v0.2.1: BIP310 Version Rolling

Der MiniPool beantwortet jetzt `mining.configure` korrekt und erlaubt **BIP310-Version-Rolling mit sicherer Maske `1fffe000`** für den synthetischen AuxPoW-Parent-Header. Nur dieser Parent-Header wird verändert; **VMESH-Child-Header, Blockchain-Regeln und 1-%-Entwicklergebühr bleiben unverändert**.

Erscheint beim Bitaxe **„Version rolling not supported (100 %)“**, verwende v0.2.3 und starte den MiniPool neu. Der Miner sollte danach die Stratum-Verbindung neu aufbauen; falls nicht, Bitaxe einmal neu starten.

Steht dort **„Using fallback pool“**, läuft der Miner nicht über den gewünschten Primary-Pool. Unter **Pool Settings** den **Primary Pool** auf den Windows-PC mit MiniPool setzen: Host beispielsweise `192.168.178.55`, Port `3938`, Stratum V1, Username `vm1DEINE_GUELTIGE_ADRESSE.bitaxe01`, Password `x`. Fallback separat überprüfen oder deaktivieren. Die beiden Meldungen können gleichzeitig auftreten, sind aber unterschiedliche Ursachen.

Mit ca. 477 GH/s und Schwierigkeit 1024 kommen Shares im Mittel ungefähr alle 9 Sekunden; tatsächliche Abstände schwanken. Die Anzahl gefundener VMESH-Blöcke bleibt zufallsabhängig.

## Sicherheit

- Nur im vertrauenswürdigen LAN betreiben; Stratum V1 ist unverschlüsselt.
- VargaMesh-RPC nur lokal `127.0.0.1:29667` anbinden. `.cookie` niemals teilen.
- Der Pool benötigt keine Seed-Phrase und keinen privaten Wallet-Schlüssel.
- Den vollständigen [englischen README](../README.md) und die [Architektur](ARCHITECTURE.md) vor dem Produktivbetrieb lesen.
