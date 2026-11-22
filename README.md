# Sol's Peanut Gallery

[![Contract checks](https://github.com/goughghan/sols-peanut-gallery/actions/workflows/contracts.yml/badge.svg?branch=main&event=push)](https://github.com/goughghan/sols-peanut-gallery/actions/workflows/contracts.yml)

Sol's Peanut Gallery is a self-hosted message-and-media display system for
showing short text, emoji, JPEG, and animated GIF reactions on a paired Android
device. A small private bridge accepts authenticated tool calls, preserves
their order in SQLite, and delivers them at least once until the receiver sends
a matching completion acknowledgment.

## Project status

This repository is an independent `0.1.0-alpha` clean-room source preview. The
bridge and Android receiver pass their automated build, test, lint, privacy,
and contract checks. Controlled testing on an Android 10 Galaxy S9+ has passed
text, emoji, JPEG, real-world animated GIF, ordered burst, Wi-Fi interruption,
package-update recovery, phone-reboot recovery, immersive display, and
automatic screen-off cases.

Long-idle testing, supervised bridge/tunnel/Linux-host recovery, and the full
matrix on the intended inexpensive Android device remain open. No public APK
is released yet. See [the testing record](docs/TESTING.md) for the exact scope
and known compatibility findings.

## Reference hardware

The project's reference bridge host is a Raspberry Pi 2 Model B Rev 1.1 with
approximately 1 GB of RAM, running 32-bit Raspberry Pi OS (`armv7l`/`armhf`).
The bridge is intentionally written for Python 3.9+ using only the standard
library and SQLite at runtime, so its published wheel is architecture-neutral
and remains suitable for ARMv7 instead of requiring a newer 64-bit Pi.

The clean-room bridge has passed public x86-64 build and runtime smoke tests;
its complete service, tunnel, and reboot acceptance test on the physical Pi 2
is still pending and is not claimed as complete.

## What is implemented

- Short-lived, one-time pairing codes and revocable receiver credentials.
- Receiver credentials encrypted with Android Keystore and bridge credentials
  loaded from the operating system's credential directory.
- Durable SQLite ordering, request idempotency, restart persistence, bounded
  queues, and explicit displayed/dismissed/failed acknowledgments.
- Authenticated text/emoji, catalog search, catalog queueing, delivery, media,
  pairing, and revocation endpoints.
- An empty operator catalog that keeps text and emoji fully useful.
- Strict local-media paths plus byte, signature, MIME, dimension, decoded-pixel,
  and SHA-256 validation. Remote media URLs and redirects are not supported.
- Android 8.0+ foreground listening, reboot/update recovery, reconnect backoff,
  immersive landscape display, GIF loop-aware timing, and optional device-admin
  screen-off behavior.

## Assistants and automations

The project is not tied to ChatGPT, OpenAI, or any other model or service. An
operator can connect ChatGPT, Claude, a local model, Home Assistant, Node-RED,
monitoring software, or an ordinary script by placing a small trusted adapter
in front of the bridge's authenticated HTTP API.

[`contracts/mcp-tools.json`](contracts/mcp-tools.json) describes the optional
assistant-facing tools: `find_display_items` searches operator-owned catalog
metadata and `queue_display` queues a bounded caption, emoji, or catalog
reaction. The same bridge endpoints can be used without MCP. The repository
does not prescribe an assistant provider, tunnel service, hosting machine,
media library, or trigger policy.

See [the integration guide](docs/INTEGRATIONS.md) for the trust boundary and a
provider-neutral setup outline. A successful queue response means accepted for
delivery; it does not by itself prove that the reaction appeared on screen.

## Media and secret boundary

The repository and base APK contain no private memes, photographs, GIF
collections, operator catalog, bridge address, pairing state, or working
credential. Operators provide media they have the right to use in a separate
catalog directory. Signing keys and transport credentials stay outside source
control.

## Build and test

See [docs/BUILD.md](docs/BUILD.md) for pinned, reproducible commands. The short
form from the repository root is:

```text
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m pip wheel --no-deps --wheel-dir dist .

cd android
./gradlew --no-daemon clean assembleDebug testDebugUnitTest lintDebug
```

The Android build requires JDK 17 and Android SDK 35/build-tools 35.0.0. The
checksum-pinned wrapper supplies Gradle 8.9; Android Gradle Plugin 8.7.3 and
downloaded dependency hashes are pinned in the project.

## Documentation

- [Bridge operation](bridge/README.md)
- [Android receiver](android/README.md)
- [Build and verification](docs/BUILD.md)
- [Installation, upgrade, recovery, and removal](docs/OPERATIONS.md)
- [Security boundary](docs/SECURITY.md)
- [Assistant and automation integrations](docs/INTEGRATIONS.md)
- [Dependencies and licenses](docs/DEPENDENCIES.md)
- [Acceptance matrix](docs/ACCEPTANCE.md)
- [Controlled testing record](docs/TESTING.md)
- [Clean-room provenance](docs/PROVENANCE.md)

## Development and AI assistance

This project was conceived, directed, tested, and maintained by Will. ChatGPT
assisted with architecture, clean-room implementation, debugging methodology,
documentation, and test development. All project decisions and public releases
are human-reviewed.

This is an independent community project and is not an official OpenAI product.

## Acknowledgments

Inspired by the proof of concept demonstrated by
[`rsms/esp32-dot`](https://github.com/rsms/esp32-dot). This is an independent
implementation developed from documented requirements and black-box acceptance
criteria. No source code, artwork, or assets from that project are included.

## License

New original source code is licensed under `GPL-3.0-or-later`; see [LICENSE](LICENSE).
Private operator media, third-party tools, dependencies, names, and logos are
not automatically covered by that license.
