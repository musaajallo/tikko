"""Thin wrapper around `pyzk` for ZKTeco binary protocol (TCP/UDP :4370).

pyzk is synchronous; callers should run instance methods via
`asyncio.to_thread(...)` to avoid blocking the FastAPI event loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from zk import ZK


class ZKConnectionError(Exception):
    """Raised when the device cannot be reached, times out, or rejects the connection."""


@dataclass(slots=True)
class DeviceInfo:
    serial_number: str
    firmware_version: str
    platform: str
    device_name: str


@dataclass(slots=True)
class RawTemplate:
    """One fingerprint template as pulled off the device."""

    finger_id: int
    data: bytes


@dataclass(slots=True)
class RawPunch:
    """One attendance record as returned by the device.

    `status` and `punch` are device-defined small integers (e.g. status 0/1/2/3/4/5
    encodes check-in/check-out/break-out/break-in/overtime-in/overtime-out;
    `punch` is the verify mode — fingerprint, face, password, etc.).
    """

    user_id: str
    timestamp: datetime
    status: int
    punch: int


class ZKClient:
    """One client per terminal. Instances are cheap; create per request."""

    def __init__(self, host: str, port: int = 4370, timeout: int = 10) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def test_connection(self) -> DeviceInfo:
        """Connect, fetch identity, disconnect. Raises ZKConnectionError on failure."""
        zk = ZK(self.host, port=self.port, timeout=self.timeout)
        try:
            conn = zk.connect()
        except Exception as exc:  # pyzk raises plain Exception subclasses
            raise ZKConnectionError(str(exc)) from exc

        try:
            return DeviceInfo(
                serial_number=_as_str(conn.get_serialnumber()),
                firmware_version=_as_str(conn.get_firmware_version()),
                platform=_as_str(conn.get_platform()),
                device_name=_as_str(conn.get_device_name()),
            )
        except Exception as exc:
            raise ZKConnectionError(str(exc)) from exc
        finally:
            try:
                conn.disconnect()
            except Exception:
                pass

    def get_attendance(self) -> list[RawPunch]:
        """Pull all attendance records currently buffered on the device."""
        zk = ZK(self.host, port=self.port, timeout=self.timeout)
        try:
            conn = zk.connect()
        except Exception as exc:
            raise ZKConnectionError(str(exc)) from exc

        try:
            records = conn.get_attendance() or []
            return [
                RawPunch(
                    user_id=_as_str(r.user_id),
                    timestamp=r.timestamp,
                    status=int(getattr(r, "status", 0) or 0),
                    punch=int(getattr(r, "punch", 0) or 0),
                )
                for r in records
            ]
        except Exception as exc:
            raise ZKConnectionError(str(exc)) from exc
        finally:
            try:
                conn.disconnect()
            except Exception:
                pass

    def get_user_templates(self, user_id: str) -> list[RawTemplate]:
        """Pull every enrolled fingerprint template for one user.

        Iterates `finger_id` 0..9 because pyzk's `get_user_template` is keyed
        by both `uid` and `temp_id` (the finger slot). Missing fingers come
        back as `None`/empty and are skipped silently — only the enrolled
        slots end up in the returned list.
        """
        if not user_id.isdigit():
            raise ValueError(f"user_id must be digits-only; got {user_id!r}")
        uid = int(user_id)

        zk = ZK(self.host, port=self.port, timeout=self.timeout)
        try:
            conn = zk.connect()
        except Exception as exc:
            raise ZKConnectionError(str(exc)) from exc

        try:
            templates: list[RawTemplate] = []
            for finger_id in range(10):
                tpl = conn.get_user_template(
                    uid=uid, temp_id=finger_id, user_id=user_id
                )
                if tpl is None:
                    continue
                data = getattr(tpl, "template", None)
                if data:
                    templates.append(
                        RawTemplate(finger_id=finger_id, data=bytes(data))
                    )
            return templates
        except Exception as exc:
            raise ZKConnectionError(str(exc)) from exc
        finally:
            try:
                conn.disconnect()
            except Exception:
                pass

    def set_user(self, user_id: str, name: str) -> None:
        """Enroll (or update) one user on the device.

        `user_id` must be a digits-only string — the device-side `uid` slot is a
        small int, and `tikko.schemas.employee.EmployeeCreate` already enforces
        this pattern at the API boundary, so the cast is guarded by the schema.
        """
        if not user_id.isdigit():
            raise ValueError(f"user_id must be digits-only; got {user_id!r}")
        uid = int(user_id)

        zk = ZK(self.host, port=self.port, timeout=self.timeout)
        try:
            conn = zk.connect()
        except Exception as exc:
            raise ZKConnectionError(str(exc)) from exc

        try:
            conn.set_user(uid=uid, name=name, user_id=user_id)
        except Exception as exc:
            raise ZKConnectionError(str(exc)) from exc
        finally:
            try:
                conn.disconnect()
            except Exception:
                pass


def _as_str(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("ascii", errors="replace")
    return str(value) if value is not None else ""
