# Controlled testing record

This document summarizes sanitized physical observations for the independent
clean-room receiver. It contains no private catalog media, endpoint, network
address, pairing state, credential, signing material, or operator log.

## Controlled environment

- Date: 2026-11-22
- Receiver: Samsung Galaxy S9+, Android 10
- Build: `0.1.0-test3`, package `org.solpeanutgallery.receiver.test`
- Bridge: isolated clean-room process and state directory
- Media: deliberately created fixture JPEG/GIF files plus two unchanged
  operator-library GIF controls; no media is included in this repository

The controlled package used a separate application identity and signing
identity so it could not replace the private feasibility receiver. The live Pi,
tunnel, private plugin, private catalog, and quarantined prototype were outside
this test boundary.

## Passed observations

- One-time pairing and authenticated polling.
- Text, captions, and Android-10-supported emoji.
- JPEG download, hash verification, immersive landscape display, and timed
  close.
- A real 80-frame, 5.32-second GIF repeated for the requested display interval
  without visible overlap.
- A real 12-frame, 0.6-second GIF repeated for the requested display interval
  without visible overlap.
- Three back-to-back reactions appeared exactly once and in queue order after
  TEST3's active-delivery identity repair.
- Full-screen reactions launched silently from a dark screen without a visible
  heads-up banner, then optional device administration turned the display off.
- An in-place package update retained pairing and listener state and resumed
  polling without the app being opened.
- A reaction queued while Wi-Fi was disabled arrived once after reconnection.
- After an Android reboot, the listener resumed without the app being opened;
  a dark-screen reaction appeared once, showed no banner, acknowledged once,
  and returned the display to dark.
- The receiver reconnected after an isolated bridge restart.

## Compatibility findings

- One newer Unicode emoji lacked a glyph in the S9+'s Android 10 system font.
  The transport and display path worked; a curated compatible emoji subset or
  redistributable fallback font remains a possible hardening item.
- Two synthetic GIFs produced by the diagnostic image tool showed composited
  frame overlap through Android's platform `Movie` decoder even after explicit
  canvas clearing. Both representative operator-library GIF classes rendered
  correctly. Arbitrary third-party GIFs may therefore need catalog preflight
  or normalization before a stable release.
- On the Android 10 S9+ and the Onn tablet, navigation controls were briefly
  visible while the display woke, then immersive mode hid them. The same flash
  was not observed on the Galaxy S7. Pixel behavior varied with its launcher
  and unlock path. In every case the reaction itself displayed and completed
  normally. This is recorded as a non-blocking Android wake-transition quirk.

## Deployed clean-room integration

On 2026-11-22, the independent bridge, ARMv7 tunnel client, and receiver build
`0.1.0-test7` were exercised together on the Raspberry Pi 2 and Android 10
S9+. The author-derived feasibility prototype remained quarantined and was not
used by these deliveries.

- A normal ChatGPT conversation discovered the clean-room MCP tools through the
  secure tunnel and queued an emoji/caption reaction. The receiver displayed it,
  acknowledged it once, and resumed polling.
- The same normal conversation called `find_display_items` and then
  `queue_display` for a catalog JPEG and a catalog GIF. Both verified media
  downloads displayed successfully and produced matching completion
  acknowledgments. The GIF completed four whole loops before closing, as
  required by the receiver timing policy.
- Sending `SIGKILL` to the bridge child caused systemd to restart it after the
  configured five-second delay. The receiver resumed polling and a subsequent
  tunneled reaction displayed and acknowledged successfully.
- Sending `SIGKILL` to the tunnel child caused systemd to restart it after the
  configured five-second delay. The replacement process reinitialized its MCP
  session and control-plane poller, then delivered and acknowledged a subsequent
  normal-chat reaction without operator credential entry.
- A reaction queued while the S9+ Wi-Fi connection was disabled remained
  pending in SQLite. After Wi-Fi was restored, the receiver claimed, displayed,
  and acknowledged it once; the queue then returned to empty polling.
- During a physical Pi Ethernet interruption, the tunnel recorded repeated
  control-plane timeouts while the bridge and tunnel processes remained active.
  After the cable was reconnected, the same processes recovered without
  operator action. A new normal-chat reaction traversed the recovered tunnel,
  displayed once, acknowledged successfully, and left no pending delivery.
- A complete Pi reboot produced a new kernel boot identity. The bridge and
  tunnel services started automatically without operator credential entry. The
  tunnel retried while the bridge completed its slower startup, then initialized
  its MCP session; the S9+ resumed polling. A new normal-chat reaction displayed
  once, acknowledged successfully, and left the durable queue empty. No systemd
  units were failed after the test.
- After roughly 18 hours of uninterrupted post-reboot polling, a normal-chat GIF
  reaction reached the S9+, completed its automatic loop timing, acknowledged
  once, and left the queue empty. This passed the clean-room long-idle delivery
  gate; the brief wake-time navigation-control flash is recorded separately as
  a compatibility observation.
- After both supervised failures, the bridge and tunnel services remained
  active and the receiver continued empty-queue polling.

## Cross-device presentation matrix

