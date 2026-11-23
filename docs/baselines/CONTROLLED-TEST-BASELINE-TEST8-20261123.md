# Controlled device-test baseline TEST8 — 2026-11-23

Baseline ID: `PG-CR-0.1.0-TEST8-20261123`

## Scope

This freezes the clean-room TEST8 fullscreen-wake and task-isolation repair,
its unsigned APK, and the separately signed controlled-test APK physically
verified on the Onn tablet. TEST1 through TEST7 artifacts remain preserved.
No private catalog media, bridge address, receiver credential, pairing state,
tunnel credential, signing secret, or author-derived implementation is present
in this baseline or its APKs.

## Reason for TEST8

Cross-device presentation testing passed on a Galaxy S7, Galaxy S9+, Pixel,
and Onn tablet, but Android briefly exposed its status and navigation controls
during dark-screen wake on the S9+ and Onn. The Onn also returned to the
configuration screen after one reaction, indicating that Android could reuse
or reveal the application's setup task around the full-screen reaction.

## Repair

- Apply fullscreen window flags before `Activity.onCreate`.
- Use `WindowInsetsController` on Android 11 and later while retaining the
  legacy immersive flags required by Android 8 through 10.
- Disable status/navigation contrast enforcement where supported.
- Disable the activity-open transition and immediately re-hide system bars if
  Android exposes them during a visibility change.
- Reapply immersive mode on attachment, resume, post-resume, and focus.
- Launch the reaction activity in a separate, no-history task affinity with
  clear-task and no-animation flags, then remove that task after completion.
  The configuration activity is not part of that disposable reaction task.

## Verification

- Python/source/contract suite: 57 tests passed after the final TEST8 source
  change.
- Android debug and release timing/state suites: 10 tests passed per variant.
- Debug and release lint: clean.
- Debug and release APK assembly: passed.
- Package: `org.solpeanutgallery.receiver.test`.
- Version: `0.1.0-test8` (`versionCode` 7).
- Android: minimum API 26; target API 35.
- Unsigned APK SHA-256:
  `04f92f8a002b4e507b62539f892baab3e1cad2f347cd395e86e2e759512eb247`.
- Stable-signed APK SHA-256:
  `1604ba16a808c192c58d699f645eb497bdc6ed7b9111b73ae02ba8c1affcec35`.
- Signing certificate SHA-256:
  `d4db28246b5d4b18bca5ded7c913609a2d2e49d713dce58f7ff1bf349032ce0c`.
- APK Signature Schemes v2 and v3: verified.
- APK contents: application code/resources and signature metadata only; no
  operator media, catalog, endpoint, credential, log, or private key.

## Physical result

The stable-signed APK installed in place over TEST7 on the Onn tablet while
preserving pairing and listener state. Two normal-chat emoji reactions opened
from a dark screen, displayed once, acknowledged once, returned the display to
dark, and left the configuration screen closed. With gesture navigation plus
window and transition animations disabled, the former obvious system-bar flash
was reduced to at most a momentary single-frame flicker. The durable queue was
empty after each completion.

## Source freeze

`SOURCE-MANIFEST-TEST8-20261123.sha256` records every tracked source, contract,
document, wrapper, test, and verification-metadata file except itself. The
deterministic source archive and SHA-256 sidecar are stored with the controlled
device-test artifacts. Rebuilding the archive twice must produce identical
bytes before this freeze is considered complete.

## Remaining gates

- Repeat the functional matrix on the intended inexpensive dedicated receiver
  after it arrives.
- Produce, independently verify, document, and publish a separately signed
  release APK; the controlled-test signing identity is not a public release
  identity.
