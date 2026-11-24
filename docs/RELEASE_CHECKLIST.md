# Public release checklist

## Provenance and licensing

- [x] Every executable file was authored in the clean-room tree.
- [x] No private prototype or unlicensed-project source was consulted during
      implementation.
- [x] Dependencies and bundled notices have been reviewed.
- [x] GPL license identifiers and the root license file are present.
- [x] Inspiration credit does not imply endorsement or included source.

## Privacy and secrets

- [x] Initial public repository history contains no tunnel keys, tokens, pairing state,
      signing material, private addresses, unintended personal details, or
      logs.
- [x] Repository and locally built debug APK contain no private images, GIFs,
      captions, or catalog.
- [x] Example identifiers and credentials are visibly inert.
- [x] Secret scanning passes against the full history and release artifacts.

## Reproducibility

- [x] A clean GitHub Actions checkout builds the bridge wheel and both Android
      APK variants using the pinned toolchains.
- [x] Gradle wrapper version, distribution checksum, Android plugin/tool
      versions, and downloaded dependency checksums are pinned.
- [x] Automated unit, contract, and integration tests pass locally.
- [x] APK contents, package identity, version, signature, and checksum are
      verified independently after release signing.
- [x] The tagged source contains the exact receiver and bridge source used for
      the signed release artifacts.

## Device and service acceptance

- [x] Text, emoji, JPEG, real-library GIF, captions, looping, and screen-off
      pass on the controlled Android 10 S9+.
- [x] Burst delivery appears once and in order on TEST3.
- [x] Android reboot and package-update listener recovery pass on TEST3.
- [x] Wi-Fi interruption and queued recovery pass on TEST3.
- [x] Bridge child, tunnel process, network link, and Linux host restart
      recovery pass on the physical Raspberry Pi 2.
- [x] Multi-hour idle delivery passes after roughly 18 hours.
- [x] Android 8 older-device compatibility passes on a Galaxy S7.
- [x] Cross-device layout passes on Android 8, 10, 12, 16, and Android 17 beta.
- [x] The 854x384 dedicated mini receiver passes balanced cutout centering,
      automatic update-state retention, no-open reboot recovery, and dark-screen
      text, JPEG, and GIF delivery.

## Public presentation

- [x] README accurately describes the system without private-project jokes as
      its primary label.
- [x] AI-development disclosure is visible.
- [x] Independent-project disclaimer and acknowledgment are visible.
- [x] Beginner installation plus recovery, upgrade, removal, and security
      instructions are complete.
- [x] Public APK is verified media-free and usable with an operator-supplied
      catalog after release signing.

## Local verification record — 2026-11-23

- Python contract, bridge, HTTP integration, media, deployment, build-pinning,
  frozen-baseline, Android-source, license, CLI, and privacy suite: 59 tests
  passed.
- Android debug and minified release variants compiled from a clean build; ten
  timing and active-delivery tests passed in each variant; debug and release
  lint reported no issues.
- The bridge wheel reports version `1.0.0`; its metadata declares Python 3.9+
  and an architecture-neutral `py3-none-any` build.
- The signed public APK verifies with Android signature schemes v2 and v3. It
  contains eleven entries, all code/resources/signature metadata, and no
  operator media or credential. Package/version/SDK metadata and release hashes
  were read back independently.
- Full Git history and current-tree scans found no private key, common API-token,
  private-address, private-media, signing-material, or credential pattern. The
  deliberate forbidden-value literals in privacy tests were reviewed as test
  data.
- The installer dry-run resolved only the expected versioned standard paths
  and made no host change.
- Physical evidence covers Android 8, 10, 12, 16, and the Android 17 beta, plus Pi
  service/tunnel/link/reboot recovery and roughly 18-hour idle delivery. Exact
  device results and the remaining wake-transition quirk are in `TESTING.md`.

## 1.0.1 patch verification — 2026-11-24

- The Python contract, bridge, HTTP integration, media, deployment,
  build-pinning, Android-source, license, CLI, and privacy suite passes all 60
  tests.
- Debug and minified release Android variants build cleanly. Each variant
  passes 13 unit tests, including asymmetric-cutout padding, and both lint
  variants report no issues.
- The signed 1.0.1 APK verifies with signature schemes v2 and v3 and the same
  release certificate as 1.0.0. It has version code 10001, contains eleven
  code/resource/signature entries, and contains no media or credential.
- Physical 1.0.1 acceptance on the Android 12 XS19Pro covers centered emoji,
  JPEG, and animated GIF presentation, readable captions, acknowledgment, and
  automatic screen-off at 854x384.
- After a full XS19Pro reboot, the listener resumed without opening the app and
  separately delivered and acknowledged text, JPEG, and GIF reactions before
  returning the display to black.
