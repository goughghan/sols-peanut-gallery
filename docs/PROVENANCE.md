# Clean-room provenance policy

## Purpose

This file defines how the public implementation remains independent while
retaining legitimate knowledge gained from feasibility testing.

## Allowed inputs

- The observable requirements in `REQUIREMENTS.md`.
- Public Android, Python, systemd, MCP, and tunnel-provider documentation.
- Black-box acceptance results describing inputs and visible outputs.
- Newly created test fixtures with clear redistribution rights.
- General programming knowledge and independently selected dependencies.

## Disallowed inputs during implementation

- Source from `rsms/esp32-dot` unless the author later supplies an explicit
  compatible license.
- Source from the private feasibility APK or bridge.
- Decompiled APKs, copied identifiers, copied prose, artwork, or distinctive
  internal organization from either implementation.
- The private media catalog, pairing records, tunnel key, signing key, or logs.

## Implementation procedure

1. Freeze and review the neutral requirements and acceptance criteria.
2. Give a fresh implementation environment only this staging tree and public
   platform documentation.
3. Author every executable source file anew and record its dependency license.
4. Run automated contract tests, followed by device-level black-box tests.
5. Perform a provenance, secret, dependency, and license audit before the first
   public commit.
6. If permission later arrives, treat any proposed incorporation of the
   original project as a separate, explicitly licensed decision; do not mix it
   into the clean-room history automatically.

## 2026-11-22 implementation record

All executable bridge, Android, test, and build source in this tree was newly
authored during the clean-room pass from the allowed documents and ordinary
platform knowledge/documentation. The prohibited project, private prototype,
prior Android projects, bridge source, private media/catalog, and generated APK
directories were not consulted. Local verification used an isolated Android
SDK build environment and deliberately created one-pixel test images only.

## Attribution

The README acknowledgment credits the original proof of concept as inspiration
without claiming endorsement, contribution, or included source.
