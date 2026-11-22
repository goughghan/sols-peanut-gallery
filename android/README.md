# Android receiver

The receiver is a dependency-light Java application for Android 8.0 (API 26)
or newer. It targets API 35 and contains no operator media or endpoint.

## Build

Required build tools:

- JDK 17
- Android SDK platform 35
- Android build-tools 35.0.0
- the included checksum-pinned Gradle wrapper

The wrapper downloads exactly Gradle 8.9 and verifies the official distribution
SHA-256. Android Gradle Plugin 8.7.3, build inputs, and dependency checksums are
pinned in the project. From this directory run:

```text
./gradlew --no-daemon clean assembleDebug testDebugUnitTest lintDebug
```

The debug APK is written to `app/build/outputs/apk/debug/app-debug.apk`. It uses
the deliberately separate package ID `org.solpeanutgallery.receiver.test` and
the label `Sol's Peanut Gallery Test` for controlled side-by-side testing. A
release build must use a maintainer-controlled signing key that is never placed
in the checkout, Gradle properties, command line, or an unencrypted file.

## Pairing and listener control

1. Enter the bridge origin, a current six-digit one-time code, and a device
   label in the app.
2. Pairing stores the receiver token encrypted by Android Keystore.
3. Explicitly enable the foreground listener. This choice survives ordinary
   reboots and package updates.
4. On Android versions that require them, grant notification and full-screen
   notification access so queued reactions can wake the dedicated display.
5. Optionally grant device-administrator force-lock permission and enable the
   screen-off choice. Without that optional permission, the app finishes after
   each reaction and leaves screen timeout behavior to Android.

Disable the listener from the app before changing its bridge or retiring a
receiver. Revoke the old receiver UUID on the bridge as well.

## Delivery behavior

The listener polls with bounded exponential reconnect backoff. It never follows
HTTP redirects. Media must exactly match delivery byte count, MIME signature,
SHA-256, and decoded dimensions before it enters the private cache. The
immersive activity acknowledges only after the requested display interval,
explicit dismissal, or a bounded failure.

GIF timing is loop-aware: at least four loops for short GIFs, at least twelve
seconds when captioned, a preferred loop-boundary close, and a thirty-second
ceiling. A long press explicitly dismisses a visible reaction.

No APK has been installed on a physical device from this clean-room tree yet;
the device acceptance matrix remains a release gate.
