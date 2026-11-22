# Controlled device-test baseline TEST3 — 2026-11-22

Baseline ID: `PG-CR-0.1.0-TEST3-20261122`

## Scope

This freezes the clean-room burst-sequencing repair and a new unsigned TEST3
APK for signing and a future controlled S9+ update test. All TEST1 and TEST2
source archives, APKs, sidecars, physical evidence, and the separately created
durable-signed TEST2 artifact remain preserved. Preparing TEST3 did not deploy,
install, pair, publish, sign, restart infrastructure, or contact the Pi, phone,
tunnel, plugin, private signing material, or quarantined prototype.

## Reason for TEST3

In a three-reaction physical burst, sequences 9 and 10 completed normally and
sequence 11 began. A late duplicate sequence-10 completion then caused the
receiver to acknowledge sequence 10 again and clear the timestamp guarding
sequence 11. The bridge rejected the stale acknowledgment but correctly
redelivered unfinished sequence 11, producing a second media download and
display attempt.

The burst also exposed a heads-up reaction banner while the screen remained
awake between immediately adjacent reactions. Isolated reactions launched
full-screen from the dark screen without that visible transition banner.

## Repair

- Persist active delivery ID, sequence, deadline, and completion-claimed state
  as one receiver-side record.
- Accept a completion only once and only while its ID and sequence match the
  unexpired active record.
- Clear active state only when the asynchronous acknowledgment still refers to
  that same record; a stale completion cannot release a newer delivery.
- On acknowledgment failure, clear only the matching record so the bridge can
  provide ordered at-least-once redelivery.
- Use the high-importance full-screen notification as the single automatic
  activity-launch path instead of also calling `startActivity` directly.
- Use a separate notification ID for each delivery. After the reaction view
  opens, the activity reports its identity and the service cancels only that
  matching notification. Stale activities cannot cancel a newer notification.
- Keep the ongoing listener notification unchanged. The TEST3 reaction channel
  remains high importance but is explicitly configured without sound or
  vibration.
- Treat repeated `onNewIntent` delivery of the same reaction as idempotent and
  do not create another display timer or completion.

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

Both debug and release variants passed all ten Android unit tests: five display
timing tests and five active-delivery transition tests. Both lint reports
contained no issues. The final Python suite passed 40/40 in the working tree.

## Unsigned test APK

- File: `local-artifacts/controlled-device-test-20261122/sol-peanut-gallery-receiver-test-0.1.0-test3-unsigned.apk`
- SHA-256: `680b977df461f679b2b1d43c06f6290ee2a4773d9d96c29837807261b572c55c`
- Size: 34,339 bytes
- Package: `org.solpeanutgallery.receiver.test`
- Version: `0.1.0-test3` (`versionCode` 2)
- Label: `Sol's Peanut Gallery Test 3`
- Android: minimum API 26; target API 35
- Signature: intentionally unsigned
- Contents: eight APK entries; no bundled operator media, catalog, endpoint,
  working credential, signature, or private signing material

This APK cannot be installed as-is. Big Brother may sign a verified copy using
the durable controlled-test identity outside this source baseline, with its
passphrase entered only through a visible graphical prompt. The signed result
must be recorded separately and its package, version, certificate, contents,
and hash reverified before any controlled update. Never place the private key
or passphrase in this repository, an archive, command argument, log, or chat.

## Source freeze

`SOURCE-MANIFEST-TEST3-20261122.sha256` records every source, contract,
document, wrapper, test, and verification-metadata file in the TEST3 frozen
tree except itself and ignored local/build artifacts. The deterministic source
archive `sol-peanut-gallery-cleanroom-0.1.0-test3-source.tar.gz` and its SHA-256
sidecar sit beside the unsigned APK under
`local-artifacts/controlled-device-test-20261122/`.

Verify the checked-out baseline from the project root:

```text
sha256sum --check docs/baselines/SOURCE-MANIFEST-TEST3-20261122.sha256
python -m unittest discover -s tests -v
cd android
./gradlew --no-daemon clean assembleDebug testDebugUnitTest lintDebug assembleRelease testReleaseUnitTest lintRelease
```

## Remaining physical gates

After separate durable signing and independent artifact verification, the S9+
still requires a controlled in-place update and repeat burst of emoji, JPEG,
and real-library GIF reactions. Acceptance requires one display, download, and
acknowledgment for each delivery in order; no stale acknowledgment; no overlap;
and prompt cancellation of only the opened reaction's burst-transition banner.
Dark-screen isolated full-screen delivery, screen-off, and update recovery must
also remain working.