On 2026-11-23, the same signed clean-room `0.1.0-test7` receiver was exercised
on four differently sized Android displays: a Galaxy S7 on Android 8, Galaxy
S9+ on Android 10, Onn tablet on Android 16, and Pixel 7 Pro on the Android 17
beta. One listener was enabled at a time; every recorded reaction acknowledged
once and the durable queue returned to empty before the next device test.

- A Galaxy S7 running Android 8 displayed a long emoji caption, JPEG, short
  12-frame GIF, and tall 88-frame GIF in landscape. Captions remained readable,
  media stayed fully visible, animation showed no overlap, and no wake-time
  navigation-control flash was observed.
- The Pixel 7 Pro on the Android 17 beta displayed long text, JPEG, and a wide
  80-frame GIF with correct caption and media scaling. Its locked wake path
  briefly transitioned from portrait to landscape; under the controlled
  stock-launcher/no-unlock-gate condition it opened directly in landscape.
- The Onn tablet on Android 16 displayed a 170-to-180-character emoji caption,
  JPEG, tall GIF, and wide GIF without clipping or visible animation overlap. The larger
  display preserved sensible media and text proportions. Dark-screen reactions
  opened full screen after the required permissions were enabled and optional
  device administration returned the display to dark. Android briefly exposed
  the system bars during wake even with the stock launcher, no swipe gate, and
  the configuration activity removed from Recents.
- Across all four devices, the responsive layout handled phone and tablet
  dimensions without a device-specific build or bundled media.

## Dedicated mini-phone acceptance and 1.0.1 cutout repair

On 2026-11-24, the signed public 1.0.0 receiver was installed on an XS19Pro
mini phone running Android 12/API 31. The device reports an 854x384 display,
3 GB RAM, 32 GB storage, and a 32-bit ARMv7 userspace. Pairing, foreground
polling, authenticated delivery, completion acknowledgment, and optional
device-administrator screen-off all worked.

The first text and JPEG reactions were centered within Android's asymmetric
landscape cutout-safe region, which made them appear visibly right of the
physical display center. The 1.0.1 candidate enables short-edge cutout layout
and mirrors the larger cutout inset onto both sides. The signed candidate
installed in place with the public release identity and preserved pairing and
listener state.

Physical retesting then passed:

- centered emoji and caption;
- centered JPEG and readable caption;
- centered animated GIF with smooth playback and readable caption;
- one-time Android full-screen tutorial dismissal;
- a direct black-screen to reaction transition after the device's Swipe lock
  screen was changed to None; and
- completion acknowledgment followed by automatic return to a dark display.

The mini phone was then fully rebooted. Without opening the receiver app, its
foreground listener resumed automatically and separately claimed, displayed,
and acknowledged an emoji/caption reaction, a JPEG/caption reaction, and an
animated GIF/caption reaction. All three were visibly confirmed; the GIF was
centered and readable, and the display returned to black afterward. Every
recorded post-reboot completion had outcome `displayed` with no error.

Disabling Google Play Protect was not required for runtime behavior; it affects
installation scanning rather than reaction presentation.

### TEST8 immersive-wake tightening

The signed `0.1.0-test8` package installed in place over TEST7 on the Onn
tablet with the same controlled-test signing identity and a higher version
code. Pairing and listener-enabled state survived the update.

TEST8 applies fullscreen flags before `Activity.onCreate`, uses the current
Android system-bar controller in addition to the legacy immersive flags,
removes the launch transition, immediately re-hides bars exposed by the system,
and launches each reaction in a separate disposable task. With gesture
navigation and window/transition animations disabled on the dedicated tablet,
two dark-screen emoji reactions opened directly, displayed and acknowledged
once, returned the screen to dark, and left the configuration screen closed.
The previously obvious system-bar flash was reduced to no clearly sustained
appearance; on close observation, the operator reported at most an
approximately single-frame flicker. This is accepted as a non-blocking
vendor-controlled wake-transition limit rather than a content or delivery
failure.

## Public clean-checkout smoke test

On 2026-11-22, a new shallow clone of the public `main` branch was tested in a
disposable directory with no private workspace files or retained build state:

- All 41 public Python, contract, security, deployment, and source-boundary
  tests passed; the two optional ignored-artifact checks skipped as designed.
- The bridge wheel built from the repository root and installed into a new
  virtual environment with no runtime dependency.
- The installed entry point reported version `0.1.0`.
- The empty example catalog validated successfully.
- Initial state creation produced an owner-only SQLite database.
- A live isolated bridge returned HTTP 200 from `/healthz` and rejected an
  unauthenticated administrator request with HTTP 401.
- The deployment layout script reported dry-run mode and made no system
  changes.

GitHub Actions independently builds the bridge wheel and both Android APK
variants from a separate clean checkout. The later physical device and release
evidence below complements that clean-checkout result.

## Release status

The separately signed public APK and the inexpensive dedicated receiver gate
have both passed. These results support the public release while retaining the
documented vendor-specific wake-transition and arbitrary-GIF compatibility
limits; they do not claim universal behavior on every Android build or GIF.
