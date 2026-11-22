# SPDX-License-Identifier: GPL-3.0-or-later

import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge" / "src"))

from peanut_gallery_bridge.catalog import Catalog  # noqa: E402
from peanut_gallery_bridge.config import BridgeConfig  # noqa: E402
from peanut_gallery_bridge.core import BridgeCore  # noqa: E402
from peanut_gallery_bridge.http_api import BridgeHTTPServer  # noqa: E402
from peanut_gallery_bridge.storage import Storage  # noqa: E402


class HttpIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        index = root / "catalog.json"
        index.write_text('{"schema_version":1,"entries":[]}', encoding="utf-8")
        media = root / "media"
        media.mkdir()
        self.config = BridgeConfig(
            bind_host="127.0.0.1", bind_port=0, state_directory=root / "state",
            catalog_index=index, media_directory=media,
        )
        catalog = Catalog.load(index, media, self.config.maximum_media_bytes)
        storage = Storage(self.config.database_path)
        core = BridgeCore(self.config, storage, catalog)
        self.admin_token = "admin-test-token-with-at-least-32-characters"
        self.server = BridgeHTTPServer(("127.0.0.1", 0), core, catalog, self.config, self.admin_token)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def request(self, method, path, body=None, token=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_address[1], timeout=3)
        headers = {}
        encoded = None
        if body is not None:
            encoded = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        connection.request(method, path, body=encoded, headers=headers)
        response = connection.getresponse()
        data = response.read()
        connection.close()
        return response.status, (json.loads(data) if data else None)

    def test_authenticated_pair_queue_deliver_and_ack_flow(self):
        status, pairing = self.request("POST", "/v1/admin/pairing-codes", {}, self.admin_token)
        self.assertEqual(201, status)
        status, receiver = self.request("POST", "/v1/pair", {
            "code": pairing["code"], "device_label": "HTTP test receiver",
        })
        self.assertEqual(201, status)
        request_id = str(uuid.uuid4())
        status, queued = self.request("POST", "/v1/tools/queue-display", {
            "request_id": request_id, "emoji": "👀", "caption": "Integration test",
        }, self.admin_token)
        self.assertEqual(202, status)
        status, repeated = self.request("POST", "/v1/tools/queue-display", {
            "request_id": request_id, "emoji": "different retry",
        }, self.admin_token)
        self.assertEqual(200, status)
        self.assertTrue(repeated["duplicate"])
        self.assertEqual(queued["delivery_id"], repeated["delivery_id"])
        status, delivery = self.request("GET", "/v1/deliveries/next", token=receiver["receiver_token"])
        self.assertEqual(200, status)
        self.assertEqual("Integration test", delivery["content"]["caption"])
        status, acknowledged = self.request(
            "POST", "/v1/deliveries/" + delivery["delivery_id"] + "/ack", {
                "delivery_id": delivery["delivery_id"],
                "sequence": delivery["sequence"],
                "outcome": "displayed",
                "completed_at": "2026-01-01T00:00:00Z",
            }, receiver["receiver_token"])
        self.assertEqual(200, status)
        self.assertFalse(acknowledged["duplicate"])
        status, empty = self.request("GET", "/v1/deliveries/next", token=receiver["receiver_token"])
        self.assertEqual(204, status)
        self.assertIsNone(empty)

    def test_protected_endpoints_reject_missing_credentials(self):
        for method, path, body in (
            ("POST", "/v1/admin/pairing-codes", {}),
            ("POST", "/v1/tools/find-display-items", {"query": "test"}),
            ("GET", "/v1/deliveries/next", None),
        ):
            with self.subTest(path=path):
                status, response = self.request(method, path, body)
                self.assertEqual(401, status)
                self.assertEqual("unauthorized", response["error"])
