# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import logging
import re
from typing import Any

from .catalog import Catalog
from .config import BridgeConfig
from .core import BridgeCore, ValidationError
from .media import MediaError, verify_media_bytes
from .storage import AuthenticationError, ConflictError, StorageError


LOGGER = logging.getLogger("peanut_gallery_bridge.http")
ACK_PATH = re.compile(r"^/v1/deliveries/([0-9a-f-]{36})/ack$")
REVOKE_PATH = re.compile(r"^/v1/admin/receivers/([0-9a-f-]{36})/revoke$")
MEDIA_PATH = re.compile(r"^/v1/media/([0-9a-f-]{36})$")


class BridgeHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], core: BridgeCore, catalog: Catalog, config: BridgeConfig, admin_token: str):
        super().__init__(address, BridgeRequestHandler)
        self.core = core
        self.catalog = catalog
        self.config = config
        self.admin_token = admin_token


class BridgeRequestHandler(BaseHTTPRequestHandler):
    server: BridgeHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format_string: str, *args: object) -> None:
        LOGGER.info("request from %s: %s", self.client_address[0], format_string % args)

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        try:
            if self.path == "/healthz":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return
            if self.path == "/v1/deliveries/next":
                token = self._bearer_token()
                delivery = self.server.core.next_delivery(token)
                if delivery is None:
                    self._send_empty(HTTPStatus.NO_CONTENT)
                else:
                    self._send_json(HTTPStatus.OK, delivery)
                return
            media_match = MEDIA_PATH.fullmatch(self.path)
            if media_match:
                self._serve_media(media_match.group(1))
                return
            self._send_error(HTTPStatus.NOT_FOUND, "not_found", "endpoint does not exist")
        except Exception as error:  # centralized protocol mapping
            self._handle_exception(error)

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        try:
            if self.path == "/v1/pair":
                body = self._read_json()
                self._send_json(HTTPStatus.CREATED, self.server.core.pair(body))
                return
            if self.path == "/v1/tools/queue-display":
                self._require_admin()
                result, duplicate = self.server.core.queue_display(self._read_json())
                self._send_json(HTTPStatus.OK if duplicate else HTTPStatus.ACCEPTED, result)
                return
            if self.path == "/v1/tools/find-display-items":
                self._require_admin()
                self._send_json(HTTPStatus.OK, self.server.core.find_display_items(self._read_json()))
                return
            if self.path == "/v1/admin/pairing-codes":
                self._require_admin()
                body = self._read_json()
                if body != {}:
                    raise ValidationError("pairing-code request must be an empty object")
                self._send_json(HTTPStatus.CREATED, self.server.core.create_pairing_code())
                return
            revoke_match = REVOKE_PATH.fullmatch(self.path)
            if revoke_match:
                self._require_admin()
                if self._read_json() != {}:
                    raise ValidationError("revoke request must be an empty object")
                revoked = self.server.core.storage.revoke_receiver(revoke_match.group(1))
                if not revoked:
                    self._send_error(HTTPStatus.NOT_FOUND, "not_found", "active receiver does not exist")
                else:
                    self._send_json(HTTPStatus.OK, {"status": "revoked"})
                return
            ack_match = ACK_PATH.fullmatch(self.path)
            if ack_match:
                token = self._bearer_token()
                body = self._read_json()
                if not isinstance(body, dict) or body.get("delivery_id") != ack_match.group(1):
                    raise ValidationError("path and acknowledgment delivery_id must match")
                self._send_json(HTTPStatus.OK, self.server.core.acknowledge(token, body))
                return
            self._send_error(HTTPStatus.NOT_FOUND, "not_found", "endpoint does not exist")
        except Exception as error:  # centralized protocol mapping
            self._handle_exception(error)

    def _read_json(self) -> Any:
        if self.headers.get("Transfer-Encoding"):
            raise ValidationError("transfer-encoded request bodies are not supported")
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            raise ValidationError("Content-Type must be application/json")
        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length or "")
        except ValueError as error:
            raise ValidationError("a valid Content-Length is required") from error
        if not 0 < length <= self.server.config.maximum_request_bytes:
            raise ValidationError("request body size is outside the permitted range")
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise ValidationError("request body was truncated")
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValidationError("request body is not valid UTF-8 JSON") from error

    def _bearer_token(self) -> str:
        authorization = self.headers.get("Authorization", "")
        if not authorization.startswith("Bearer ") or len(authorization) > 600:
            raise AuthenticationError("a bearer credential is required")
        token = authorization[7:]
        if not token or any(character.isspace() for character in token):
            raise AuthenticationError("bearer credential is malformed")
        return token

    def _require_admin(self) -> None:
        supplied = self._bearer_token()
        if not hmac.compare_digest(supplied, self.server.admin_token):
            raise AuthenticationError("administrator credential is invalid")

    def _serve_media(self, media_id: str) -> None:
        self.server.core.storage.authenticate_receiver(self._bearer_token())
        entry = self.server.catalog.by_media_id.get(media_id)
        if entry is None:
            self._send_error(HTTPStatus.NOT_FOUND, "not_found", "media does not exist")
            return
        try:
            with entry.media_path.open("rb") as source:
                data = source.read(self.server.config.maximum_media_bytes + 1)
            verify_media_bytes(data, entry.media, self.server.config.maximum_media_bytes)
        except (OSError, MediaError) as error:
            LOGGER.warning("refusing changed or unreadable catalog media %s: %s", media_id, error)
            self._send_error(HTTPStatus.CONFLICT, "media_changed", "catalog media no longer matches validated metadata")
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", entry.media.mime_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _handle_exception(self, error: Exception) -> None:
        if isinstance(error, AuthenticationError):
            self._send_error(HTTPStatus.UNAUTHORIZED, "unauthorized", str(error), authenticate=True)
        elif isinstance(error, ValidationError):
            self._send_error(HTTPStatus.BAD_REQUEST, "invalid_request", str(error))
        elif isinstance(error, ConflictError):
            self._send_error(HTTPStatus.CONFLICT, "conflict", str(error))
        elif isinstance(error, StorageError):
            LOGGER.error("storage operation failed: %s", error)
            self._send_error(HTTPStatus.SERVICE_UNAVAILABLE, "unavailable", "bridge storage is unavailable")
        else:
            LOGGER.exception("unexpected request failure")
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "request could not be completed")

    def _send_json(self, status: HTTPStatus, payload: object) -> None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _send_empty(self, status: HTTPStatus) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _send_error(self, status: HTTPStatus, code: str, message: str, authenticate: bool = False) -> None:
        data = json.dumps({"error": code, "message": message}, separators=(",", ":")).encode("utf-8")
        self.close_connection = True
        self.send_response(status)
        if authenticate:
            self.send_header("WWW-Authenticate", 'Bearer realm="sol-peanut-gallery"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)
