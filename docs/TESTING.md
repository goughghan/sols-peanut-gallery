# Controlled testing record

This document summarizes sanitized physical observations for the independent
clean-room receiver. It contains no private catalog media, endpoint, network
address, pairing state, credential, signing material, or operator log.

## Controlled environment

- Date: 2026-11-22
- Receiver: Samsung Galaxy S9+, Android 10
- Build: `0.1.0-test3`, package `org.solpeanutgallery.receiver.test`
- Bridge: isolated clean-room process and state directory
- Media: deliberately created fixture JPEG/GIF files plus two unchanged
  operator-library GIF controls; no media is included in this repository

The controlled package used a separate application identity and signing
identity so it could not replace the private feasibility receiver. The live Pi,
tunnel, private plugin, private catalog, and quarantined prototype were outside
this test boundary.

## Passed observations

- One-time pairing and authenticated polling.
- Text, captions, and Android-10-supported emoji.
- JPEG download, hash verification, immersive landscape display, and timed
  close.
- A real 80-frame, 5.32-second GIF repeated for the requested display interval
  without visible overlap.
- A real 12-frame, 0.6-second GIF repeated for the requested display interval
  without visible overlap.
- Three back-to-back reactions appeared exactly once and in queue order after
  TEST3's active-delivery identity repair.
- Full-screen reactions launched silently from a dark screen without a visible
  heads-up banner, then optional device administration turned the display off.
- An in-place package update retained pairing and listener state and resumed
  polling without the app being opened.
- A reaction queued while Wi-Fi was disabled arrived once after reconnection.
- After an Android reboot, the listener resumed without the app being opened;
  a dark-screen reaction appeared once, showed no banner, acknowledged once,
  and returned the display to dark.
- The receiver reconnected after an isolated bridge restart.

## Compatibility findings

- One newer Unicode emoji lacked a glyph in the S9+'s Android 10 system font.
  The transport and display path worked; a curated compatible emoji subset or
  redistributable fallback font remains a possible hardening item.
- Two synthetic GIFs produced by the diagnostic image tool showed composited
  frame overlap through Android's platform `Movie` decoder even after explicit
  canvas clearing. Both representative operator-library GIF classes rendered
  correctly. Arbitrary third-party GIFs may therefore need catalog preflight
  or normalization before a stable release.

## Deployed clean-room integration

On 2026-11-22, the independent bridge, ARMv7 tunnel client, and receiver build
`0.1.0-test7` were exercised together on the Raspberry Pi 2 and Android 10
S9+. The author-derived feasibility prototype remained quarantined and was not
used by these deliveries.

- A normal ChatGPT conversation discovered the clean-room MCP tools through the
  secure tunnel and queued an emoji/caption reaction. The receiver displayed it,
  acknowledged it once, and resumed polling.
- The same normal conversation called `find_display_items` and then
  `queue_display` for a catalog JPEG and a catalog GIF. Both verified media
  downloads displayed successfully and produced matching completion
  acknowledgments. The GIF completed four whole loops before closing, as
  required by the receiver timing policy.
- Sending `SIGKILL` to the bridge child caused systemd to restart it after the
  configured five-second delay. The receiver resumed polling and a subsequent
  tunneled reaction displayed and acknowledged successfully.
- Sending `SIGKILL` to the tunnel child caused systemd to restart it after the
  configured five-second delay. The replacement process reinitialized its MCP
  session and control-plane poller, then delivered and acknowledged a subsequent
  normal-chat reaction without operator credential entry.
- A reaction queued while the S9+ Wi-Fi connection was disabled remained
  pending in SQLite. After Wi-Fi was restored, the receiver claimed, displayed,
  and acknowledged it once; the queue then returned to empty polling.
- During a physical Pi Ethernet interruption, the tunnel recorded repeated
  control-plane timeouts while the bridge and tunnel processes remained active.
  After the cable was reconnected, the same processes recovered without
  operator action. A new normal-chat reaction traversed the recovered tunnel,
  displayed once, acknowledged successfully, and left no pending delivery.
- A complete Pi reboot produced a new kernel boot identity. The bridge and
  tunnel services started automatically without operator credential entry. The
  tunnel retried while the bridge completed its slower startup, then initialized
  its MCP session; the S9+ resumed polling. A new normal-chat reaction displayed
  once, acknowledged successfully, and left the durable queue empty. No systemd
  units were failed after the test.
- After both supervised failures, the bridge and tunnel services remained
  active and the receiver continued empty-queue polling.

## Public clean-checkout smoke test

On 2026-11-22, a new shallow clone of the public `main` branch was tested in a
disposable directory with no private workspace files or retained build state:

- All 41 public Python, contract, security, deployment, and source-boundary
  tests passed; the two optional ignored-artifact checks skipped as designed.
- The bridge wheel built from the repository root and installed into a new
  virtual environment with no runtime dependency.
- The installed entry point reported version `0.1.0`.
- The empty example catalog validated successfully.
- Initial state creation produced an owner-only SQLite database.
- A live isolated bridge returned HTTP 200 from `/healthz` and rejected an
  unauthenticated administrator request with HTTP 401.
- The deployment layout script reported dry-run mode and made no system
  changes.

GitHub Actions independently builds the bridge wheel and both Android APK
variants from a separate clean checkout. This smoke test does not replace the
remaining physical-device acceptance matrix.

## Still pending

- Multi-hour clean-room idle delivery.
- The full matrix on the intended inexpensive older Android receiver.
- A separately signed, verified public release APK.

These results support an alpha source publication. They do not claim stable
release readiness or universal Android/GIF compatibility.
