# SPDX-License-Identifier: GPL-3.0-or-later

"""Small, stateless MCP adapter for the private bridge HTTP server.

The adapter deliberately reuses :class:`BridgeCore` rather than proxying back
through the public HTTP endpoints.  Authentication is still enforced by the
HTTP request handler before a JSON-RPC message reaches this module.
"""

from __future__ import annotations

import json
from typing import Any

from .core import BridgeCore, ValidationError


LATEST_PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = {
    "2024-11-05",
    "2025-03-26",
    LATEST_PROTOCOL_VERSION,
}

SERVER_INFO = {"name": "sols-peanut-gallery", "version": "0.1.0"}
SERVER_INSTRUCTIONS = (
    "Use find_display_items to search the operator-owned local catalog. "
    "Use queue_display to queue one reaction. A successful queue operation "
    "means queued, not necessarily displayed."
)

TOOLS: list[dict[str, Any]] = [
    {
        "name": "find_display_items",
        "title": "Find display items",
        "description": (
            "Find items in the operator-owned local catalog. Returns metadata "
            "only and never downloads public internet media."
        ),
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
            "idempotentHint": True,
        },
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "query": {"type": "string", "minLength": 1, "maxLength": 120},
                "tags": {
                    "type": "array",
                    "maxItems": 8,
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                        "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
                    },
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                },
            },
            "anyOf": [{"required": ["query"]}, {"required": ["tags"]}],
        },
        "outputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["items", "count"],
            "properties": {
                "items": {
                    "type": "array",
                    "maxItems": 10,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "title", "tags", "caption_seeds"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
                                "maxLength": 80,
                            },
                            "title": {"type": "string", "minLength": 1, "maxLength": 120},
                            "tags": {
                                "type": "array",
                                "minItems": 1,
                                "maxItems": 32,
                                "uniqueItems": True,
                                "items": {
                                    "type": "string",
                                    "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
                                    "maxLength": 40,
                                },
                            },
                            "caption_seeds": {
                                "type": "array",
                                "maxItems": 20,
                                "uniqueItems": True,
                                "items": {
                                    "type": "string",
                                    "minLength": 1,
                                    "maxLength": 180,
                                },
                            },
                        },
                    },
                },
                "count": {"type": "integer", "minimum": 0, "maximum": 10},
            },
        },
        "_meta": {
            "openai/toolInvocation/invoking": "Checking the reaction library…",
            "openai/toolInvocation/invoked": "Reaction library checked",
        },
    },
    {
        "name": "queue_display",
        "title": "Queue display reaction",
        "description": (
            "Queue one bounded text, emoji, or operator-catalog reaction. "
            "Success means queued, not visibly displayed."
        ),
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": False,
            "idempotentHint": True,
        },
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["request_id"],
            "properties": {
                "request_id": {"type": "string", "format": "uuid"},
                "emoji": {"type": "string", "minLength": 1, "maxLength": 16},
                "reaction_id": {
                    "type": "string",
                    "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
                    "maxLength": 80,
                },
                "caption": {"type": "string", "maxLength": 180},
                "display_seconds": {
                    "type": "integer",
                    "minimum": 3,
                    "maximum": 30,
                    "default": 8,
                },
            },
            "oneOf": [
                {"required": ["emoji"], "not": {"required": ["reaction_id"]}},
                {"required": ["reaction_id"], "not": {"required": ["emoji"]}},
                {
                    "required": ["caption"],
                    "properties": {
                        "caption": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 180,
                        }
                    },
                    "not": {
                        "anyOf": [
                            {"required": ["emoji"]},
                            {"required": ["reaction_id"]},
                        ]
                    },
                },
            ],
        },
        "outputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["status", "duplicate", "delivery_id", "sequence"],
            "properties": {
                "status": {"type": "string", "const": "queued"},
                "duplicate": {"type": "boolean"},
                "delivery_id": {"type": "string", "format": "uuid"},
                "sequence": {"type": "integer", "minimum": 1},
            },
        },
        "_meta": {
            "openai/toolInvocation/invoking": "Preparing a reaction…",
            "openai/toolInvocation/invoked": "Reaction queued",
        },
    },
]


class MCPProtocolError(ValueError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _result(request_id: object, result: object) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: object, code: int, message: str) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _tool_result(payload: object, *, is_error: bool = False) -> dict[str, object]:
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    result: dict[str, object] = {
        "content": [{"type": "text", "text": text}],
    }
    if isinstance(payload, dict) and not is_error:
        result["structuredContent"] = payload
    if is_error:
        result["isError"] = True
    return result


def handle_message(core: BridgeCore, message: object) -> dict[str, object] | None:
    """Handle one MCP JSON-RPC message.

    The bridge is intentionally stateless at the MCP transport layer.  Durable
    application state remains in SQLite, and request UUIDs make queue retries
    idempotent.
    """

    if not isinstance(message, dict):
        return _error(None, -32600, "Invalid Request")
    request_id = message.get("id")
    if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        return _error(request_id, -32600, "Invalid Request")
    method = message["method"]
    params = message.get("params", {})
    if not isinstance(params, dict):
        return _error(request_id, -32602, "Invalid params")

    # Notifications have no response body.
    if request_id is None and method.startswith("notifications/"):
        return None

    try:
        if method == "initialize":
            requested = params.get("protocolVersion")
            protocol_version = (
                requested if requested in SUPPORTED_PROTOCOL_VERSIONS else LATEST_PROTOCOL_VERSION
            )
            return _result(
                request_id,
                {
                    "protocolVersion": protocol_version,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": SERVER_INFO,
                    "instructions": SERVER_INSTRUCTIONS,
                },
            )
        if method == "ping":
            return _result(request_id, {})
        if method == "tools/list":
            if set(params) - {"cursor"}:
                raise MCPProtocolError(-32602, "Invalid params")
            return _result(request_id, {"tools": TOOLS})
        if method == "tools/call":
            if set(params) - {"name", "arguments", "_meta"}:
                raise MCPProtocolError(-32602, "Invalid params")
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not isinstance(name, str) or not isinstance(arguments, dict):
                raise MCPProtocolError(-32602, "Invalid params")
            try:
                if name == "find_display_items":
                    return _result(request_id, _tool_result(core.find_display_items(arguments)))
                if name == "queue_display":
                    queued, _duplicate = core.queue_display(arguments)
                    return _result(request_id, _tool_result(queued))
                raise MCPProtocolError(-32602, "Unknown tool")
            except ValidationError as error:
                return _result(
                    request_id,
                    _tool_result({"error": "invalid_request", "message": str(error)}, is_error=True),
                )
        raise MCPProtocolError(-32601, "Method not found")
    except MCPProtocolError as error:
        return _error(request_id, error.code, error.message)
