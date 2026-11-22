# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import uuid

from .media import MediaInfo, inspect_media, safe_media_path


ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FILE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
MEDIA_NAMESPACE = uuid.UUID("9e0dcc4c-3b7a-4a6a-9d4d-10127e6b552a")


class CatalogError(ValueError):
    pass


@dataclass(frozen=True)
class CatalogEntry:
    identifier: str
    title: str
    file_name: str
    tags: tuple[str, ...]
    caption_seeds: tuple[str, ...]
    media_id: str
    media_path: Path
    media: MediaInfo


class Catalog:
    def __init__(self, entries: tuple[CatalogEntry, ...] = ()) -> None:
        self.entries = entries
        self.by_identifier = {entry.identifier: entry for entry in entries}
        self.by_media_id = {entry.media_id: entry for entry in entries}

    @classmethod
    def load(cls, index_path: Path, media_directory: Path, maximum_media_bytes: int) -> "Catalog":
        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CatalogError(f"cannot read catalog index: {error}") from error
        if not isinstance(payload, dict) or set(payload) != {"schema_version", "entries"}:
            raise CatalogError("catalog root must contain only schema_version and entries")
        if payload["schema_version"] != 1 or not isinstance(payload["entries"], list):
            raise CatalogError("unsupported catalog schema")
        if len(payload["entries"]) > 5_000:
            raise CatalogError("catalog has too many entries")
        entries: list[CatalogEntry] = []
        identifiers: set[str] = set()
        file_names: set[str] = set()
        for raw in payload["entries"]:
            entry = cls._load_entry(raw, media_directory, maximum_media_bytes)
            if entry.identifier in identifiers or entry.file_name in file_names:
                raise CatalogError("catalog identifiers and file names must be unique")
            identifiers.add(entry.identifier)
            file_names.add(entry.file_name)
            entries.append(entry)
        return cls(tuple(entries))

    @staticmethod
    def _load_entry(raw: object, media_directory: Path, maximum_media_bytes: int) -> CatalogEntry:
        required = {"id", "title", "file_name", "tags", "caption_seeds"}
        if not isinstance(raw, dict) or set(raw) != required:
            raise CatalogError("each catalog entry must contain exactly the documented fields")
        identifier = raw["id"]
        title = raw["title"]
        file_name = raw["file_name"]
        tags = raw["tags"]
        captions = raw["caption_seeds"]
        if not isinstance(identifier, str) or len(identifier) > 80 or not ID_PATTERN.fullmatch(identifier):
            raise CatalogError("catalog identifier is invalid")
        if not isinstance(title, str) or not 1 <= len(title) <= 120:
            raise CatalogError("catalog title is invalid")
        if not isinstance(file_name, str) or not FILE_PATTERN.fullmatch(file_name):
            raise CatalogError("catalog file name is invalid")
        if not isinstance(tags, list) or not 1 <= len(tags) <= 32 or len(set(tags)) != len(tags):
            raise CatalogError("catalog tags are invalid")
        if any(not isinstance(tag, str) or len(tag) > 40 or not ID_PATTERN.fullmatch(tag) for tag in tags):
            raise CatalogError("catalog tag is invalid")
        if not isinstance(captions, list) or len(captions) > 20 or len(set(captions)) != len(captions):
            raise CatalogError("catalog caption seeds are invalid")
        if any(not isinstance(caption, str) or not 1 <= len(caption) <= 180 for caption in captions):
            raise CatalogError("catalog caption seed is invalid")
        try:
            path = safe_media_path(media_directory, file_name)
            media = inspect_media(path, maximum_media_bytes)
        except ValueError as error:
            raise CatalogError(str(error)) from error
        return CatalogEntry(
            identifier=identifier,
            title=title,
            file_name=file_name,
            tags=tuple(tags),
            caption_seeds=tuple(captions),
            media_id=str(uuid.uuid5(MEDIA_NAMESPACE, identifier)),
            media_path=path,
            media=media,
        )

    def search(self, query: str | None, tags: list[str] | None, limit: int) -> list[dict[str, object]]:
        words = tuple((query or "").casefold().split())
        required_tags = set(tags or [])
        results: list[dict[str, object]] = []
        for entry in self.entries:
            haystack = " ".join((entry.title, entry.identifier, *entry.tags, *entry.caption_seeds)).casefold()
            if words and not all(word in haystack for word in words):
                continue
            if required_tags and not required_tags.issubset(entry.tags):
                continue
            results.append({
                "id": entry.identifier,
                "title": entry.title,
                "tags": list(entry.tags),
                "caption_seeds": list(entry.caption_seeds),
            })
            if len(results) == limit:
                break
        return results
