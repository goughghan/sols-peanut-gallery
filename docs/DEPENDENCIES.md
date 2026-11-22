# Dependencies and licenses

## Shipped runtime

The bridge has no third-party Python runtime dependency. It uses Python 3.9+
standard-library HTTP, JSON, hashing, and SQLite modules.

The APK has no third-party runtime library. It uses Android platform APIs for
HTTP, JSON, Android Keystore, notifications, foreground services, image
decoding, and device administration.

## Build and test tools

| Component | Pinned range/version | Use | License or terms |
|---|---:|---|---|
| setuptools | `>=68` | Python wheel build | MIT |
| jsonschema | `>=4.20,<5` | Python contract tests only | MIT |
| JUnit | `4.13.2` | Android timing tests only | Eclipse Public License 1.0 |
| Hamcrest Core | `1.3` | transitive JUnit assertion helper | BSD 3-Clause |
| Gradle | `8.9` | Android build orchestration | Apache License 2.0 |
| Gradle Wrapper | `8.9` | checksum-pinned Gradle bootstrap | Apache License 2.0 |
| Android Gradle Plugin | `8.7.3` | Android build plugin | Apache License 2.0 |
| Android SDK/build-tools | platform 35 / 35.0.0 | compile, package, lint, inspect | Android SDK terms |
| JDK | 17 | Java compiler/runtime for build | provider-specific OpenJDK terms |

Only the standard Gradle Wrapper bootstrap scripts/JAR are bundled in the
source tree; no build/test tool or third-party runtime library is bundled in
the APK. The app's compiled platform API references do not package Android SDK
code into the APK.

Review these pins and their upstream notices again before a public release,
especially if any version changes.
