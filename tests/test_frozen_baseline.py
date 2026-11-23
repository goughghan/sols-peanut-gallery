# SPDX-License-Identifier: GPL-3.0-or-later

import hashlib
from pathlib import Path
import tarfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASELINES = [
    (
        ROOT / "docs" / "baselines" / "SOURCE-MANIFEST-TEST3-20261122.sha256",
        ROOT / "local-artifacts" / "controlled-device-test-20261122"
        / "sol-peanut-gallery-cleanroom-0.1.0-test3-source.tar.gz",
    ),
    (
        ROOT / "docs" / "baselines" / "SOURCE-MANIFEST-TEST8-20261123.sha256",
        ROOT / "local-artifacts" / "controlled-device-test-20261122"
        / "sol-peanut-gallery-cleanroom-0.1.0-test8-source.tar.gz",
    ),
]


class FrozenBaselineTests(unittest.TestCase):
    def manifest_entries(self, manifest):
        self.assertTrue(manifest.is_file())
        entries = {}
        for line in manifest.read_text(encoding="utf-8").splitlines():
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
        for manifest, _archive in BASELINES:
            with self.subTest(manifest=manifest.name):
                self.manifest_entries(manifest)

    def test_frozen_archive_matches_manifest_when_present(self):
        checked = 0
        for manifest, archive_path in BASELINES:
            if not archive_path.exists():
                continue
            entries = self.manifest_entries(manifest)
            with tarfile.open(archive_path, "r:gz") as archive:
                members = {member.name: member for member in archive.getmembers() if member.isfile()}
                for relative, expected in entries.items():
                    with self.subTest(archive=archive_path.name, path=relative):
                        self.assertIn(relative, members)
                        extracted = archive.extractfile(members[relative])
                        self.assertIsNotNone(extracted)
                        self.assertEqual(expected, hashlib.sha256(extracted.read()).hexdigest())
            checked += 1
        if checked == 0:
            self.skipTest("ignored frozen source archives are not present in this checkout")

    def test_sacrificial_apks_match_their_sidecars_when_present(self):
        directory = ROOT / "local-artifacts" / "controlled-device-test-20261122"
        artifacts = [
            "sol-peanut-gallery-receiver-test-0.1.0-test1.apk",
            "sol-peanut-gallery-receiver-test-0.1.0-test2.apk",
            "sol-peanut-gallery-receiver-test-0.1.0-test2-stable-signed.apk",
            "sol-peanut-gallery-receiver-test-0.1.0-test3-unsigned.apk",
            "sol-peanut-gallery-receiver-test-0.1.0-test8-unsigned.apk",
            "sol-peanut-gallery-receiver-test-0.1.0-test8-stable-signed.apk",
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
