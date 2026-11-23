# Controlled installation and operations

The standard installation path is documented in
[`QUICKSTART.md`](QUICKSTART.md). It installs a versioned environment and a
ready hardened service without enabling or starting it. The steps below cover
the operational boundaries after that first installation.

## Bridge installation

1. Verify the release wheel with the published `SHA256SUMS`.
2. Run `deploy/bin/pi-preflight.sh` and review the result.
3. Run `deploy/bin/install-bridge.sh --dry-run WHEEL` as an ordinary user.
4. After reviewing its exact paths, run the same installer with `--apply` as
   root. It creates the unprivileged account, versioned environment, empty
   catalog, host-encrypted transport/status credentials, and ready service.
5. Review `/etc/sol-peanut-gallery/bridge.json` and the installed service.
6. Enable and start the service only as a separate deliberate step, then check
   `/healthz` from the Android device before creating a pairing code.

The installer preserves an existing configuration and encrypted credentials.
It refuses to overwrite an existing environment for the same version and does
not enable or start the bridge automatically.

Use HTTPS or a separately reviewed protected local transport if the network is
not physically and administratively trusted. Tunnel software is an external
component and should have its own least-privilege unit and encrypted credential.
Never forward the bridge's plain-HTTP port through a router.

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
