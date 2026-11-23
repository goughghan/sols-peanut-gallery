# Acceptance matrix

## Automated contract tests

- One-time pairing code expires and cannot be reused.
- Invalid receiver credentials are rejected.
- Duplicate request IDs do not create duplicate queue records.
- Concurrent requests receive stable ordering.
- Restarting the bridge preserves undelivered records.
- A receiver acknowledges only the reaction it actually finished.
- JPEG and GIF integrity checks accept valid fixtures and reject altered bytes.
- Oversized files, incorrect MIME types, redirects, and traversal attempts fail.
- An empty catalog still permits text and emoji reactions.
- No test writes credentials or private media into build artifacts.
- Receiver battery reports reject extra fields and out-of-range percentages.
- Status-observer credentials cannot perform administrator operations.
- Low-battery alerts deduplicate, ignore stale reports, and re-arm only after
  charging or recovery above the hysteresis threshold.

## Device acceptance tests

| Test | Required result | Current alpha evidence |
|---|---|---|
| Text and emoji | Full reaction appears and closes on schedule | Pass on Android 10 S9+ |
| JPEG | Correct image and caption appear in landscape | Pass on Android 10 S9+ |
| GIF | Animation loops, caption remains readable, close occurs on boundary | Pass with short and long operator-library controls |
| Burst of three | All three appear once, in order, without overlap | Pass on TEST3 |
| Android reboot | Listener resumes without opening the app | Pass on TEST3 |
| Wi-Fi interruption | Queued reaction arrives after reconnection | Pass on TEST3 and deployed clean-room TEST7; one delivery acknowledged after reconnect |
| Bridge child failure | Supervisor restores delivery automatically | Pass on deployed clean-room Pi service; post-recovery reaction acknowledged |
| Tunnel failure | Service manager restores bridge and tunnel | Pass on deployed ARMv7 tunnel; MCP reinitialized and reaction acknowledged |
| Pi network interruption | Bridge and tunnel recover after link restoration without operator action | Pass on deployed Pi; processes survived, tunnel reconnected, and post-recovery reaction was acknowledged |
| Linux host reboot | Both components start without manual secret entry | Pass on deployed Pi; new boot verified, MCP tunnel recovered, S9+ resumed polling, and reaction acknowledged |
| Long idle | Reaction arrives after an agreed multi-hour idle period | In progress |
| Older target phone | Full matrix passes on the intended inexpensive device | Pending target-device arrival |
| Battery heartbeat | Desktop receives one low-battery alert without delivery authority | Source-only simulation pending physical test |

The sanitized observations behind these status entries are recorded in
[`TESTING.md`](TESTING.md). A pass on one controlled device does not replace
the remaining target-device and deployment acceptance gates.

## Release gates

- Clean source checkout builds without private workspace files.
- APK contains no operator media, credentials, private addresses, or logs.
- Dependency and provenance review passes.
- GPL notice, AI-development disclosure, and inspiration acknowledgment are
  visible.
- Release APK signature and published checksum are independently verified.
