# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class BatteryWatchError(RuntimeError):
    pass


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise BatteryWatchError(f"{name} must be an integer from {minimum} through {maximum}")
    return value


@dataclass(frozen=True)
class BatteryWatchConfig:
    status_url: str
    token_file: Path
    state_file: Path
    notification_command: tuple[str, ...]
    low_percent: int = 20
    recover_percent: int = 25
    stale_after_seconds: int = 900
    repeat_seconds: int = 21_600
    poll_seconds: int = 300

    @classmethod
    def from_file(cls, path: Path) -> "BatteryWatchConfig":
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise BatteryWatchError(f"cannot read battery-watch configuration: {error}") from error
        if not isinstance(value, dict) or value.get("schema_version") != 1:
            raise BatteryWatchError("battery-watch configuration schema_version must be 1")
        allowed = {
            "schema_version", "status_url", "token_file", "state_file",
            "notification_command", "low_percent", "recover_percent",
            "stale_after_seconds", "repeat_seconds", "poll_seconds",
        }
        if set(value) - allowed:
            raise BatteryWatchError("battery-watch configuration contains unsupported fields")
        status_url = value.get("status_url")
        if not isinstance(status_url, str):
            raise BatteryWatchError("status_url must be a string")
        parsed = urlsplit(status_url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path != "/v1/status/receivers"
        ):
            raise BatteryWatchError(
                "status_url must be an http(s) URL ending at /v1/status/receivers"
            )
        token_file = value.get("token_file")
        state_file = value.get("state_file")
        command = value.get("notification_command")
        if not isinstance(token_file, str) or not token_file:
            raise BatteryWatchError("token_file must be a non-empty path")
        if not isinstance(state_file, str) or not state_file:
            raise BatteryWatchError("state_file must be a non-empty path")
        if (
            not isinstance(command, list)
            or not command
            or any(not isinstance(item, str) or not item for item in command)
        ):
            raise BatteryWatchError("notification_command must be a non-empty string array")
        low = _integer(value.get("low_percent", 20), "low_percent", 1, 99)
        recover = _integer(value.get("recover_percent", 25), "recover_percent", 2, 100)
        if recover <= low:
            raise BatteryWatchError("recover_percent must be greater than low_percent")
        return cls(
            status_url=status_url,
            token_file=Path(token_file).expanduser(),
            state_file=Path(state_file).expanduser(),
            notification_command=tuple(command),
            low_percent=low,
            recover_percent=recover,
            stale_after_seconds=_integer(
                value.get("stale_after_seconds", 900), "stale_after_seconds", 60, 86_400
            ),
            repeat_seconds=_integer(
                value.get("repeat_seconds", 21_600), "repeat_seconds", 300, 604_800
            ),
            poll_seconds=_integer(value.get("poll_seconds", 300), "poll_seconds", 30, 86_400),
        )

    def read_token(self) -> str:
        try:
            details = self.token_file.stat()
            token = self.token_file.read_text(encoding="utf-8").strip()
        except OSError as error:
            raise BatteryWatchError(f"cannot read status observer credential: {error}") from error
        if os.name == "posix" and stat.S_IMODE(details.st_mode) & 0o077:
            raise BatteryWatchError("status observer credential must not be accessible by group or others")
        if len(token) < 32 or len(token) > 512 or any(character.isspace() for character in token):
            raise BatteryWatchError("status observer credential has an invalid format")
        return token


def fetch_status(config: BatteryWatchConfig) -> dict[str, object]:
    request = Request(
        config.status_url,
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + config.read_token(),
            "Cache-Control": "no-store",
            "User-Agent": "sol-peanut-gallery-battery-watch/0.1",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=20) as response:
            content_type = response.headers.get_content_type()
            data = response.read(65_537)
            if response.status != 200 or content_type != "application/json" or len(data) > 65_536:
                raise BatteryWatchError("bridge returned an invalid status response")
    except (HTTPError, URLError, TimeoutError) as error:
        raise BatteryWatchError(f"cannot fetch receiver battery status: {error}") from error
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BatteryWatchError("bridge returned invalid status JSON") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("receivers"), list):
        raise BatteryWatchError("bridge status response has an invalid shape")
    return payload


