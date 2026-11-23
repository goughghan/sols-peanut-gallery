# Controlled installation and operations

These procedures are prepared for review. They have not been run on a live
bridge, receiver, tunnel, or catalog.

## Bridge installation

1. Build and test the wheel from a clean checkout as documented in `BUILD.md`.
2. Review `deploy/bin/create-layout.sh` and explicitly approve its exact target
   before using `--apply` as root.
3. Create a versioned virtual environment below `/opt/sol-peanut-gallery/` and
   install only the verified wheel.
4. Place non-secret configuration below `/etc/sol-peanut-gallery/`, with state
   and operator catalog paths below `/var/lib/sol-peanut-gallery/`.
5. Generate a high-entropy administrator token directly into a protected
   operating-system credential workflow. Do not expose it in a terminal
   command argument, environment file, JSON, or log.
   Generate a different high-entropy status-observer token through the same
   protected workflow if the optional battery watcher will be used.
6. Resolve every placeholder in the systemd template, review the resulting
   unit, and only then install it. Service enable/start requires a separate
   deployment approval.
7. Validate the empty catalog, create one one-time pairing code locally, and
   verify health and authentication before admitting a receiver.

Use HTTPS or a separately reviewed protected local transport if the network is
not physically and administratively trusted. Tunnel software is an external
component and should have its own least-privilege unit and encrypted credential.

## Upgrade

1. Back up the SQLite state, non-secret configuration, and operator catalog
   metadata/media separately; never copy credentials into the source checkout.
2. Build and test the new wheel, then install it into a new versioned virtual
   environment without modifying the active version.
3. Stop the service, copy the state database for rollback, change the resolved
   executable path, start the service, and run health/authentication checks.
4. Keep the prior environment and database copy until queued delivery,
   receiver reconnection, and acknowledgment all pass.

## Recovery

Restore non-secret configuration, catalog, media, and the last consistent
SQLite backup with owner-only permissions. Restore the administrator token
through the operating-system credential mechanism, not from source control.
After a lost or uncertain state database, revoke/re-pair every receiver rather
than trusting a copied token. Re-run catalog validation before starting.

## Removal

Disable and stop the reviewed unit first. Preserve state and the operator
catalog if recovery may be needed. Removing the service account, credential,
state, catalog, application environments, or receiver app is destructive and
requires explicit approval for those exact targets. Revoking receivers before
retirement prevents a retained device token from becoming useful again.

## Android side-by-side test

Use a separately named debug build or an otherwise reviewed installation plan
so the working private receiver is not overwritten. Do not pair through the
production bridge or tunnel. Exercise every row of `ACCEPTANCE.md` against an
isolated bridge state directory and deliberately created test media before any
cutover decision.

## Desktop low-battery notifications

This optional path is independent of message delivery. Review
`deploy/config/battery-watch.example.json` and the inactive user-service
template before installation. Place the status-observer token in an owner-only
file outside the source tree; do not reuse the administrator or receiver token.
The Linux example uses `notify-send`, while other platforms may supply an
equivalent command array. The helper does not invoke a shell.

Before enabling it permanently, test with synthetic status payloads, then with
a non-production receiver. Verify one alert below the threshold, no repeat
storm, re-arming only after recovery, and silence for charging or stale devices.
Installing or enabling the user service remains a separate operator-approved
deployment step.
