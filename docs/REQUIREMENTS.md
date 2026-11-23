# Version 1 requirements

These requirements describe observable behavior only. They intentionally avoid
implementation details from any existing project or prototype.

## Core delivery

- `PG-001` Accept authorized reaction requests containing text/emoji or a
  stable catalog item identifier plus an optional caption.
- `PG-002` Preserve request order and display each accepted reaction at least
  once; closely spaced requests must not silently overwrite one another.
- `PG-003` Make repeated submission of the same request identifier
  idempotent.
- `PG-004` Support a bounded, authenticated Android polling or equivalent
  delivery interface on the local network.
- `PG-005` Pair a receiver using a short-lived, one-time code and issue a
  revocable receiver credential.

## Android receiver

- `PG-101` Support Android 8.0 or newer for the initial public target.
- `PG-102` Run an explicitly enabled foreground listener and resume it after a
  device reboot or package update.
- `PG-103` Present reactions in immersive landscape mode without status or
  navigation bars when the operating system permits it.
- `PG-104` Render text, Unicode emoji, verified JPEG files, and verified
  animated GIF files.
- `PG-105` Preserve GIF animation timing, provide at least four complete loops
  for short GIFs, allow at least twelve seconds for captioned GIFs, and prefer
  closing on a loop boundary within a thirty-second ceiling.
- `PG-106` Wake the display for a reaction and return the dedicated device to a
  dark screen afterward when the operator enables the required device setting.
- `PG-107` Resume polling after temporary Wi-Fi loss without reopening the app.
- `PG-108` Retain pairing and the operator's listener-enabled choice across
  ordinary updates and reboots.
- `PG-109` Optionally report bounded battery percentage and charging state so
  an operator can receive a low-battery alert without exposing queue authority.

## Bridge and tunnel integration

- `PG-201` Run on low-resource Linux hardware including 32-bit ARM with no
  mandatory cloud database.
- `PG-202` Start at boot and recover automatically after a bridge-child crash,
  tunnel-process crash, network outage, or host restart.
- `PG-203` Keep tunnel credentials outside source control and make unattended
  operation possible through an operating-system credential mechanism.
- `PG-204` Expose small, bounded tool descriptions for direct text/emoji,
  catalog search or selection, and catalog display.
- `PG-205` Treat a successful tool call as queued delivery, not proof that the
  physical screen displayed the reaction.
- `PG-206` Protect battery-status reads with a distinct least-privilege
  credential that cannot queue, pair, revoke, download, or acknowledge.

## Media and privacy

- `PG-301` Keep operator media outside the APK and public source repository.
- `PG-302` Validate permitted MIME type, byte ceiling, dimensions, and content
  hash before displaying downloaded media.
- `PG-303` Prevent path traversal, redirects to untrusted locations, and
  unauthenticated media retrieval.
- `PG-304` Support an empty catalog so text and emoji remain useful without any
  media files.

## Release quality

- `PG-401` Produce reproducible source builds and a signed release APK without
  committing the signing key.
- `PG-402` Ship automated tests for pairing, authentication, idempotency,
  ordering, queue persistence, catalog validation, and media rejection.
- `PG-403` Publish no credentials, private addresses, pairing state, logs,
  personal media, or private reaction metadata.
- `PG-404` State the AI-assisted development history and independent-project
  status prominently.

## Deliberately outside version 1

- Hosted media search or automatic downloading from third-party sites.
- Bundled meme or family-photo libraries.
- A hosted relay service operated for the public.
- Editable speech bubbles or on-device image authoring.
- Guaranteed unsolicited activity when no assistant turn or scheduled action
  occurs.
