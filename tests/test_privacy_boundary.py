# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PrivacyBoundaryTests(unittest.TestCase):
    def source_files(self):
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT)
            excluded = {".git", ".gradle", ".venv", "__pycache__", "build", "dist", "local-artifacts"}
            if any(part in excluded or part.endswith(".egg-info") for part in relative.parts):
                continue
            yield path

    def test_tree_contains_no_private_network_address_or_host_inventory(self):
        private_ipv4 = re.compile(
            r"(?<![0-9])(?:10(?:\.[0-9]{1,3}){3}|192\.168(?:\.[0-9]{1,3}){2}|"
            r"172\.(?:1[6-9]|2[0-9]|3[01])(?:\.[0-9]{1,3}){2})(?![0-9])"
        )
        local_user = Path.home().name
        forbidden_inventory = (
            "sol-" + "peanut-pi",
            "/var/" + "home/",
            f"/home/{local_user}/",
            "/var/" + "home/" + local_user + "/",
            "SHA256:" + "QTdC2",
        )
        for path in self.source_files():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(private_ipv4.search(text))
                self.assertFalse(any(value in text for value in forbidden_inventory))

    def test_no_media_or_signing_material_is_committed(self):
        forbidden_suffixes = {
            ".gif", ".jpg", ".jpeg", ".png", ".webp", ".mp4", ".jks", ".keystore", ".p12", ".pem", ".key"
        }
        found = [
            str(path.relative_to(ROOT)) for path in self.source_files()
            if path.suffix.lower() in forbidden_suffixes
        ]
        self.assertEqual([], found)

    def test_executable_sources_have_gpl_identifiers(self):
        executable_suffixes = {".py", ".java", ".sh", ".gradle"}
        missing = []
        for path in self.source_files():
            if path.suffix in executable_suffixes:
                first_lines = "\n".join(path.read_text(encoding="utf-8").splitlines()[:4])
                if "SPDX-License-Identifier: GPL-3.0-or-later" not in first_lines:
                    missing.append(str(path.relative_to(ROOT)))
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
