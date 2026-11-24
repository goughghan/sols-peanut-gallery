# Release verification — 1.0.1

Release date: 2026-11-24

Tag: `v1.0.1`

## Published artifacts

| Artifact | SHA-256 |
|---|---|
| `SolPeanutGallery-1.0.1.apk` | `cdfc89c990bb2d38e4505d5e2400bc40542262b572ade0f927506a2decf13ba4` |
| `sol_peanut_gallery_bridge-1.0.0-py3-none-any.whl` | `95103625af97f50e4c82ffb67ea6e333959d410c5dc99f581ce26e1ef18fd1e6` |
| `sol-peanut-gallery-release-certificate.pem` | `39edef52fc0f41708b9ec5b50913be018e84b0c1c2e118bfe8c330d921ffcc1c` |

The bridge is unchanged from 1.0.0; its wheel is repeated here so the latest
release remains a complete installation set.

The APK contains no catalog media or credentials. It has package name
`org.solpeanutgallery.receiver`, version code `10001`, version name `1.0.1`,
minimum SDK 26, and target SDK 35. Android APK Signature Schemes v2 and v3
verify successfully.

## Patch scope

Android normally centers an edge-to-edge activity inside its asymmetric
landscape cutout-safe area. On an 854x384 XS19Pro this made otherwise centered
content appear right of the physical display center. Version 1.0.1 allows
short-edge cutout layout and mirrors the larger safe inset onto both sides,
keeping content physically centered while protecting it from the cutout.

The patch also adds focused unit and source-contract coverage for the cutout
policy. The bridge protocol, durable queue, media format, and signing identity
are unchanged.

## Signing identity

- Subject: `CN=Sol's Peanut Gallery, OU=Release Signing, O=Sol's Peanut Gallery, C=US`
- RSA key size: 4096 bits
- Certificate SHA-256 fingerprint:
  `3c888c4e480bee019fb2904a03da9f86e6ac479e790353c85adf5852cd2f6e99`

The matching signer and higher version code permit an in-place update from
1.0.0 while preserving pairing, credentials, listener preference, and optional
screen-off preference.

## Verification summary

- All 60 Python bridge, contract, source, privacy, deployment, and integration
  tests pass.
- Debug and minified release Android variants build with the pinned toolchain.
- Thirteen Android unit tests pass in each variant; debug and release lint are
  clean.
- The APK is zip-aligned, contains eleven code/resource/signature entries, and
  contains no media, private address, credential, or signing material.
- Package metadata, v2/v3 signatures, signer fingerprint, and all published
  hashes were independently read back after signing.

## Physical acceptance

The signed candidate installed in place over 1.0.0 on an XS19Pro running
Android 12/API 31. It preserved pairing and listener state. At 854x384 it
displayed centered emoji, JPEG, and animated GIF reactions with readable
captions, matching acknowledgments, and automatic return to a dark screen.

After a full phone reboot, the listener resumed without the app being opened.
Separate text, JPEG, and GIF reactions were claimed, displayed, visibly
confirmed, acknowledged without error, and followed by automatic screen-off.
For a dedicated unattended display, changing the device's Swipe lock screen to
None avoided a vendor lock-screen transition before the reaction.
