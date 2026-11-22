# Linux deployment material

This directory contains a reviewed but inactive service layout, credential-free
configuration example, hardened systemd template, and read-only Pi preflight.
Nothing here installs, enables, starts, stops, or restarts a live service.

## Reference host

The reference deployment target is a Raspberry Pi 2 Model B Rev 1.1 running
32-bit Raspberry Pi OS (`armv7l` kernel and Debian `armhf` packages) with
approximately 1 GB of RAM. The bridge has no third-party Python runtime
dependency or native extension: it uses Python 3.9+ standard-library HTTP,
JSON, hashing, SQLite, and filesystem APIs.

The same code can run on newer ARM or x86-64 Linux hosts. The Pi 2 target is a
compatibility goal, not a requirement for other operators. Physical Pi 2
service, tunnel-recovery, and complete host-reboot acceptance remain pending.

## Files

- `bin/pi-preflight.sh` performs a read-only compatibility inventory.
- `bin/create-layout.sh` prints the proposed service account and directories by
  default; `--apply` changes a host only after separate review and approval.
- `config/bridge.example.json` is bounded non-secret configuration.
- `systemd/sol-peanut-gallery.service.in` is inactive until every placeholder
  is resolved during a controlled installation.

## Proposed target layout

```text
/opt/sol-peanut-gallery/       versioned application and virtual environment
/etc/sol-peanut-gallery/       root-controlled non-secret configuration
/var/lib/sol-peanut-gallery/   queue, pairing, catalog, and runtime state
/var/log/sol-peanut-gallery/   optional bounded logs
```

The service runs as the dedicated unprivileged `sol-peanut-gallery` account.
Its administrator token must be supplied by `LoadCredentialEncrypted`; it must
not appear in JSON, environment files, command arguments, repository history,
or logs.

See `docs/OPERATIONS.md` for the controlled install, upgrade, recovery, and
removal procedure. None of those steps has been run on the live host.
