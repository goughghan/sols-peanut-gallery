# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
import uuid

from .catalog import Catalog, CatalogError
from .config import BridgeConfig, ConfigError
from .core import BridgeCore
from .http_api import BridgeHTTPServer
from .storage import Storage


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="sol-peanut-gallery")
    result.add_argument("--config", required=True, type=Path, help="path to non-secret bridge JSON configuration")
    result.add_argument("--version", action="version", version="sol-peanut-gallery 0.1.0")
    subcommands = result.add_subparsers(dest="command", required=True)
    subcommands.add_parser("serve", help="run the authenticated bridge HTTP service")
    subcommands.add_parser("validate-catalog", help="validate the configured operator catalog and media")
    subcommands.add_parser("pairing-code", help="create one short-lived, one-time receiver pairing code")
    subcommands.add_parser("receivers", help="list receiver identifiers and revocation state")
    revoke = subcommands.add_parser("revoke-receiver", help="revoke one receiver credential")
    revoke.add_argument("receiver_id", help="receiver UUID shown by the receivers command")
    return result


def load(config_path: Path) -> tuple[BridgeConfig, Catalog]:
    config = BridgeConfig.from_file(config_path)
    catalog = Catalog.load(config.catalog_index, config.media_directory, config.maximum_media_bytes)
    return config, catalog


def main(arguments: list[str] | None = None) -> int:
    options = parser().parse_args(arguments)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        config, catalog = load(options.config)
        if options.command == "validate-catalog":
            print(f"catalog_valid=yes entries={len(catalog.entries)}")
            return 0
        storage = Storage(config.database_path)
        core = BridgeCore(config, storage, catalog)
        if options.command == "pairing-code":
            print(json.dumps(core.create_pairing_code(), separators=(",", ":")))
            return 0
        if options.command == "receivers":
            print(json.dumps({"receivers": storage.list_receivers()}, separators=(",", ":")))
            return 0
        if options.command == "revoke-receiver":
            try:
                receiver_id = str(uuid.UUID(options.receiver_id))
            except ValueError:
                print("error: receiver_id must be a canonical UUID", file=sys.stderr)
                return 2
            if receiver_id != options.receiver_id.lower() or not storage.revoke_receiver(receiver_id):
                print("error: active receiver does not exist", file=sys.stderr)
                return 3
            print(json.dumps({"status": "revoked", "receiver_id": receiver_id}, separators=(",", ":")))
            return 0
        admin_token = config.read_admin_token()
        server = BridgeHTTPServer((config.bind_host, config.bind_port), core, catalog, config, admin_token)
        logging.getLogger(__name__).info("bridge listening on %s:%d", config.bind_host, config.bind_port)
        try:
            server.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0
    except (ConfigError, CatalogError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
