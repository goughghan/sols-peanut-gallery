# SPDX-License-Identifier: GPL-3.0-or-later

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from peanut_gallery_bridge.cli import main


class LocalQueueCommandTests(unittest.TestCase):
    def test_queue_local_uses_the_durable_validated_queue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "state"
            media = root / "media"
            state.mkdir()
            media.mkdir()
            catalog = root / "catalog.json"
            catalog.write_text('{"schema_version":1,"entries":[]}', encoding="utf-8")
            config = root / "bridge.json"
            config.write_text(json.dumps({
                "schema_version": 1,
                "listener": {
                    "bind_host": "127.0.0.1",
                    "bind_port": 8765,
                    "require_paired_device": True,
                },
                "storage": {
                    "state_directory": str(state),
                    "catalog_index": str(catalog),
                    "media_directory": str(media),
                },
                "queue": {"maximum_pending": 10, "retention_hours": 24},
                "limits": {
                    "maximum_request_bytes": 65536,
                    "maximum_media_bytes": 8388608,
                    "maximum_caption_characters": 180,
                },
                "security": {
                    "pairing_ttl_seconds": 300,
                    "credential_name": "transport-token",
                    "status_credential_name": "status-token",
                },
                "logging": {
                    "destination": "journald",
                    "level": "info",
                    "redact_sensitive_values": True,
                },
            }), encoding="utf-8")

            output = io.StringIO()
            with redirect_stdout(output):
                result = main([
                    "--config", str(config), "queue-local",
                    "--emoji", "🥜", "--caption", "Local smoke test",
                ])

            self.assertEqual(0, result)
            response = json.loads(output.getvalue())
            self.assertEqual("queued", response["status"])
            self.assertFalse(response["duplicate"])
            with sqlite3.connect(state / "bridge.sqlite3") as database:
                row = database.execute(
                    "SELECT sequence, content_json FROM deliveries"
                ).fetchone()
            self.assertEqual(1, row[0])
            self.assertEqual(
                {"kind": "text", "emoji": "🥜", "caption": "Local smoke test"},
                json.loads(row[1]),
            )


if __name__ == "__main__":
    unittest.main()
