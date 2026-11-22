# Contributing

This project welcomes reviewed contributions after the independent public
implementation begins.

## Clean-room boundary

- Work only from this repository, its issue descriptions, public platform
  documentation, and independently created tests.
- Do not submit code, assets, wording, or internal organization copied from an
  unlicensed project or the private feasibility prototype.
- Identify all third-party dependencies and their licenses.
- Do not submit private media, personal information, credentials, logs, or
  operator configuration.

## Development expectations

- Add or update tests for behavior changes.
- Keep inputs and outputs bounded.
- Preserve ordered, acknowledged delivery and request idempotency.
- Keep the base APK and repository media-free.
- Run `python -m unittest discover -s tests -v` before opening a change.

## AI-assisted contributions

AI-assisted contributions are welcome when the contributor reviews and takes
responsibility for the result. Disclose material AI assistance in the change
description, verify provenance, and do not assume that generated code is free
of licensing or security problems.

## License

Unless explicitly stated otherwise, submitted original code is intended for
distribution under `GPL-3.0-or-later`.
