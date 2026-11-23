# Bridge

The bridge is an original Python 3.9+ service using only the standard library
at runtime. SQLite owns pairing state, receiver-token hashes, idempotent request
IDs, durable sequence numbers, claims, and acknowledgments.

## Build

From the repository root:

```text
python -m pip wheel --no-deps --wheel-dir dist .
python -m pip install dist/sol_peanut_gallery_bridge-0.1.0-py3-none-any.whl
```

For a disposable development environment, create a virtual environment and
install the project in editable mode. Do not place a credential in the virtual
environment, project tree, command line, or environment variables.

## Configuration and catalog

Copy `deploy/config/bridge.example.json` outside the source checkout and adjust
only non-secret paths and listener settings. The bridge requires:

- a writable private state directory;
- a catalog index matching `contracts/catalog.schema.json`;
- a separate operator-owned media directory; and
- an administrator transport token supplied by systemd's
  `LoadCredentialEncrypted` mechanism as `transport-token`; and
- a distinct read-only status token supplied as `status-token` for optional
  battery monitors.

An empty index is valid:

```json
{"schema_version":1,"entries":[]}
```

Catalog file names are single lowercase path components. At startup the bridge
reads each file, rejects unsupported or unsafe data, and derives the delivery
MIME type, byte count, dimensions, frame timing, and SHA-256. It checks the file
again before every authenticated download, so a file changed after startup is
not served under stale metadata.

## Commands

```text
sol-peanut-gallery --config /path/to/bridge.json validate-catalog
sol-peanut-gallery --config /path/to/bridge.json pairing-code
sol-peanut-gallery --config /path/to/bridge.json receivers
sol-peanut-gallery --config /path/to/bridge.json revoke-receiver RECEIVER_UUID
sol-peanut-gallery --config /path/to/bridge.json serve
```

The pairing command prints a six-digit code and expiry, never a long-term
credential. The Android app exchanges it directly with the bridge. Receiver
tokens are shown only to the receiver once and stored as SHA-256 digests in
bridge state.

## HTTP surface

| Method and path | Authentication | Purpose |
|---|---|---|
| `GET /healthz` | none | bounded liveness only |
| `POST /v1/pair` | one-time code | issue receiver credential |
| `POST /v1/tools/find-display-items` | administrator bearer | metadata-only catalog search |
| `POST /v1/tools/queue-display` | administrator bearer | queue text, emoji, or catalog item |
| `GET /v1/deliveries/next` | receiver bearer | fetch oldest unfinished delivery |
| `GET /v1/media/{media_id}` | receiver bearer | fetch verified local media |
| `POST /v1/deliveries/{id}/ack` | receiver bearer | acknowledge exact completion |
| `POST /v1/receiver/status` | receiver bearer | record bounded battery status |
| `GET /v1/status/receivers` | status-observer bearer | read current receiver battery status |
| `POST /v1/admin/pairing-codes` | administrator bearer | create one-time code remotely |
| `POST /v1/admin/receivers/{id}/revoke` | administrator bearer | revoke receiver remotely |

The schemas under `contracts/` and tool descriptions in
`contracts/mcp-tools.json` are the public payload contracts. A successful queue
response means queued, never visibly displayed.

Use HTTPS or a reviewed authenticated local transport whenever other devices
can observe the network. The bridge intentionally does not fetch remote URLs,
follow redirects, or bundle a tunnel provider.

## Optional desktop battery watcher

`sol-peanut-gallery-battery-watch` polls the status-only endpoint and runs an
operator-configured notification command when an unplugged receiver crosses a
low-battery threshold. It ignores stale reports, uses hysteresis before
re-arming, and persists notification state so service restarts do not create a
notification storm. See `deploy/config/battery-watch.example.json`.

The watcher reads its token from a private file; the token is never accepted in
JSON, an environment variable, or a command-line argument. Notification
commands are executed directly without a shell. The example uses `notify-send`
for Linux desktops, but the command is replaceable for other operating systems.
