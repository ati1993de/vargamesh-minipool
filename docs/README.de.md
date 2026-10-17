# VargaMesh MiniPool – VMESH SOLO Pool für Bitaxe und SHA-256d ASICs

**Eigene VMESH-Blöcke mit dem eigenen Computer und eigener VargaMesh-Node finden.** Kein BTC-Full-Node, keine BTC-Auszahlung, kein zentraler Mining-Account.

> **Entwickler-Vorschau v0.1.0:** Die lokalen Tests sind erfolgreich. Ein echter Mainnet-Blockfund mit einem ASIC wurde für diese Version noch nicht nachgewiesen.

## Windows-Schnellstart

1. Offiziellen [VargaMesh Core](https://github.com/ati1993de/vargamesh-core/releases) für Windows herunterladen, Prüfsumme kontrollieren und entpacken.
2. Python 3.10+ installieren, dann `start-windows.bat` doppelklicken. Alternativ die Windows-EXE erst nach dem GitHub-Actions-Build verwenden.
3. Im Programm `vargameshd.exe` auswählen und auf **Start VargaMesh Node** klicken. Vollständige Synchronisierung abwarten.
4. **Start SOLO Pool** klicken und das Dashboard im Browser öffnen (`http://127.0.0.1:8686`).
5. Bitaxe oder anderen SHA-256d-Miner auf die LAN-IP des PCs und Port `3938` konfigurieren.

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
