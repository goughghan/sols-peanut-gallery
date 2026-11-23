# Architecture boundaries

```text
Assistant/tool client
        |
        v
Authenticated tool adapter
        |
        v
Persistent ordered queue  <---->  Operator-owned catalog
        |
        v
Authenticated local delivery endpoint
        |
        v
Android foreground listener --> immersive reaction screen
        |
        +--> bounded battery heartbeat --> read-only status endpoint
                                             |
                                             v
                                    optional desktop notifier
```

## Components

### Bridge core

Owns pairing, receiver credentials, request idempotency, ordered persistence,
catalog metadata, and bounded media delivery. It must be usable without any
specific tunnel provider.

### Tool adapter

Translates small tool calls into bridge-core requests. Provider-specific
tunnel software remains an external dependency and is never copied into this
repository.

### Android receiver

Owns foreground listening, reconnection, validation, rendering, ordered
acknowledgment, wake behavior, and optional screen-off behavior. The receiver
must not contain an operator's media library or bridge administrator secret.

The listener persists the active delivery ID, sequence, deadline, and whether
completion has already been claimed. Activity-opened and completion signals may
cancel, acknowledge, or clear state only when both identity fields match that
record. Each delivery has its own full-screen notification ID; the activity
cancels only its matching notification after its reaction view has opened.

The receiver reports only battery percentage and charging state at a bounded
interval. The bridge timestamps the report and does not accept arbitrary device
metadata through this path.

### Battery status observer

Battery observers use a credential distinct from the receiver and administrator
tokens. They can read current receiver battery status but cannot pair, revoke,
queue, search, download media, or acknowledge deliveries. The reference desktop
watcher ignores stale reports and delegates presentation to a replaceable local
notification command.

### Operator catalog

Lives outside the application and can be empty. The public repository may
include only a media-free example and redistributable test fixtures created
specifically for the project.

## Independence rule

The public implementation may satisfy these interfaces in any original way.
File names, class names, protocol shapes, wording, and internal organization
must not be copied from an unlicensed project or from the private feasibility
prototype.
