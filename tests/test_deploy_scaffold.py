# SPDX-License-Identifier: GPL-3.0-or-later

import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "deploy"


class DeployScaffoldTests(unittest.TestCase):
    def test_shell_scripts_are_syntactically_valid(self):
        for script in sorted((DEPLOY / "bin").glob("*.sh")):
            with self.subTest(script=script.name):
                subprocess.run(["bash", "-n", str(script)], check=True)

    def test_layout_is_dry_run_by_default(self):
        result = subprocess.run(
            [str(DEPLOY / "bin" / "create-layout.sh")],
            check=True, capture_output=True, text=True)
        self.assertIn("mode=dry-run", result.stdout)
        self.assertIn("no changes made", result.stdout)

    def test_scaffold_never_activates_a_service(self):
        for script in sorted((DEPLOY / "bin").glob("*.sh")):
            text = script.read_text(encoding="utf-8")
            self.assertIsNone(re.search(
                r"(?m)^\s*systemctl\s+(?:enable|start|restart)\b", text))

    def test_release_installer_is_dry_run_first(self):
        with tempfile.TemporaryDirectory() as temporary:
            wheel = Path(temporary) / "sol_peanut_gallery_bridge-1.0.0-py3-none-any.whl"
            wheel.write_bytes(b"dry-run fixture")
            result = subprocess.run(
                [str(DEPLOY / "bin" / "install-bridge.sh"), "--dry-run", str(wheel)],
                check=True, capture_output=True, text=True)
        self.assertIn("mode=dry-run", result.stdout)
        self.assertIn("no changes made", result.stdout)
        self.assertIn("venv-1.0.0", result.stdout)

    def test_example_config_is_bounded_and_contains_no_secret(self):
        path = DEPLOY / "config" / "bridge.example.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(config["listener"]["require_paired_device"])
        self.assertLessEqual(config["limits"]["maximum_media_bytes"], 8 * 1024 * 1024)
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in ("192.168.", "sk-", "tunnel_", "token\":"):
            self.assertNotIn(forbidden, text)

        watch_path = DEPLOY / "config" / "battery-watch.example.json"
        watch = json.loads(watch_path.read_text(encoding="utf-8"))
        self.assertEqual("https", watch["status_url"].split(":", 1)[0])
        self.assertGreater(watch["recover_percent"], watch["low_percent"])
        self.assertIsInstance(watch["notification_command"], list)
        self.assertNotIn("status-token\":", watch_path.read_text(encoding="utf-8").lower())

    def test_service_remains_an_unresolved_hardened_template(self):
        unit = (DEPLOY / "systemd" / "sol-peanut-gallery.service.in").read_text(
            encoding="utf-8")
        self.assertIn("ExecStart=@EXECUTABLE@", unit)
        self.assertIn("@ENCRYPTED_CREDENTIAL_FILE@", unit)
        self.assertIn("@ENCRYPTED_STATUS_CREDENTIAL_FILE@", unit)
        self.assertIn("NoNewPrivileges=true", unit)
        self.assertIn("ProtectSystem=strict", unit)

        ready = (DEPLOY / "systemd" / "sol-peanut-gallery.service").read_text(
            encoding="utf-8")
        self.assertNotIn("@", ready)
        self.assertIn("/opt/sol-peanut-gallery/current/bin/sol-peanut-gallery", ready)
        self.assertIn("LoadCredentialEncrypted=transport-token:", ready)
        self.assertIn("LoadCredentialEncrypted=status-token:", ready)
        self.assertNotIn("Environment=", ready)

        watcher = (DEPLOY / "systemd" / "sol-peanut-gallery-battery-watch.service.in").read_text(
            encoding="utf-8")
        self.assertIn("ExecStart=@EXECUTABLE@", watcher)
        self.assertIn("@CONFIG_FILE@", watcher)
        self.assertNotIn("systemctl enable", watcher)

    def test_tunnel_service_is_separate_hardened_and_credential_backed(self):
        unit = (DEPLOY / "systemd" / "sol-peanut-gallery-tunnel.service.in").read_text(
            encoding="utf-8"
        )
        self.assertIn("@TUNNEL_CLIENT@", unit)
        self.assertIn("@TUNNEL_ID@", unit)
        self.assertIn("@ENCRYPTED_CONTROL_PLANE_CREDENTIAL@", unit)
        self.assertIn("@ENCRYPTED_TRANSPORT_CREDENTIAL@", unit)
        self.assertIn("LoadCredentialEncrypted=", unit)
        self.assertIn("--mcp.server-url", unit)
        self.assertIn("http://127.0.0.1:@BRIDGE_PORT@/mcp", unit)
        self.assertIn("file:%d/transport-token", unit)
        self.assertIn("file:%d/CONTROL_PLANE_API_KEY", unit)
        self.assertIn("Restart=always", unit)
        self.assertIn("Wants=sol-peanut-gallery.service", unit)
        self.assertNotIn("Requires=sol-peanut-gallery.service", unit)
        self.assertIn("NoNewPrivileges=true", unit)
        self.assertNotIn("WantedBy=default.target", unit)


if __name__ == "__main__":
    unittest.main()
