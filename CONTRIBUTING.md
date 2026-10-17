# Contributing

Contributions focused on SHA-256d Stratum compatibility, VMESH-only AuxPoW block acceptance testing, Windows usability, performance and security are welcome. Open an issue explaining the reproducer and expected/actual behavior. Submit PRs with Python standard-library unit tests where possible.

Run `python -m unittest discover -v` before opening a PR. Do not include real `.cookie` files, passwords, wallet seeds, server addresses, or block reward guarantees in fixtures. Any changes to developer fee calculations or payout ordering must be explicit and tested.
