# SPDX-License-Identifier: GPL-3.0-or-later

import base64
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bridge" / "src"))

from peanut_gallery_bridge.catalog import Catalog, CatalogError  # noqa: E402
from peanut_gallery_bridge.media import (  # noqa: E402
    MediaError,
    inspect_media_bytes,
    safe_media_path,
    verify_media_bytes,
)


GIF_1X1 = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==")
JPEG_1X1 = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgK"
    "CgkICQkKDA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2wBDAQMDAwQDBAgEBAgQCwkL"
    "EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAAR"
    "CAABAAEDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACP/EABQQAQAAAAAAAAAAAAAAAAAA"
    "AAD/xAAVAQEBAAAAAAAAAAAAAAAAAAAGB//EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhED"
    "EQA/AD0uBa//2Q=="
)


class MediaSecurityTests(unittest.TestCase):
    def test_valid_gif_metadata_and_hash_are_verified(self):
        info = inspect_media_bytes(GIF_1X1)
        self.assertEqual("image/gif", info.mime_type)
        self.assertEqual((1, 1), (info.width, info.height))
        self.assertEqual(1, info.frame_count)
        verify_media_bytes(GIF_1X1, info)
        altered = bytearray(GIF_1X1)
        altered[-2] ^= 1
        with self.assertRaises(MediaError):
            verify_media_bytes(bytes(altered), info)

    def test_created_valid_jpeg_metadata_and_hash_are_verified(self):
        info = inspect_media_bytes(JPEG_1X1)
        self.assertEqual("image/jpeg", info.mime_type)
        self.assertEqual((1, 1), (info.width, info.height))
        verify_media_bytes(JPEG_1X1, info)
        altered = bytearray(JPEG_1X1)
        altered[-10] ^= 1
        with self.assertRaises(MediaError):
            verify_media_bytes(bytes(altered), info)

    def test_wrong_mime_and_oversize_are_rejected(self):
        with self.assertRaises(MediaError):
            inspect_media_bytes(b"not-an-image")
        with self.assertRaises(MediaError):
            inspect_media_bytes(GIF_1X1, maximum_bytes=len(GIF_1X1) - 1)

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("../escape.gif", "/tmp/escape.gif", "folder/file.gif", ".."):
                with self.subTest(name=name), self.assertRaises(MediaError):
                    safe_media_path(root, name)

    def test_catalog_derives_delivery_metadata_from_local_media(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            media = root / "media"
            media.mkdir()
            (media / "created-test.gif").write_bytes(GIF_1X1)
            index = root / "catalog.json"
            index.write_text(json.dumps({
                "schema_version": 1,
                "entries": [{
                    "id": "created-test",
                    "title": "Created test fixture",
                    "file_name": "created-test.gif",
                    "tags": ["test"],
                    "caption_seeds": [],
                }],
            }), encoding="utf-8")
            catalog = Catalog.load(index, media, 8_388_608)
            entry = catalog.by_identifier["created-test"]
            self.assertEqual("image/gif", entry.media.mime_type)
            self.assertEqual(64, len(entry.media.sha256))

    def test_catalog_rejects_unsafe_file_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            index = root / "catalog.json"
            index.write_text(json.dumps({
                "schema_version": 1,
                "entries": [{
                    "id": "escape",
                    "title": "Escape",
                    "file_name": "../escape.gif",
                    "tags": ["test"],
                    "caption_seeds": [],
                }],
            }), encoding="utf-8")
            with self.assertRaises(CatalogError):
                Catalog.load(index, root / "media", 8_388_608)
