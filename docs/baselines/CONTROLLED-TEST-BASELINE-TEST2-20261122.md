# Controlled device-test baseline TEST2 — 2026-11-22

Baseline ID: `PG-CR-0.1.0-TEST2-20261122`

## Scope

This freezes the narrowly repaired clean-room source and a new sacrificial
debug APK for a controlled S9+ GIF regression test. TEST1 and its source
archive remain preserved. Preparing TEST2 did not deploy, install, pair,
publish, restart infrastructure, or contact the Pi, phone, tunnel, plugin, or
quarantined prototype.

## Reason for TEST2

TEST1 passed pairing, authenticated polling, text and supported-emoji display,
JPEG display, delivery acknowledgment, automatic screen-off, and reconnection
after isolated bridge restarts. Two independently generated animated GIFs still
showed overlapping frames, including full-size opaque frames with explicit
background disposal.

TEST2 makes one renderer correction in `GifView.onDraw`: immediately before
selecting and drawing each decoded GIF frame, the view replaces the complete
canvas with opaque black using `PorterDuff.Mode.SRC`. This prevents pixels from
the preceding frame from surviving in the software canvas. A source regression
test requires that exact replacement operation to remain before `Movie.draw`.

## Pinned build chain

- JDK 17
- Android SDK platform 35 and build-tools 35.0.0
- Gradle Wrapper 8.9
- Gradle distribution SHA-256:
  `d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab`
- Gradle Wrapper JAR SHA-256:
  `498495120a03b9a6ab5d155f5de3c8f0d986a449153702fb80fc80e134484f17`
- Android Gradle Plugin 8.7.3
- Dependency artifact hashes in `android/gradle/verification-metadata.xml`

The strict wrapper build completed with dependency verification enabled. Both
debug and release variants passed all five timing tests, and both lint reports
contained no issues. The final Python suite passed 39/39 in the working tree.

## Sacrificial APK

- File: `local-artifacts/controlled-device-test-20261122/sol-peanut-gallery-receiver-test-0.1.0-test2.apk`
- SHA-256: `dceca58123a02232e7c3bb45cb1ac00e7354a4d1f88eda7d42bf8bb966c11eec`
- Size: 35,755 bytes
- Package: `org.solpeanutgallery.receiver.test`
- Version: `0.1.0-test2` (`versionCode` 1)
- Label: `Sol's Peanut Gallery Test 2`
- Android: minimum API 26; target API 35
- Signature: valid APK Signature Scheme v2 disposable Android debug signature
- Debug certificate SHA-256:
  `e8a466636c77e80ae17f333a86d08c8123370a78e23b4df96c510d5f10638a8d`
- Contents: eight APK entries; no bundled operator media, catalog, endpoint, or
  working credential

The unchanged `.test` package remains isolated from a future release package.
The TEST2 label and version distinguish this candidate from TEST1. The debug
certificate is disposable and is not release identity. Do not publish this APK.

## Source freeze

`SOURCE-MANIFEST-TEST2-20261122.sha256` records every source, contract,
document, wrapper, and verification-metadata file in the TEST2 frozen tree
except itself and ignored local/build artifacts. The deterministic source
archive `sol-peanut-gallery-cleanroom-0.1.0-test2-source.tar.gz` and its SHA-256
sidecar sit beside the APK under
`local-artifacts/controlled-device-test-20261122/`.

Verify the checked-out baseline from the project root:

```text
sha256sum --check docs/baselines/SOURCE-MANIFEST-TEST2-20261122.sha256
python -m unittest discover -s tests -v
cd android
./gradlew --no-daemon clean assembleDebug testDebugUnitTest lintDebug assembleRelease testReleaseUnitTest lintRelease
```

## Remaining physical gate

Static source ordering, compilation, unit tests, lint, signing, APK structure,
and source-archive reproducibility cannot prove the S9+ compositor behavior.
The TEST2 APK still requires a controlled physical GIF regression test using a
deliberately generated full-size opaque animated fixture. Deployment and pairing
remain outside this preparation baseline and require a separate explicit start.
