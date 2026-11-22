# Recorded decisions

## 2026-11-21

- Prepare an independent public implementation if the original author declines
  permission or does not respond.
- Do not publish the private feasibility implementation.
- Plan to license new original source under `GPL-3.0-or-later`.
- Keep all private reaction media outside the repository and APK.
- Publish a functional media-free APK after the clean-room implementation and
  release audit pass.
- Credit `rsms/esp32-dot` as inspiration without implying endorsement.
- Disclose ChatGPT's assistance prominently and identify Will as the human
  project owner, decision-maker, tester, and maintainer.
- Reserve project naming and visual identity separately from the source-code
  license.
- While permission is pending, prepare only an implementation-neutral,
  disabled Raspberry Pi deployment scaffold. It must contain no executable
  bridge, tunnel client, credentials, live addresses, service activation, or
  author-derived implementation.

## 2026-11-22

- Begin the independent implementation from this clean-room tree without
  consulting the acknowledged project's source or any private prototype.
- Use Python standard-library HTTP plus SQLite for a low-resource, ARMv7-capable
  bridge with no mandatory cloud database or runtime package dependency.
- Use a Java Android receiver with Android platform APIs and no third-party
  runtime library; retain Android 8.0 support while targeting API 35.
- Keep tool transport provider-neutral through authenticated bounded HTTP
  endpoints and the implementation-neutral tool definitions under `contracts/`.
- Remove machine-specific Pi access and inventory notes from the public tree;
  deployment evidence belongs outside a secret-free source release.
- Do not deploy, pair, restart, publish, or modify any live component during
  implementation. Stop at a locally built, tested side-by-side candidate.
- After physical burst testing exposed a stale activity completion, use a
  persisted active-delivery identity and a one-time completion claim rather
  than a timestamp alone. Use one full-screen notification launch path with
  per-delivery notification IDs, and cancel a notification only after the
  matching activity confirms that it opened.
