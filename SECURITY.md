# Security policy

**VMESH MiniPool v0.1.0 is a developer preview, not yet externally audited or proven with a successful mainnet block.**

- Keep VargaMesh RPC cookie and JSON config private; the node RPC is always loopback (`127.0.0.1`).
- Open Stratum only on trusted LANs. Plain Stratum V1 traffic is not encrypted.
- Do not expose the local dashboard or VMESH node RPC directly to the Internet.
- Download official Core binaries from the project's GitHub Releases, verify checksums, and never execute binaries supplied via unsolicited messages.
- Do not put wallet seed phrases or wallet private keys into MiniPool settings.
- Treat all third-party miners, accepted shares and coinbase accounting as untrusted until audited.

Please report reproducible vulnerabilities privately to the VargaMesh project maintainer rather than publishing secrets or exploitable account information.
