# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    pass


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be an object")
    return value


def _integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ConfigError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True)
class BridgeConfig:
    bind_host: str
    bind_port: int
    state_directory: Path
    catalog_index: Path
    media_directory: Path
    maximum_pending: int = 100
    retention_hours: int = 24
    maximum_request_bytes: int = 65_536
    maximum_media_bytes: int = 8_388_608
    maximum_caption_characters: int = 180
    pairing_ttl_seconds: int = 300
    credential_name: str = "transport-token"
    status_credential_name: str = "status-token"

    @property
    def database_path(self) -> Path:
        return self.state_directory / "bridge.sqlite3"

    @classmethod
    def from_file(cls, path: Path) -> "BridgeConfig":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ConfigError(f"cannot read configuration: {error}") from error
        root = _mapping(data, "configuration")
        if root.get("schema_version") != 1:
            raise ConfigError("schema_version must be 1")
        listener = _mapping(root.get("listener"), "listener")
        storage = _mapping(root.get("storage"), "storage")
        queue = _mapping(root.get("queue"), "queue")
        limits = _mapping(root.get("limits"), "limits")
        security = _mapping(root.get("security", {}), "security")
        host = listener.get("bind_host")
        if not isinstance(host, str) or not host or len(host) > 253:
            raise ConfigError("listener.bind_host is invalid")
        if listener.get("require_paired_device") is not True:
            raise ConfigError("listener.require_paired_device must be true")
        paths: dict[str, Path] = {}
        for key in ("state_directory", "catalog_index", "media_directory"):
            value = storage.get(key)
            if not isinstance(value, str) or not value:
                raise ConfigError(f"storage.{key} is invalid")
            paths[key] = Path(value).expanduser()
        credential_name = security.get("credential_name", "transport-token")
        if not isinstance(credential_name, str) or not credential_name.replace("-", "").isalnum():
            raise ConfigError("security.credential_name is invalid")
        status_credential_name = security.get("status_credential_name", "status-token")
        if (
            not isinstance(status_credential_name, str)
            or not status_credential_name.replace("-", "").isalnum()
            or status_credential_name == credential_name
        ):
            raise ConfigError("security.status_credential_name is invalid")
        return cls(
            bind_host=host,
            bind_port=_integer(listener.get("bind_port"), "listener.bind_port", 1, 65_535),
            state_directory=paths["state_directory"],
            catalog_index=paths["catalog_index"],
            media_directory=paths["media_directory"],
            maximum_pending=_integer(queue.get("maximum_pending"), "queue.maximum_pending", 1, 10_000),
            retention_hours=_integer(queue.get("retention_hours"), "queue.retention_hours", 1, 8_760),
            maximum_request_bytes=_integer(limits.get("maximum_request_bytes"), "limits.maximum_request_bytes", 1_024, 1_048_576),
            maximum_media_bytes=_integer(limits.get("maximum_media_bytes"), "limits.maximum_media_bytes", 1, 8_388_608),
            maximum_caption_characters=_integer(limits.get("maximum_caption_characters"), "limits.maximum_caption_characters", 1, 180),
            pairing_ttl_seconds=_integer(security.get("pairing_ttl_seconds", 300), "security.pairing_ttl_seconds", 30, 900),
            credential_name=credential_name,
            status_credential_name=status_credential_name,
        )

    def read_admin_token(self) -> str:
        return self._read_credential(self.credential_name)

    def read_status_token(self) -> str:
        return self._read_credential(self.status_credential_name)

    @staticmethod
    def _read_credential(credential_name: str) -> str:
        credentials_directory = os.environ.get("CREDENTIALS_DIRECTORY")
        if not credentials_directory:
            raise ConfigError("CREDENTIALS_DIRECTORY is not set")
        credential_path = Path(credentials_directory) / credential_name
        try:
            token = credential_path.read_text(encoding="utf-8").strip()
        except OSError as error:
            raise ConfigError(f"cannot read operating-system credential: {error}") from error
        if len(token) < 32 or len(token) > 512 or any(character.isspace() for character in token):
            raise ConfigError("operating-system credential has an invalid format")
        return token
