# Public release checklist

## Provenance and licensing

- [x] Every executable file was authored in the clean-room tree.
- [x] No private prototype or unlicensed-project source was consulted during
      implementation.
- [x] Dependencies and bundled notices have been reviewed.
- [x] GPL license identifiers and the root license file are present.
- [x] Inspiration credit does not imply endorsement or included source.

## Privacy and secrets

- [ ] Repository history contains no tunnel keys, tokens, pairing state,
      signing material, private addresses, unintended personal details, or
      logs.
- [x] Repository and locally built debug APK contain no private images, GIFs,
      captions, or catalog.
- [x] Example identifiers and credentials are visibly inert.
- [ ] Secret scanning passes against the full history and release artifacts.

## Reproducibility

- [ ] A clean checkout builds the bridge and APK using documented commands.
- [x] Gradle wrapper version, distribution checksum, Android plugin/tool
      versions, and downloaded dependency checksums are pinned.
- [x] Automated unit, contract, and integration tests pass locally.
- [ ] APK contents, package identity, version, signature, and checksum are
      verified independently.
- [ ] Published source corresponds exactly to the release artifact.

## Device and service acceptance

- [x] Text, emoji, JPEG, real-library GIF, captions, looping, and screen-off
      pass on the controlled Android 10 S9+.
- [x] Burst delivery appears once and in order on TEST3.
- [x] Android reboot and package-update listener recovery pass on TEST3.
- [x] Wi-Fi interruption and queued recovery pass on TEST3.
- [ ] Bridge child, tunnel process, and Linux host restart recovery pass.
- [ ] Multi-hour idle delivery passes.
- [ ] Intended older Android device passes the full matrix.

## Public presentation

- [x] README accurately describes the system without private-project jokes as
      its primary label.
- [x] AI-development disclosure is visible.
- [x] Independent-project disclaimer and acknowledgment are visible.
- [ ] Installation, recovery, upgrade, removal, and security instructions are
      complete.
- [ ] Public APK is media-free and usable with an operator-supplied catalog.

## Local verification record — 2026-11-22

- Python contract, bridge, HTTP integration, media, deployment, build-pinning,
  frozen-baseline, Android-source, license, and privacy suite: 41 tests passed.
- Android debug and minified unsigned release variants compiled from a clean
  build; ten timing and active-delivery tests passed in both variants; debug
  and release lint reported no issues.
- The bridge wheel built, installed into an isolated virtual environment, and
  its console entry point reported version `0.1.0`.
- The pre-freeze debug and unsigned release APKs each contained eight entries
  and no bundled media. The frozen sacrificial build is recorded separately in
  `docs/baselines/CONTROLLED-TEST-BASELINE-20261122.md`.
- Controlled S9+ evidence now covers media display, burst ordering,
  package-update recovery, Wi-Fi recovery, Android reboot recovery, silent
  full-screen launch, and automatic screen-off. It does not satisfy
  supervised service/tunnel/host restart, long-idle, intended target-device,
  final release-key, clean-public-history, or independent second-system gates.
