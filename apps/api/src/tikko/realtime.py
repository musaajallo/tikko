"""In-process WebSocket broadcaster for attendance events.

Single instance per Python process. Fine for one-replica deployments;
for multi-replica we'd swap in Redis pub/sub (deferred — see F31 hardening)."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class AttendanceBroadcaster:
    def __init__(self) -> None:
        self._sockets: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self, ws: WebSocket) -> None:
        async with self._lock:
            self._sockets.add(ws)

    async def unsubscribe(self, ws: WebSocket) -> None:
        async with self._lock:
            self._sockets.discard(ws)

    async def publish(self, payload: dict[str, Any]) -> None:
        """Send `payload` as JSON to every subscriber. Dead sockets are dropped."""
        async with self._lock:
            stale: list[WebSocket] = []
            for ws in self._sockets:
                try:
                    await ws.send_json(payload)
                except Exception:
                    stale.append(ws)
            for ws in stale:
                self._sockets.discard(ws)

    @property
    def subscriber_count(self) -> int:
        return len(self._sockets)


_broadcaster: AttendanceBroadcaster | None = None


def get_broadcaster() -> AttendanceBroadcaster:
    global _broadcaster
    if _broadcaster is None:
        _broadcaster = AttendanceBroadcaster()
    return _broadcaster
