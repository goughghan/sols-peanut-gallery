# Public contract draft

The JSON Schemas under `contracts/` define implementation-neutral boundaries
for pairing, requests, ordered receiver delivery, explicit completion
acknowledgments, and operator catalogs. They are requirements artifacts, not a
commitment to any private prototype protocol.

The draft MCP surface deliberately contains only two tools:

- `find_display_items` searches operator-owned metadata without fetching media
  from the public internet.
- `queue_display` accepts exactly one of emoji, catalog reaction ID, or a
  caption-only reaction and reports queued status rather than claiming visible
  delivery.

The delivery contract separates acceptance from completion. A receiver must
acknowledge a specific opaque delivery ID only after the reaction finishes or
is explicitly dismissed. This makes sequential burst behavior testable and
prevents accepted messages from being silently treated as displayed.

All identifiers and values in `examples/` are inert placeholders. The example
catalog is empty and contains no media.

`receiver-status.schema.json` bounds the receiver heartbeat to battery
percentage and charging state. `receiver-status-list.schema.json` defines the
read-only observer response. These endpoints are not MCP tools and do not grant
an assistant access to device telemetry.
