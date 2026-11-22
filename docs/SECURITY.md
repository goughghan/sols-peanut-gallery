# Security boundary

## Never commit

- Tunnel or API keys.
- Pairing and receiver tokens.
- Android signing keys or passwords.
- Operator IP addresses, hostnames, logs, or state databases.
- Private catalogs, media, captions, or family information.

## Required controls

- Short-lived one-time pairing codes.
- Random revocable receiver credentials.
- Authenticated queue and media access.
- Strict request, caption, duration, size, MIME, and dimension bounds.
- Content hashes checked after download.
- No untrusted redirects or arbitrary remote media URLs in version 1.
- Idempotent requests and persistent ordered delivery.
- Least-privilege service accounts and operating-system credential storage.
- Secret scanning before every public release.

## Implemented controls

- Bridge receiver tokens are generated with the operating-system CSPRNG and
  only SHA-256 digests are stored in the owner-only SQLite state database.
- The administrator token is read only from the systemd credential directory;
  configuration and environment variables cannot carry it.
- Android encrypts its receiver token with a non-exportable Android Keystore
  AES-GCM key and opts all app state out of backup/device transfer.
- HTTP bodies, text, captions, queues, media bytes, dimensions, decoded pixel
  counts, GIF frames, and display times are bounded.
- Media IDs map only to validated catalog entries. The bridge and receiver
  reject unsafe paths, untrusted redirects, signature/MIME mismatch, changed
  lengths, changed hashes, and changed decoded dimensions.
- Completion acknowledgments must match the delivery ID, sequence, and receiver
  that claimed the oldest unfinished queue item.

The bridge supports plain local HTTP for isolated networks because Android 8
devices may need it. Bearer credentials are observable on an untrusted LAN;
operators must use HTTPS or a separately reviewed protected local transport in
that environment.

Security reports should eventually use a private contact method documented in
the public repository rather than a public issue containing exploit details.
