# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
from typing import Iterator
import uuid


class StorageError(RuntimeError):
    pass


class AuthenticationError(StorageError):
    pass


class ConflictError(StorageError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def token_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class Storage:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        database_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(database_path.parent, 0o700)
        except OSError:
            pass
        self._initialize()

    @contextmanager
    def _connection(self, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            if immediate:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS pairing_codes (
                    code_digest TEXT PRIMARY KEY,
                    expires_at TEXT NOT NULL,
                    used_at TEXT
                );
                CREATE TABLE IF NOT EXISTS receivers (
                    receiver_id TEXT PRIMARY KEY,
                    token_digest TEXT NOT NULL UNIQUE,
                    device_label TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT
                );
                CREATE TABLE IF NOT EXISTS deliveries (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    delivery_id TEXT NOT NULL UNIQUE,
                    request_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    display_seconds INTEGER NOT NULL,
                    content_json TEXT NOT NULL,
                    claimed_by TEXT REFERENCES receivers(receiver_id),
                    outcome TEXT,
                    completed_at TEXT,
                    error TEXT
                );
                CREATE INDEX IF NOT EXISTS deliveries_pending
                    ON deliveries(outcome, sequence);
                """
            )
        try:
            os.chmod(self.database_path, 0o600)
        except OSError:
            pass

    def create_pairing_code(self, ttl_seconds: int, now: datetime | None = None) -> tuple[str, str]:
        moment = now or utc_now()
        expires = moment.timestamp() + ttl_seconds
        with self._connection(immediate=True) as connection:
            connection.execute("DELETE FROM pairing_codes WHERE expires_at < ? OR used_at IS NOT NULL", (isoformat(moment),))
            for _ in range(20):
                code = f"{secrets.randbelow(1_000_000):06d}"
                try:
                    connection.execute(
                        "INSERT INTO pairing_codes(code_digest, expires_at) VALUES (?, ?)",
                        (token_digest(code), isoformat(datetime.fromtimestamp(expires, timezone.utc))),
                    )
                except sqlite3.IntegrityError:
                    continue
                return code, isoformat(datetime.fromtimestamp(expires, timezone.utc))
        raise StorageError("could not allocate a pairing code")

    def pair(self, code: str, device_label: str, now: datetime | None = None) -> dict[str, str]:
        moment = now or utc_now()
        digest = token_digest(code)
        with self._connection(immediate=True) as connection:
            row = connection.execute(
                "SELECT expires_at, used_at FROM pairing_codes WHERE code_digest = ?", (digest,)
            ).fetchone()
            if row is None or row["used_at"] is not None or row["expires_at"] < isoformat(moment):
                raise AuthenticationError("pairing code is invalid, expired, or already used")
            changed = connection.execute(
                "UPDATE pairing_codes SET used_at = ? WHERE code_digest = ? AND used_at IS NULL",
                (isoformat(moment), digest),
            ).rowcount
            if changed != 1:
                raise AuthenticationError("pairing code is invalid, expired, or already used")
            receiver_id = str(uuid.uuid4())
            receiver_token = "pg_rt_" + secrets.token_urlsafe(32)
            connection.execute(
                "INSERT INTO receivers(receiver_id, token_digest, device_label, created_at) VALUES (?, ?, ?, ?)",
                (receiver_id, token_digest(receiver_token), device_label, isoformat(moment)),
            )
        return {"receiver_id": receiver_id, "receiver_token": receiver_token}

    def authenticate_receiver(self, token: str) -> str:
        digest = token_digest(token)
        with self._connection() as connection:
            row = connection.execute(
                "SELECT receiver_id, token_digest FROM receivers WHERE token_digest = ? AND revoked_at IS NULL",
                (digest,),
            ).fetchone()
        if row is None or not hmac.compare_digest(row["token_digest"], digest):
            raise AuthenticationError("receiver credential is invalid or revoked")
        return str(row["receiver_id"])

    def revoke_receiver(self, receiver_id: str, now: datetime | None = None) -> bool:
        with self._connection(immediate=True) as connection:
            changed = connection.execute(
                "UPDATE receivers SET revoked_at = ? WHERE receiver_id = ? AND revoked_at IS NULL",
                (isoformat(now or utc_now()), receiver_id),
            ).rowcount
            if changed == 1:
                connection.execute(
                    "UPDATE deliveries SET claimed_by = NULL WHERE claimed_by = ? AND outcome IS NULL",
                    (receiver_id,),
                )
        return changed == 1

    def list_receivers(self) -> list[dict[str, object]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT receiver_id, device_label, created_at, revoked_at FROM receivers ORDER BY created_at, receiver_id"
            ).fetchall()
        return [
            {
                "receiver_id": row["receiver_id"],
                "device_label": row["device_label"],
                "created_at": row["created_at"],
                "revoked": row["revoked_at"] is not None,
            }
            for row in rows
        ]

    def queue(self, request_id: str, display_seconds: int, content: dict[str, object], maximum_pending: int, retention_hours: int) -> tuple[dict[str, object], bool]:
        with self._connection(immediate=True) as connection:
            connection.execute(
                "DELETE FROM deliveries WHERE outcome IS NOT NULL AND created_at < ?",
                (isoformat(utc_now() - timedelta(hours=retention_hours)),),
            )
            existing = connection.execute(
                "SELECT * FROM deliveries WHERE request_id = ?", (request_id,)
            ).fetchone()
            if existing is not None:
                return self._delivery(existing), True
            pending = connection.execute(
                "SELECT COUNT(*) FROM deliveries WHERE outcome IS NULL"
            ).fetchone()[0]
            if pending >= maximum_pending:
                raise ConflictError("the pending delivery queue is full")
            delivery_id = str(uuid.uuid4())
            created_at = isoformat(utc_now())
            cursor = connection.execute(
                "INSERT INTO deliveries(delivery_id, request_id, created_at, display_seconds, content_json) VALUES (?, ?, ?, ?, ?)",
                (delivery_id, request_id, created_at, display_seconds, json.dumps(content, ensure_ascii=False, separators=(",", ":"))),
            )
            row = connection.execute(
                "SELECT * FROM deliveries WHERE sequence = ?", (cursor.lastrowid,)
            ).fetchone()
        return self._delivery(row), False

    def next_delivery(self, receiver_id: str) -> dict[str, object] | None:
        with self._connection(immediate=True) as connection:
            row = connection.execute(
                "SELECT * FROM deliveries WHERE outcome IS NULL ORDER BY sequence LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            if row["claimed_by"] not in (None, receiver_id):
                return None
            if row["claimed_by"] is None:
                connection.execute(
                    "UPDATE deliveries SET claimed_by = ? WHERE sequence = ? AND claimed_by IS NULL",
                    (receiver_id, row["sequence"]),
                )
                row = connection.execute(
                    "SELECT * FROM deliveries WHERE sequence = ?", (row["sequence"],)
                ).fetchone()
        return self._delivery(row)

    def acknowledge(self, receiver_id: str, delivery_id: str, sequence: int, outcome: str, completed_at: str, error: str | None) -> bool:
        with self._connection(immediate=True) as connection:
            row = connection.execute(
                "SELECT * FROM deliveries WHERE delivery_id = ?", (delivery_id,)
            ).fetchone()
            if row is None or row["sequence"] != sequence or row["claimed_by"] != receiver_id:
                raise ConflictError("acknowledgment does not match the receiver's active delivery")
            if row["outcome"] is not None:
                same = (
                    row["outcome"] == outcome
                    and row["completed_at"] == completed_at
                    and row["error"] == error
                )
                if not same:
                    raise ConflictError("delivery already has a different acknowledgment")
                return True
            connection.execute(
                "UPDATE deliveries SET outcome = ?, completed_at = ?, error = ? WHERE delivery_id = ? AND outcome IS NULL",
                (outcome, completed_at, error, delivery_id),
            )
        return False

    def pending_count(self) -> int:
        with self._connection() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM deliveries WHERE outcome IS NULL").fetchone()[0])

    @staticmethod
    def _delivery(row: sqlite3.Row) -> dict[str, object]:
        return {
            "delivery_id": row["delivery_id"],
            "sequence": row["sequence"],
            "request_id": row["request_id"],
            "created_at": row["created_at"],
            "display_seconds": row["display_seconds"],
            "content": json.loads(row["content_json"]),
        }
