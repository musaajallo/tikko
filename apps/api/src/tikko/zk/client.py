"""Thin wrapper around `pyzk` for ZKTeco binary protocol (TCP/UDP :4370).

pyzk is synchronous; callers should run instance methods via
`asyncio.to_thread(...)` to avoid blocking the FastAPI event loop.
"""

from __future__ import annotations

from dataclasses import dataclass

from zk import ZK


class ZKConnectionError(Exception):
    """Raised when the device cannot be reached, times out, or rejects the connection."""


@dataclass(slots=True)
class DeviceInfo:
    serial_number: str
    firmware_version: str
    platform: str
    device_name: str


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


def _as_str(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("ascii", errors="replace")
    return str(value) if value is not None else ""
