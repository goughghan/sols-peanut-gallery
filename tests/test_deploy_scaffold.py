# SPDX-License-Identifier: GPL-3.0-or-later

import json
from pathlib import Path
import subprocess
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
            self.assertNotIn("systemctl enable", text)
            self.assertNotIn("systemctl start", text)
            self.assertNotIn("systemctl restart", text)

    def test_example_config_is_bounded_and_contains_no_secret(self):
        path = DEPLOY / "config" / "bridge.example.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(config["listener"]["require_paired_device"])
        self.assertLessEqual(config["limits"]["maximum_media_bytes"], 8 * 1024 * 1024)
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in ("192.168.", "sk-", "tunnel_", "token\":"):
            self.assertNotIn(forbidden, text)

    def test_service_remains_an_unresolved_hardened_template(self):
        unit = (DEPLOY / "systemd" / "sol-peanut-gallery.service.in").read_text(
            encoding="utf-8")
        self.assertIn("ExecStart=@EXECUTABLE@", unit)
        self.assertIn("@ENCRYPTED_CREDENTIAL_FILE@", unit)
        self.assertIn("NoNewPrivileges=true", unit)
        self.assertIn("ProtectSystem=strict", unit)


if __name__ == "__main__":
    unittest.main()
