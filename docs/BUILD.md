# Reproducible local build and verification

Run all commands from a clean source checkout with no operator catalog, media,
credential, signing key, or prior build directory present.

## Bridge and contract suite

Use Python 3.9 or newer:

```text
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip wheel --no-deps --wheel-dir dist .
```

The test suite covers contract examples, pairing expiry/reuse/revocation,
invalid authentication, request idempotency, concurrent sequencing, restart
persistence, exact acknowledgments, empty catalogs, HTTP integration, media
tampering, size/MIME/path rejection, deployment safety, GPL identifiers, and
the public privacy boundary.

## Android receiver

Install JDK 17, Android SDK platform 35, and build-tools 35.0.0, then use the
included wrapper:

```text
cd android
./gradlew --no-daemon clean assembleDebug testDebugUnitTest lintDebug
```

The wrapper downloads Gradle 8.9 and refuses a distribution whose SHA-256 does
not match `gradle-wrapper.properties`. Gradle dependency verification checks
the pinned Android Gradle Plugin 8.7.3, its build inputs, and test-only JUnit
artifacts against `gradle/verification-metadata.xml`.

## Artifact inspection

Before release, inspect the unsigned or debug artifact without installing it:

```text
apkanalyzer manifest application-id app/build/outputs/apk/debug/app-debug.apk
apkanalyzer manifest min-sdk app/build/outputs/apk/debug/app-debug.apk
apkanalyzer manifest target-sdk app/build/outputs/apk/debug/app-debug.apk
apkanalyzer files list app/build/outputs/apk/debug/app-debug.apk
apksigner verify --verbose --print-certs app/build/outputs/apk/debug/app-debug.apk
sha256sum app/build/outputs/apk/debug/app-debug.apk
```

The frozen controlled-test build uses debug package
`org.solpeanutgallery.receiver.test`; the unsigned release retains
`org.solpeanutgallery.receiver`. Both use minimum API 26 and target API 35.

## Release build

`./gradlew --no-daemon clean assembleRelease testReleaseUnitTest lintRelease`
produces an unsigned release artifact. Signing is a separate maintainer action
using a protected key and a visible graphical secret prompt. Never put a
signing password in chat, shell arguments, environment variables, Gradle
properties, or plaintext files. Verify the final signature and checksum on a
second clean system before publication.
