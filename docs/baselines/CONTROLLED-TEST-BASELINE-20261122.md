# Controlled device-test baseline — 2026-11-22

Baseline ID: `PG-CR-0.1.0-TEST1-20261122`

## Scope

This freezes the locally verified clean-room source and a sacrificial debug APK
for a future controlled S9+ test. It does not authorize deployment, pairing,
Pi/tunnel changes, publication, or inspection of the quarantined prototype.

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

The strict wrapper build completed after dependency verification was enabled;
debug and release lint both reported no issues and both variants passed all five
timing tests. The final Python suite passed 38/38 in the working tree; the same
38 tests passed from the extracted source archive, with the intentionally absent
ignored APK check reported as skipped there.

## Sacrificial APK

- File: `local-artifacts/controlled-device-test-20261122/sol-peanut-gallery-receiver-test-0.1.0-test1.apk`
- SHA-256: `50d5793cd154788794e5bf9cf889de89d0d75d85fa4b977d46be30235e1e57eb`
- Size: 35,671 bytes
- Package: `org.solpeanutgallery.receiver.test`
- Version: `0.1.0-test` (`versionCode` 1)
- Android: minimum API 26; target API 35
- Signature: valid APK Signature Scheme v2 disposable Android debug signature
- Debug certificate SHA-256:
  `bc6654e0cc0a30065d7e06073b44fd8419eac51b00c99f8bbc2ce22a6ec8a22f`
- Contents: eight APK entries; no bundled operator media, catalog, endpoint, or
  working credential

The `.test` package and test label deliberately distinguish this candidate from
the future release application. The debug certificate is disposable and is not
release identity. Do not publish this APK.

## Source freeze

`SOURCE-MANIFEST-20261122.sha256` records every source, contract, document,
wrapper, and verification-metadata file in the frozen tree except itself and
ignored local/build artifacts. The local source archive and its SHA-256 sidecar
sit beside the APK under `local-artifacts/controlled-device-test-20261122/`.

Verify the checked-out baseline from the project root:

```text
sha256sum --check docs/baselines/SOURCE-MANIFEST-20261122.sha256
python -m unittest discover -s tests -v
cd android
./gradlew --no-daemon clean assembleDebug testDebugUnitTest lintDebug assembleRelease testReleaseUnitTest lintRelease
```

## Remaining gates

No physical acceptance row has passed yet. Text, emoji, deliberately created
JPEG/GIF fixtures, captions, looping, screen-off, burst ordering, reboot/update
recovery, Wi-Fi recovery, bridge/tunnel/host restart, multi-hour idle, and the
intended older-device matrix remain pending.

