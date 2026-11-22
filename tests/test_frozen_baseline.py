# SPDX-License-Identifier: GPL-3.0-or-later

import hashlib
from pathlib import Path
import tarfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "baselines" / "SOURCE-MANIFEST-TEST3-20261122.sha256"
ARCHIVE = (
    ROOT
    / "local-artifacts"
    / "controlled-device-test-20261122"
    / "sol-peanut-gallery-cleanroom-0.1.0-test3-source.tar.gz"
)


class FrozenBaselineTests(unittest.TestCase):
    def manifest_entries(self):
        self.assertTrue(MANIFEST.is_file())
        entries = {}
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            digest, relative = line.split("  ", 1)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            self.assertRegex(relative, r"^\./[^/].*$")
            self.assertNotIn("..", Path(relative).parts)
            self.assertNotIn(relative, entries)
            entries[relative] = digest
        self.assertGreater(len(entries), 50)
        return entries

    def test_frozen_manifest_is_well_formed(self):
        self.manifest_entries()

    def test_frozen_archive_matches_manifest_when_present(self):
        if not ARCHIVE.exists():
            self.skipTest("ignored frozen source archive is not present in this checkout")
        entries = self.manifest_entries()
        with tarfile.open(ARCHIVE, "r:gz") as archive:
            members = {member.name: member for member in archive.getmembers() if member.isfile()}
            for relative, expected in entries.items():
                with self.subTest(path=relative):
                    self.assertIn(relative, members)
                    extracted = archive.extractfile(members[relative])
                    self.assertIsNotNone(extracted)
                    self.assertEqual(expected, hashlib.sha256(extracted.read()).hexdigest())

    def test_sacrificial_apks_match_their_sidecars_when_present(self):
        directory = ROOT / "local-artifacts" / "controlled-device-test-20261122"
        artifacts = [
            "sol-peanut-gallery-receiver-test-0.1.0-test1.apk",
            "sol-peanut-gallery-receiver-test-0.1.0-test2.apk",
            "sol-peanut-gallery-receiver-test-0.1.0-test2-stable-signed.apk",
            "sol-peanut-gallery-receiver-test-0.1.0-test3-unsigned.apk",
        ]
        checked = 0
        for filename in artifacts:
            apk = directory / filename
            if not apk.exists():
                continue
            sidecar = directory / f"{filename}.sha256"
            with self.subTest(artifact=filename):
                self.assertTrue(sidecar.is_file())
                expected = sidecar.read_text(encoding="utf-8").split()[0]
                self.assertEqual(expected, hashlib.sha256(apk.read_bytes()).hexdigest())
            checked += 1
        if checked == 0:
            self.skipTest("ignored local test artifacts are not present in this checkout")


if __name__ == "__main__":
    unittest.main()
