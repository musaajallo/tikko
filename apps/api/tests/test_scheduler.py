"""Scheduler: pure due-check logic + lifespan loop sanity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from tikko.scheduler import devices_due_for_poll


def _device(
    id: str,
    *,
    enabled: bool = True,
    last: datetime | None = None,
    interval: int | None = None,
):
    return SimpleNamespace(
        id=id,
        enabled=enabled,
        poll_interval_sec=interval,
        last_polled_at=last,
    )


def test_device_with_no_last_poll_is_always_due() -> None:
    now = datetime(2026, 5, 13, 9, 0, tzinfo=UTC)
    devs = [_device("a")]
    due = devices_due_for_poll(devs, now=now, default_interval=60)
    assert [d.id for d in due] == ["a"]


def test_disabled_devices_are_skipped() -> None:
    now = datetime(2026, 5, 13, 9, 0, tzinfo=UTC)
    devs = [_device("a", enabled=False)]
    assert devices_due_for_poll(devs, now=now, default_interval=60) == []


def test_recently_polled_device_is_not_due() -> None:
    now = datetime(2026, 5, 13, 9, 0, tzinfo=UTC)
    devs = [_device("a", last=now - timedelta(seconds=30))]
    assert devices_due_for_poll(devs, now=now, default_interval=60) == []


def test_overdue_device_is_due() -> None:
    now = datetime(2026, 5, 13, 9, 0, tzinfo=UTC)
    devs = [_device("a", last=now - timedelta(seconds=120))]
    due = devices_due_for_poll(devs, now=now, default_interval=60)
    assert [d.id for d in due] == ["a"]


def test_per_device_interval_overrides_default() -> None:
    now = datetime(2026, 5, 13, 9, 0, tzinfo=UTC)
    # Polled 90s ago; default 60s says due, but device says 300s → not due.
    devs = [_device("a", last=now - timedelta(seconds=90), interval=300)]
    assert devices_due_for_poll(devs, now=now, default_interval=60) == []
