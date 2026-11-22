# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from datetime import datetime
import re
from typing import Any
import uuid

from .catalog import Catalog, ID_PATTERN
from .config import BridgeConfig
from .storage import Storage


class ValidationError(ValueError):
    pass


UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def valid_uuid(value: object) -> str:
    if not isinstance(value, str) or not UUID_RE.fullmatch(value):
        raise ValidationError("identifier must be a UUID")
    try:
        parsed = uuid.UUID(value)
    except ValueError as error:
        raise ValidationError("identifier must be a UUID") from error
    if str(parsed) != value.lower():
        raise ValidationError("identifier must use canonical UUID syntax")
    return value


def valid_timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValidationError("completed_at must be a UTC date-time")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValidationError("completed_at must be a UTC date-time") from error
    return value


class BridgeCore:
    def __init__(self, config: BridgeConfig, storage: Storage, catalog: Catalog) -> None:
        self.config = config
        self.storage = storage
        self.catalog = catalog

    def create_pairing_code(self) -> dict[str, str]:
        code, expires_at = self.storage.create_pairing_code(self.config.pairing_ttl_seconds)
        return {"code": code, "expires_at": expires_at}

    def pair(self, body: object) -> dict[str, str]:
        value = self._object(body, {"code", "device_label"})
        code = value.get("code")
        label = value.get("device_label")
        if not isinstance(code, str) or not re.fullmatch(r"[0-9]{6}", code):
            raise ValidationError("code must contain exactly six digits")
        if not isinstance(label, str) or not 1 <= len(label) <= 80 or any(ord(char) < 32 for char in label):
            raise ValidationError("device_label is invalid")
        return self.storage.pair(code, label)

    def queue_display(self, body: object) -> tuple[dict[str, object], bool]:
        allowed = {"request_id", "emoji", "reaction_id", "caption", "display_seconds"}
        value = self._object(body, allowed)
        request_id = valid_uuid(value.get("request_id"))
        display_seconds = value.get("display_seconds", 8)
        if isinstance(display_seconds, bool) or not isinstance(display_seconds, int) or not 3 <= display_seconds <= 30:
            raise ValidationError("display_seconds must be an integer from 3 through 30")
        sources = sum(key in value for key in ("emoji", "reaction_id"))
        caption_only = "caption" in value and sources == 0
        if sources != 1 and not caption_only:
            raise ValidationError("provide exactly one emoji, catalog reaction, or non-empty caption")
        caption = value.get("caption", "")
        if not isinstance(caption, str) or len(caption) > self.config.maximum_caption_characters:
            raise ValidationError("caption is invalid")
        if caption_only and not caption:
            raise ValidationError("caption-only reactions must not be empty")
        if "emoji" in value:
            emoji = value["emoji"]
            if not isinstance(emoji, str) or not 1 <= len(emoji) <= 16:
                raise ValidationError("emoji is invalid")
            content: dict[str, object] = {"kind": "text", "emoji": emoji}
            if "caption" in value:
                content["caption"] = caption
        elif "reaction_id" in value:
            reaction_id = value["reaction_id"]
            if not isinstance(reaction_id, str) or len(reaction_id) > 80 or not ID_PATTERN.fullmatch(reaction_id):
                raise ValidationError("reaction_id is invalid")
            entry = self.catalog.by_identifier.get(reaction_id)
            if entry is None:
                raise ValidationError("reaction_id is not present in the operator catalog")
            content = {
                "kind": "media",
                "caption": caption,
                "media_id": entry.media_id,
                "file_name": entry.file_name,
                "mime_type": entry.media.mime_type,
                "bytes": entry.media.byte_count,
                "sha256": entry.media.sha256,
                "width": entry.media.width,
                "height": entry.media.height,
            }
            if entry.media.frame_count is not None:
                content["frame_count"] = entry.media.frame_count
            if entry.media.duration_ms is not None:
                content["duration_ms"] = entry.media.duration_ms
        else:
            content = {"kind": "text", "caption": caption}
        delivery, duplicate = self.storage.queue(
            request_id, display_seconds, content, self.config.maximum_pending,
            self.config.retention_hours,
        )
        return {
            "status": "queued",
            "duplicate": duplicate,
            "delivery_id": delivery["delivery_id"],
            "sequence": delivery["sequence"],
        }, duplicate

    def find_display_items(self, body: object) -> dict[str, object]:
        value = self._object(body, {"query", "tags", "limit"})
        query = value.get("query")
        tags = value.get("tags")
        limit = value.get("limit", 5)
        if query is None and tags is None:
            raise ValidationError("query or tags is required")
        if query is not None and (not isinstance(query, str) or not 1 <= len(query) <= 120):
            raise ValidationError("query is invalid")
        if tags is not None:
            if not isinstance(tags, list) or len(tags) > 8 or len(set(tags)) != len(tags):
                raise ValidationError("tags are invalid")
            if any(not isinstance(tag, str) or not ID_PATTERN.fullmatch(tag) for tag in tags):
                raise ValidationError("tag is invalid")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10:
            raise ValidationError("limit is invalid")
        results = self.catalog.search(query, tags, limit)
        return {"items": results, "count": len(results)}

    def next_delivery(self, receiver_token: str) -> dict[str, object] | None:
        receiver_id = self.storage.authenticate_receiver(receiver_token)
        return self.storage.next_delivery(receiver_id)

    def acknowledge(self, receiver_token: str, body: object) -> dict[str, object]:
        receiver_id = self.storage.authenticate_receiver(receiver_token)
        value = self._object(body, {"delivery_id", "sequence", "outcome", "completed_at", "error"})
        delivery_id = valid_uuid(value.get("delivery_id"))
        sequence = value.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            raise ValidationError("sequence is invalid")
        outcome = value.get("outcome")
        if outcome not in {"displayed", "dismissed", "failed"}:
            raise ValidationError("outcome is invalid")
        completed_at = valid_timestamp(value.get("completed_at"))
        error = value.get("error")
        if outcome == "failed":
            if not isinstance(error, str) or not 1 <= len(error) <= 180:
                raise ValidationError("failed acknowledgments require an error")
        elif error is not None:
            raise ValidationError("only failed acknowledgments may include an error")
        duplicate = self.storage.acknowledge(
            receiver_id, delivery_id, sequence, outcome, completed_at, error
        )
        return {"status": "acknowledged", "duplicate": duplicate}

    @staticmethod
    def _object(body: object, allowed: set[str]) -> dict[str, Any]:
        if not isinstance(body, dict):
            raise ValidationError("request body must be an object")
        extra = set(body) - allowed
        if extra:
            raise ValidationError("request body contains unsupported fields")
        return body
