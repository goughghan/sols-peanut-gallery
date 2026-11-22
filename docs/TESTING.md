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
pending ARMv7/Pi service, tunnel, or complete host-reboot tests.

## Still pending

- Multi-hour clean-room idle delivery.
- Supervisor recovery after bridge child failure.
- Tunnel process recovery and a complete Linux host reboot.
- The full matrix on the intended inexpensive older Android receiver.
- A separately signed, verified public release APK.

These results support an alpha source publication. They do not claim stable
release readiness or universal Android/GIF compatibility.
