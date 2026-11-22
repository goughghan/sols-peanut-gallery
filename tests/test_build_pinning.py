# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
import hashlib
import xml.etree.ElementTree as ET
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BuildPinningTests(unittest.TestCase):
    def test_gradle_wrapper_distribution_and_checksum_are_pinned(self):
        properties = (ROOT / "android" / "gradle" / "wrapper" / "gradle-wrapper.properties").read_text(
            encoding="utf-8")
        self.assertIn("gradle-8.9-bin.zip", properties)
        self.assertIn(
            "distributionSha256Sum=d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab",
            properties,
        )
        wrapper_jar = ROOT / "android" / "gradle" / "wrapper" / "gradle-wrapper.jar"
        self.assertTrue(wrapper_jar.is_file())
        self.assertEqual(
            "498495120a03b9a6ab5d155f5de3c8f0d986a449153702fb80fc80e134484f17",
            hashlib.sha256(wrapper_jar.read_bytes()).hexdigest(),
        )

    def test_dependency_verification_metadata_is_present(self):
        path = ROOT / "android" / "gradle" / "verification-metadata.xml"
        tree = ET.parse(path)
        namespace = {"v": "https://schema.gradle.org/dependency-verification"}
        components = tree.findall(".//v:component", namespace)
        checksums = tree.findall(".//v:sha256", namespace)
        self.assertGreater(len(components), 10)
        self.assertGreater(len(checksums), 10)


if __name__ == "__main__":
    unittest.main()
