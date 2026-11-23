# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge" / "src"))

from peanut_gallery_bridge.battery_watch import (  # noqa: E402
    BatteryWatch,
    BatteryWatchConfig,
    BatteryWatchError,
)


class BatteryWatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.config = BatteryWatchConfig(
            status_url="https://bridge.example.invalid/v1/status/receivers",
            token_file=root / "status-token",
            state_file=root / "state" / "battery.json",
            notification_command=("notify-test", "{title}", "{body}"),
            low_percent=20,
            recover_percent=25,
            stale_after_seconds=900,
            repeat_seconds=21_600,
            poll_seconds=300,
        )
        self.now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.temporary.cleanup()

    def payload(self, percent=18, charging=False, moment=None):
        timestamp = (moment or self.now).isoformat(timespec="seconds").replace("+00:00", "Z")
        return {"receivers": [{
            "receiver_id": "66666666-6666-4666-8666-666666666666",
            "device_label": "Example display",
            "battery_percent": percent,
            "charging": charging,
            "reported_at": timestamp,
        }]}

    def test_low_notification_is_deduplicated_and_resets_after_recovery(self):
        watch = BatteryWatch(self.config)
        self.assertEqual(1, len(watch.evaluate(self.payload(), now=self.now)))
        self.assertEqual([], watch.evaluate(self.payload(), now=self.now + timedelta(minutes=1)))
        self.assertEqual([], watch.evaluate(
            self.payload(percent=30, moment=self.now + timedelta(minutes=2)),
            now=self.now + timedelta(minutes=2),
        ))
        notifications = watch.evaluate(
            self.payload(percent=17, moment=self.now + timedelta(minutes=3)),
            now=self.now + timedelta(minutes=3),
        )
        self.assertEqual(17, notifications[0]["battery_percent"])

    def test_charging_and_stale_reports_do_not_notify(self):
        watch = BatteryWatch(self.config)
        self.assertEqual([], watch.evaluate(self.payload(charging=True), now=self.now))
        stale = self.payload(moment=self.now - timedelta(hours=1))
        self.assertEqual([], watch.evaluate(stale, now=self.now))

    def test_configuration_rejects_credentials_embedded_in_url(self):
        path = Path(self.temporary.name) / "config.json"
        path.write_text(
            '{"schema_version":1,'
            '"status_url":"https://token@example.invalid/v1/status/receivers",'
            '"token_file":"/tmp/token","state_file":"/tmp/state",'
            '"notification_command":["notify-test","{body}"]}',
            encoding="utf-8",
        )
        with self.assertRaises(BatteryWatchError):
            BatteryWatchConfig.from_file(path)


if __name__ == "__main__":
    unittest.main()
