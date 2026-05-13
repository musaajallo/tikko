"""WebSocket endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from tikko.auth.tokens import TokenError, decode_token
from tikko.realtime import get_broadcaster

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/attendance")
async def attendance_feed(
    websocket: WebSocket,
    token: str | None = Query(None),
) -> None:
    """Subscribe to new attendance events. Auth via `?token=<access_token>`
    because browsers can't attach Authorization headers to a WS upgrade."""
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="missing token")
        return
    try:
        decode_token(token, expected_type="access")
    except TokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid token")
        return

    await websocket.accept()
    broadcaster = get_broadcaster()
    await broadcaster.subscribe(websocket)
    try:
        # We don't expect client messages; just keep the socket open until
        # the client disconnects.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await broadcaster.unsubscribe(websocket)