class BatteryWatch:
    def __init__(self, config: BatteryWatchConfig) -> None:
        self.config = config
        self.state = self._load_state()

    def evaluate(
        self, payload: dict[str, object], now: datetime | None = None
    ) -> list[dict[str, object]]:
        moment = now or datetime.now(timezone.utc)
        receivers = payload.get("receivers")
        if not isinstance(receivers, list):
            raise BatteryWatchError("bridge status response has an invalid shape")
        notifications: list[dict[str, object]] = []
        for item in receivers:
            status = self._validated_status(item, moment)
            if status is None:
                continue
            receiver_id = status["receiver_id"]
            prior = self.state.setdefault(receiver_id, {"low": False, "last_notified": None})
            percent = status["battery_percent"]
            charging = status["charging"]
            if charging or percent >= self.config.recover_percent:
                prior["low"] = False
                prior["last_notified"] = None
                continue
            if percent > self.config.low_percent:
                continue
            last = prior.get("last_notified")
            repeated = isinstance(last, (int, float)) and moment.timestamp() - float(last) >= self.config.repeat_seconds
            if not prior.get("low") or repeated:
                notifications.append(status)
                prior["last_notified"] = moment.timestamp()
            prior["low"] = True
        self._save_state()
        return notifications

    def _validated_status(
        self, value: object, now: datetime
    ) -> dict[str, object] | None:
        if not isinstance(value, dict):
            raise BatteryWatchError("receiver status entry must be an object")
        receiver_id = value.get("receiver_id")
        label = value.get("device_label")
        percent = value.get("battery_percent")
        charging = value.get("charging")
        reported_at = value.get("reported_at")
        if not isinstance(receiver_id, str) or not receiver_id:
            raise BatteryWatchError("receiver status has an invalid identifier")
        if not isinstance(label, str) or not 1 <= len(label) <= 80:
            raise BatteryWatchError("receiver status has an invalid label")
        if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100:
            raise BatteryWatchError("receiver status has an invalid battery percentage")
        if not isinstance(charging, bool) or not isinstance(reported_at, str) or not reported_at.endswith("Z"):
            raise BatteryWatchError("receiver status has invalid charging or time data")
        try:
            reported = datetime.fromisoformat(reported_at[:-1] + "+00:00")
        except ValueError as error:
            raise BatteryWatchError("receiver status has an invalid report time") from error
        age = (now - reported).total_seconds()
        if age < -60 or age > self.config.stale_after_seconds:
            return None
        return {
            "receiver_id": receiver_id,
            "device_label": label,
            "battery_percent": percent,
            "charging": charging,
            "reported_at": reported_at,
        }

    def _load_state(self) -> dict[str, dict[str, object]]:
        try:
            value = json.loads(self.config.state_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as error:
            raise BatteryWatchError(f"cannot read battery-watch state: {error}") from error
        if not isinstance(value, dict):
            raise BatteryWatchError("battery-watch state is invalid")
        return value

    def _save_state(self) -> None:
        path = self.config.state_file
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = path.with_name(path.name + ".tmp")
        data = json.dumps(self.state, sort_keys=True, separators=(",", ":")) + "\n"
        try:
            with temporary.open("w", encoding="utf-8") as output:
                os.chmod(temporary, 0o600)
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        except OSError as error:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise BatteryWatchError(f"cannot write battery-watch state: {error}") from error


def send_notification(config: BatteryWatchConfig, status: dict[str, object]) -> None:
    values = {
        "title": "Peanut Gallery battery is low",
        "body": f"{status['device_label']} is at {status['battery_percent']}% and is not charging.",
        "device_label": str(status["device_label"]),
        "battery_percent": str(status["battery_percent"]),
    }
    try:
        command = [item.format_map(values) for item in config.notification_command]
    except (KeyError, ValueError) as error:
        raise BatteryWatchError(f"notification command template is invalid: {error}") from error
    try:
        result = subprocess.run(command, check=False, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise BatteryWatchError(f"cannot run notification command: {error}") from error
    if result.returncode != 0:
        raise BatteryWatchError(f"notification command exited with status {result.returncode}")


def run_once(config: BatteryWatchConfig, now: datetime | None = None) -> int:
    watch = BatteryWatch(config)
    for status in watch.evaluate(fetch_status(config), now=now):
        send_notification(config, status)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="sol-peanut-gallery-battery-watch")
    result.add_argument("--config", required=True, type=Path, help="path to non-secret battery-watch JSON configuration")
    result.add_argument("--once", action="store_true", help="check once instead of remaining active")
    return result


def main(arguments: list[str] | None = None) -> int:
    options = parser().parse_args(arguments)
    try:
        config = BatteryWatchConfig.from_file(options.config)
        if options.once:
            return run_once(config)
        while True:
            try:
                run_once(config)
            except BatteryWatchError as error:
                print(f"battery watch: {error}", file=sys.stderr)
            time.sleep(config.poll_seconds)
    except BatteryWatchError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
