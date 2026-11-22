# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
from pathlib import Path
import struct


class MediaError(ValueError):
    pass


@dataclass(frozen=True)
class MediaInfo:
    mime_type: str
    byte_count: int
    sha256: str
    width: int
    height: int
    frame_count: int | None = None
    duration_ms: int | None = None


def safe_media_path(directory: Path, file_name: str) -> Path:
    if not file_name or file_name in {".", ".."} or Path(file_name).name != file_name:
        raise MediaError("media file name is not a single safe path component")
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789._-" for character in file_name):
        raise MediaError("media file name contains a forbidden character")
    candidate = (directory / file_name).resolve()
    root = directory.resolve()
    if candidate.parent != root:
        raise MediaError("media path escapes its configured directory")
    return candidate


def inspect_media(path: Path, maximum_bytes: int) -> MediaInfo:
    try:
        with path.open("rb") as source:
            data = source.read(maximum_bytes + 1)
    except OSError as error:
        raise MediaError(f"cannot read media: {error}") from error
    if not data:
        raise MediaError("media is empty")
    if len(data) > maximum_bytes:
        raise MediaError("media exceeds the configured byte limit")
    return inspect_media_bytes(data, maximum_bytes)


def inspect_media_bytes(data: bytes, maximum_bytes: int = 8_388_608) -> MediaInfo:
    if not data or len(data) > maximum_bytes:
        raise MediaError("media size is outside the permitted range")
    digest = hashlib.sha256(data).hexdigest()
    if data.startswith((b"GIF87a", b"GIF89a")):
        width, height, frames, duration = _inspect_gif(data)
        return MediaInfo("image/gif", len(data), digest, width, height, frames, duration)
    if data.startswith(b"\xff\xd8"):
        width, height = _inspect_jpeg(data)
        return MediaInfo("image/jpeg", len(data), digest, width, height)
    raise MediaError("only verified JPEG and GIF media is permitted")


def verify_media_bytes(data: bytes, expected: MediaInfo, maximum_bytes: int = 8_388_608) -> None:
    actual = inspect_media_bytes(data, maximum_bytes)
    if actual.mime_type != expected.mime_type:
        raise MediaError("media MIME signature does not match metadata")
    if actual.byte_count != expected.byte_count:
        raise MediaError("media byte count does not match metadata")
    if not hmac.compare_digest(actual.sha256, expected.sha256):
        raise MediaError("media SHA-256 does not match metadata")
    if (actual.width, actual.height) != (expected.width, expected.height):
        raise MediaError("media dimensions do not match metadata")


def _dimensions(width: int, height: int) -> tuple[int, int]:
    if not 1 <= width <= 8_192 or not 1 <= height <= 8_192:
        raise MediaError("media dimensions are outside the permitted range")
    if width * height > 33_554_432:
        raise MediaError("decoded media pixel count is too large")
    return width, height


def _inspect_gif(data: bytes) -> tuple[int, int, int, int]:
    if len(data) < 14:
        raise MediaError("truncated GIF")
    width, height = _dimensions(*struct.unpack_from("<HH", data, 6))
    packed = data[10]
    offset = 13
    if packed & 0x80:
        offset += 3 * (2 ** ((packed & 0x07) + 1))
    frames = 0
    duration_ms = 0
    pending_delay_cs = 0
    trailer_seen = False
    while offset < len(data):
        marker = data[offset]
        offset += 1
        if marker == 0x3B:
            trailer_seen = True
            break
        if marker == 0x21:
            if offset >= len(data):
                raise MediaError("truncated GIF extension")
            label = data[offset]
            offset += 1
            if label == 0xF9:
                if offset + 6 > len(data) or data[offset] != 4:
                    raise MediaError("invalid GIF graphics control extension")
                pending_delay_cs = struct.unpack_from("<H", data, offset + 2)[0]
                offset += 6
            else:
                offset = _skip_gif_sub_blocks(data, offset)
            continue
        if marker != 0x2C or offset + 9 > len(data):
            raise MediaError("invalid GIF block")
        frame_width, frame_height = struct.unpack_from("<HH", data, offset + 4)
        _dimensions(frame_width, frame_height)
        image_packed = data[offset + 8]
        offset += 9
        if image_packed & 0x80:
            offset += 3 * (2 ** ((image_packed & 0x07) + 1))
        if offset >= len(data):
            raise MediaError("truncated GIF image data")
        offset += 1
        offset = _skip_gif_sub_blocks(data, offset)
        frames += 1
        if frames > 10_000:
            raise MediaError("GIF has too many frames")
        duration_ms += max(pending_delay_cs, 1) * 10
        pending_delay_cs = 0
    if not trailer_seen or frames < 1:
        raise MediaError("GIF is incomplete or has no frames")
    return width, height, frames, min(duration_ms, 300_000)


def _skip_gif_sub_blocks(data: bytes, offset: int) -> int:
    while True:
        if offset >= len(data):
            raise MediaError("truncated GIF sub-block")
        length = data[offset]
        offset += 1
        if length == 0:
            return offset
        if offset + length > len(data):
            raise MediaError("truncated GIF sub-block payload")
        offset += length


def _inspect_jpeg(data: bytes) -> tuple[int, int]:
    offset = 2
    sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset < len(data):
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker == 0xD9:
            break
        if marker in {0x01, *range(0xD0, 0xD8)}:
            continue
        if offset + 2 > len(data):
            raise MediaError("truncated JPEG segment")
        length = struct.unpack_from(">H", data, offset)[0]
        if length < 2 or offset + length > len(data):
            raise MediaError("invalid JPEG segment length")
        if marker in sof_markers:
            if length < 7:
                raise MediaError("invalid JPEG frame header")
            height, width = struct.unpack_from(">HH", data, offset + 3)
            return _dimensions(width, height)
        if marker == 0xDA:
            break
        offset += length
    raise MediaError("JPEG dimensions could not be verified")
