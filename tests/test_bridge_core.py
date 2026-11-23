# SPDX-License-Identifier: GPL-3.0-or-later

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge" / "src"))

from peanut_gallery_bridge.catalog import Catalog  # noqa: E402
from peanut_gallery_bridge.config import BridgeConfig  # noqa: E402
from peanut_gallery_bridge.core import BridgeCore, ValidationError  # noqa: E402
from peanut_gallery_bridge.storage import (  # noqa: E402
    AuthenticationError,
    ConflictError,
    Storage,
)


class BridgeTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.catalog_index = self.root / "catalog.json"
        self.catalog_index.write_text('{"schema_version":1,"entries":[]}', encoding="utf-8")
        self.media_directory = self.root / "media"
        self.media_directory.mkdir()
        self.config = BridgeConfig(
            bind_host="127.0.0.1",
            bind_port=8765,
            state_directory=self.root / "state",
            catalog_index=self.catalog_index,
            media_directory=self.media_directory,
            maximum_pending=100,
        )
        self.storage = Storage(self.config.database_path)
        self.catalog = Catalog.load(self.catalog_index, self.media_directory, 8_388_608)
        self.core = BridgeCore(self.config, self.storage, self.catalog)

    def tearDown(self):
        self.temporary.cleanup()

    def pair_receiver(self):
        code = self.core.create_pairing_code()["code"]
        return self.core.pair({"code": code, "device_label": "Test receiver"})

    @staticmethod
    def request(identifier: int, caption: str = "Test"):
        return {
            "request_id": str(uuid.UUID(int=identifier)),
            "caption": caption,
            "display_seconds": 3,
        }


class PairingTests(BridgeTestCase):
    def test_pairing_code_is_one_time_and_receiver_can_be_revoked(self):
        pairing = self.core.create_pairing_code()
        receiver = self.core.pair({"code": pairing["code"], "device_label": "Dedicated display"})
        self.assertTrue(receiver["receiver_token"].startswith("pg_rt_"))
        with self.assertRaises(AuthenticationError):
            self.core.pair({"code": pairing["code"], "device_label": "Replay"})
        receiver_id = self.storage.authenticate_receiver(receiver["receiver_token"])
        self.assertTrue(self.storage.revoke_receiver(receiver_id))
        with self.assertRaises(AuthenticationError):
            self.storage.authenticate_receiver(receiver["receiver_token"])

    def test_expired_pairing_code_is_rejected(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        code, _ = self.storage.create_pairing_code(30, now=start)
        with self.assertRaises(AuthenticationError):
            self.storage.pair(code, "Late receiver", now=start + timedelta(seconds=31))

    def test_invalid_receiver_token_is_rejected(self):
        with self.assertRaises(AuthenticationError):
            self.storage.authenticate_receiver("pg_rt_" + "x" * 43)

    def test_receiver_reports_bounded_battery_status(self):
        receiver = self.pair_receiver()
        recorded = self.core.report_receiver_status(
            receiver["receiver_token"],
            {"battery_percent": 18, "charging": False},
        )
        self.assertEqual("recorded", recorded["status"])
        statuses = self.core.receiver_status()["receivers"]
        self.assertEqual(1, len(statuses))
        self.assertEqual(18, statuses[0]["battery_percent"])
        self.assertFalse(statuses[0]["charging"])

        with self.assertRaises(ValidationError):
            self.core.report_receiver_status(
                receiver["receiver_token"],
                {"battery_percent": True, "charging": False},
            )
        with self.assertRaises(ValidationError):
            self.core.report_receiver_status(
                receiver["receiver_token"],
                {"battery_percent": 101, "charging": False},
            )

        receiver_id = self.storage.authenticate_receiver(receiver["receiver_token"])
        self.storage.revoke_receiver(receiver_id)
        self.assertEqual([], self.core.receiver_status()["receivers"])


class QueueTests(BridgeTestCase):
    def test_duplicate_request_id_returns_original_delivery(self):
        first, duplicate_one = self.core.queue_display(self.request(1, "First value"))
        second, duplicate_two = self.core.queue_display(self.request(1, "Changed retry value"))
        self.assertFalse(duplicate_one)
        self.assertTrue(duplicate_two)
        self.assertEqual(first["delivery_id"], second["delivery_id"])
        self.assertEqual(1, self.storage.pending_count())

    def test_concurrent_requests_receive_one_stable_sequence_each(self):
        with ThreadPoolExecutor(max_workers=8) as workers:
            results = list(workers.map(lambda number: self.core.queue_display(self.request(number))[0], range(1, 31)))
        sequences = sorted(result["sequence"] for result in results)
        self.assertEqual(list(range(1, 31)), sequences)
        self.assertEqual(30, len({result["delivery_id"] for result in results}))

    def test_restart_preserves_unacknowledged_delivery(self):
        receiver = self.pair_receiver()
        queued, _ = self.core.queue_display(self.request(1))
        reopened = BridgeCore(self.config, Storage(self.config.database_path), self.catalog)
        delivered = reopened.next_delivery(receiver["receiver_token"])
        self.assertEqual(queued["delivery_id"], delivered["delivery_id"])
        self.assertEqual(delivered, reopened.next_delivery(receiver["receiver_token"]))

    def test_revocation_releases_unfinished_delivery_for_new_receiver(self):
        first = self.pair_receiver()
        self.core.queue_display(self.request(1))
        claimed = self.core.next_delivery(first["receiver_token"])
        first_id = self.storage.authenticate_receiver(first["receiver_token"])
        self.assertTrue(self.storage.revoke_receiver(first_id))
        second = self.pair_receiver()
        redelivered = self.core.next_delivery(second["receiver_token"])
        self.assertEqual(claimed["delivery_id"], redelivered["delivery_id"])

    def test_acknowledgment_must_match_claimed_delivery(self):
        receiver = self.pair_receiver()
        self.core.queue_display(self.request(1))
        delivery = self.core.next_delivery(receiver["receiver_token"])
        body = {
            "delivery_id": delivery["delivery_id"],
            "sequence": delivery["sequence"],
            "outcome": "displayed",
            "completed_at": "2026-01-01T00:00:00Z",
        }
        wrong = dict(body, sequence=delivery["sequence"] + 1)
        with self.assertRaises(ConflictError):
            self.core.acknowledge(receiver["receiver_token"], wrong)
        result = self.core.acknowledge(receiver["receiver_token"], body)
        self.assertFalse(result["duplicate"])
        repeated = self.core.acknowledge(receiver["receiver_token"], body)
        self.assertTrue(repeated["duplicate"])
        self.assertIsNone(self.core.next_delivery(receiver["receiver_token"]))

    def test_empty_catalog_still_allows_text_and_emoji(self):
        text, _ = self.core.queue_display(self.request(1, "Caption only"))
        emoji, _ = self.core.queue_display({
            "request_id": str(uuid.UUID(int=2)),
            "emoji": "🙂",
        })
        self.assertEqual(1, text["sequence"])
        self.assertEqual(2, emoji["sequence"])
        with self.assertRaises(ValidationError):
            self.core.queue_display({
                "request_id": str(uuid.UUID(int=3)),
                "reaction_id": "not-present",
            })

    def test_pending_queue_limit_is_enforced(self):
        bounded = BridgeCore(replace(self.config, maximum_pending=1), self.storage, self.catalog)
        bounded.queue_display(self.request(1))
        with self.assertRaises(ConflictError):
            bounded.queue_display(self.request(2))
