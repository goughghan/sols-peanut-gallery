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

## Device acceptance tests

| Test | Required result | Current alpha evidence |
|---|---|---|
| Text and emoji | Full reaction appears and closes on schedule | Pass on Android 10 S9+ |
| JPEG | Correct image and caption appear in landscape | Pass on Android 10 S9+ |
| GIF | Animation loops, caption remains readable, close occurs on boundary | Pass with short and long operator-library controls |
| Burst of three | All three appear once, in order, without overlap | Pass on TEST3 |
| Android reboot | Listener resumes without opening the app | Pass on TEST3 |
| Wi-Fi interruption | Queued reaction arrives after reconnection | Pass on TEST3 |
| Bridge child failure | Supervisor restores delivery automatically | Pending supervised deployment test |
| Tunnel failure | Service manager restores bridge and tunnel | Pending supervised deployment test |
| Linux host reboot | Both components start without manual secret entry | Pending supervised deployment test |
| Long idle | Reaction arrives after an agreed multi-hour idle period | In progress |
| Older target phone | Full matrix passes on the intended inexpensive device | Pending target-device arrival |

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
