# VargaMesh MiniPool – VMESH SOLO Pool für Bitaxe und SHA-256d ASICs

**Eigene VMESH-Blöcke mit dem eigenen Computer und eigener VargaMesh-Node finden.** Kein BTC-Full-Node, keine BTC-Auszahlung, kein zentraler Mining-Account.

> **Entwickler-Vorschau v0.1.0:** Die lokalen Tests sind erfolgreich. Ein echter Mainnet-Blockfund mit einem ASIC wurde für diese Version noch nicht nachgewiesen.

## Windows: VMESH-Node und SOLO-Pool mit einem Klick

1. Auf [GitHub Actions – Windows](https://github.com/ati1993de/vargamesh-minipool/actions/workflows/windows.yml) einen erfolgreichen Build öffnen und das ZIP-Artefakt **VargaMesh-MiniPool-Windows-x64** herunterladen. Entpacken und **VargaMesh-MiniPool.exe** starten. Alternativ Python 3.10+ installieren und **start-windows.bat** aus dem Quellcode starten.
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

## Warum funktioniert das ohne Bitcoin-Node?

VMESH benötigt auf Mainnet einen AuxPoW-Nachweis. MiniPool erstellt dafür einen synthetischen SHA-256d-Parent-Header mit VMESH-Commitment. Der Miner berechnet dessen SHA-256d-PoW. Ein Erfolg wird ausschließlich als VMESH-Block an `vargameshd` eingereicht. Es werden keine Bitcoin-Blöcke geschürft und keine BTC-Transaktionen erstellt.

## Sicherheit

- Nur im vertrauenswürdigen LAN betreiben; Stratum V1 ist unverschlüsselt.
- VargaMesh-RPC nur lokal `127.0.0.1:29667` anbinden. `.cookie` niemals teilen.
- Der Pool benötigt keine Seed-Phrase und keinen privaten Wallet-Schlüssel.
- Den vollständigen [englischen README](../README.md) und die [Architektur](ARCHITECTURE.md) vor dem Produktivbetrieb lesen.
