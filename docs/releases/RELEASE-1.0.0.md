# Release verification — 1.0.0

Release date: 2026-11-23

Tag: `v1.0.0`

## Published artifacts

| Artifact | SHA-256 |
|---|---|
| `SolPeanutGallery-1.0.0.apk` | `199376f32752525531c25f54955d7d82cc969391c90e270f31682e45c9037c23` |
| `sol_peanut_gallery_bridge-1.0.0-py3-none-any.whl` | `95103625af97f50e4c82ffb67ea6e333959d410c5dc99f581ce26e1ef18fd1e6` |
| `sol-peanut-gallery-release-certificate.pem` | `39edef52fc0f41708b9ec5b50913be018e84b0c1c2e118bfe8c330d921ffcc1c` |

The APK contains no catalog media or credentials. It has package name
`org.solpeanutgallery.receiver`, version code `10000`, version name `1.0.0`,
minimum SDK 26, and target SDK 35. Android APK Signature Schemes v2 and v3
verify successfully.

## Signing identity

- Subject: `CN=Sol's Peanut Gallery, OU=Release Signing, O=Sol's Peanut Gallery, C=US`
- RSA key size: 4096 bits
- Certificate SHA-256 fingerprint:
  `3c888c4e480bee019fb2904a03da9f86e6ac479e790353c85adf5852cd2f6e99`

Future Android updates must use this same identity. The private key and its
passphrase are not part of the repository or release assets; the PEM asset is
the public certificate only.

## Verification summary

- The complete Python bridge/contract/privacy/deployment test suite passes.
- Debug and minified release Android variants build with the pinned toolchain.
- Ten Android unit tests pass in each variant; debug and release lint are clean.
- Release installer dry-run resolves the expected versioned paths without
  changing the host.
- APK contents, package metadata, signature, certificate, and hashes were
  independently read back after signing.

## Physical acceptance matrix

- Samsung Galaxy S7 — Android 8
- Samsung Galaxy S9+ — Android 10
- Onn tablet — Android 16
- Pixel 7 Pro — **Android 17 beta**

The matrix covers text, emoji, JPEG, short/long/tall/wide animated GIFs,
captions, responsive landscape scaling, acknowledgment, and screen-off. The
S9+ also passed ordered burst, Wi-Fi interruption, package-update, phone-reboot,
and roughly 18-hour idle recovery. The Raspberry Pi 2 reference host passed
service-child, tunnel-child, Ethernet-link, and unattended-reboot recovery.

Android may expose its navigation/status controls very briefly while waking on
some devices. TEST8 reduced the Onn tablet behavior to at most a momentary
single-frame flicker; delivery and screen-off still completed normally.
