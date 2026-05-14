"""In-process fake of the `pyzk` `ZK` class.

`ZKClient` (in `tikko.zk.client`) imports `ZK` from the `zk` package and
instantiates it as `ZK(host, port=, timeout=)`. To exercise `ZKClient` end-to-end
in tests — and to run the app without real hardware in dev — we expose:

- `FakeDevice` — mutable in-memory state for one terminal
- `FakeZK` — drop-in for `zk.ZK`; its `.connect()` returns a `FakeConnection`
- `use_fake_devices(*devices)` — context manager that monkeypatches the `ZK`
  symbol bound inside `tikko.zk.client` for the duration of the block

Once F19 stabilises we can layer a TCP-listening fake on top for full protocol
coverage, but the in-process version is enough to unblock employee enrollment
and beyond.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime

import tikko.zk.client as _zk_client_module


@dataclass(slots=True)
class _FakePunchRecord:
    """Shape that pyzk's Attendance objects expose to consumers of `get_attendance()`."""

    user_id: str
    timestamp: datetime
    status: int
    punch: int


@dataclass(slots=True)
class FakeSyncedUser:
    """What `FakeConnection.set_user(...)` records on the device."""

    uid: int
    user_id: str
    name: str


@dataclass(slots=True)
class _FakeFinger:
    """Mirrors the pyzk `Finger` object shape that consumers read: a `.template` bytes attr."""

    finger_id: int
    template: bytes


@dataclass
class FakeDevice:
    """Mutable in-memory state for a single fake terminal, keyed by host.

    `host` is what `ZKClient(host=...)` will be called with — that's how the
    registry routes a `FakeZK(host)` lookup back to this device.
    """

    host: str
    serial_number: str = "FAKE-0000"
    firmware_version: str = "6.60"
    platform: str = "JZ4775_TFT"
    device_name: str = "iClock Fake"
    punches: list[_FakePunchRecord] = field(default_factory=list)
    synced_users: dict[str, FakeSyncedUser] = field(default_factory=dict)
    templates: dict[str, dict[int, bytes]] = field(default_factory=dict)

    def add_punch(
        self, user_id: str, timestamp: datetime, status: int = 0, punch: int = 0
    ) -> None:
        self.punches.append(
            _FakePunchRecord(
                user_id=user_id, timestamp=timestamp, status=status, punch=punch
            )
        )

    def set_user_template(self, user_id: str, finger_id: int, data: bytes) -> None:
        """Seed a fingerprint template on the fake device (test convenience)."""
        self.templates.setdefault(user_id, {})[finger_id] = data


class FakeConnection:
    """What `FakeZK.connect()` returns. Mirrors the subset of pyzk's `Connection`
    interface that `ZKClient` uses."""

    def __init__(self, device: FakeDevice) -> None:
        self._device = device

    def get_serialnumber(self) -> str:
        return self._device.serial_number

    def get_firmware_version(self) -> str:
        return self._device.firmware_version

    def get_platform(self) -> str:
        return self._device.platform

    def get_device_name(self) -> str:
        return self._device.device_name

    def get_attendance(self) -> list[_FakePunchRecord]:
        return list(self._device.punches)

    def set_user(
        self,
        uid: int,
        name: str = "",
        privilege: int = 0,
        password: str = "",
        group_id: str = "",
        user_id: str = "",
        card: int = 0,
    ) -> None:
        key = user_id or str(uid)
        self._device.synced_users[key] = FakeSyncedUser(
            uid=uid, user_id=key, name=name
        )

    def get_user_template(
        self, uid: int, temp_id: int, user_id: str = ""
    ) -> _FakeFinger | None:
        key = user_id or str(uid)
        data = self._device.templates.get(key, {}).get(temp_id)
        if data is None:
            return None
        return _FakeFinger(finger_id=temp_id, template=data)

    def disconnect(self) -> None:
        return None


class FakeZK:
    """Drop-in for `zk.ZK`. Looks the host up in the module registry on `.connect()`."""

    def __init__(self, host: str, port: int = 4370, timeout: int = 10) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def connect(self) -> FakeConnection:
        device = _REGISTRY.get(self.host)
        if device is None:
            raise ConnectionError(
                f"no fake device registered for host {self.host!r}"
            )
        return FakeConnection(device)


_REGISTRY: dict[str, FakeDevice] = {}


@contextmanager
def use_fake_devices(*devices: FakeDevice) -> Iterator[None]:
    """Swap the `ZK` symbol bound inside `tikko.zk.client` for `FakeZK` while
    the context is active, and seed the registry with the given devices.

    On exit, the original `ZK` is restored and the registry is cleared, so
    fakes never leak across tests.
    """
    original_zk = _zk_client_module.ZK
    previous_registry = _REGISTRY.copy()
    _REGISTRY.clear()
    for device in devices:
        _REGISTRY[device.host] = device
    _zk_client_module.ZK = FakeZK  # type: ignore[assignment]
    try:
        yield
    finally:
        _zk_client_module.ZK = original_zk  # type: ignore[assignment]
        _REGISTRY.clear()
        _REGISTRY.update(previous_registry)


__all__ = [
    "FakeConnection",
    "FakeDevice",
    "FakeSyncedUser",
    "FakeZK",
    "use_fake_devices",
]
