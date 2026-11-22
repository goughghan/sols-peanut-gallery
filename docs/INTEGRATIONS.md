# Assistant and automation integrations

Sol's Peanut Gallery is provider-neutral. The bridge and Android receiver do
not require a particular AI company, model, chat client, automation platform,
or tunnel provider.

An integration normally has this shape:

```text
assistant or automation
        |
trusted adapter or MCP server
        |
authenticated Peanut Gallery bridge
        |
paired Android receiver
```

The trusted adapter translates a provider's tool-call format into the bridge's
bounded authenticated requests. It may run beside the bridge, on another
trusted host, or behind a separately reviewed secure transport.

## Public assistant tool contract

[`../contracts/mcp-tools.json`](../contracts/mcp-tools.json) defines an
optional, implementation-neutral MCP-style surface:

- `find_display_items` searches the operator-owned catalog and returns metadata
  only. It does not fetch media from the public internet.
- `queue_display` queues exactly one caption-only, emoji, or catalog reaction.
  Its UUID request ID makes retries idempotent.

These schemas can also be translated into another assistant's function or tool
format. MCP is a convenient option, not a requirement. Direct scripts and
automation systems can use the authenticated HTTP endpoints documented in
[`../bridge/README.md`](../bridge/README.md).

## Provider-neutral setup outline

1. Deploy and verify the bridge using an empty catalog and an isolated receiver
   before connecting any external assistant or automation.
2. Keep the administrator transport credential in the trusted adapter's
   operating-system credential store. Never place it in a prompt, chat,
   repository, mobile APK, catalog, URL, or assistant-visible configuration.
3. Map the integration's tool definitions to `find_display_items` and
   `queue_display`, preserving every input bound and the UUID request ID.
4. Expose only the minimum required bridge surface through a reviewed local or
   encrypted transport. Do not expose the bridge directly to the public
   internet merely to simplify setup.
5. Pair the receiver with a short-lived one-time code, then test caption, emoji,
   image, GIF, reconnect, and screen-off behavior in the intended environment.
6. Give the assistant or automation a clear policy for when reactions are
   appropriate, which catalog entries it may use, and whether human
   confirmation is required.

## Suitable integration sources

Examples include:

- hosted assistants such as ChatGPT or Claude;
- local models and agent frameworks;
- Home Assistant, Node-RED, or similar automation systems;
- monitoring and alerting services;
- scheduled jobs and ordinary command-line or server-side scripts;
- custom applications using the bridge's bounded HTTP contract.

Those products and services are not bundled, endorsed, or required by this
project. Operators are responsible for their providers' terms, network
security, credentials, media rights, and trigger policies.

## Delivery semantics

An accepted tool call means the reaction is queued durably. It does not prove
that the phone downloaded or displayed it. The bridge retains ordered delivery
until the paired receiver reports a matching displayed, dismissed, or failed
completion. Integrations should therefore say **queued** unless they separately
observe a receiver completion.

This distinction is especially important during Wi-Fi loss, receiver reboot,
or other temporary outages: a successful queue operation may intentionally be
displayed later.
