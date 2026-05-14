"""Pure-function payroll calc.

`compute_day` is the workhorse: given a shift spec, an iterable of punch
timestamps, and the date in question, return per-day metrics (late, early-out,
overtime, total worked).

Assumptions / scope (MVP):
- All times are UTC. Real timezone-per-org handling is a follow-up.
- Naive in/out detection: first punch of the day = "in", last = "out".
  Many ZK terminals don't classify check-in vs check-out reliably; the
  min/max approach is robust against missing punch_type signals.
- Punches outside `on_date` are ignored — overnight shifts that span
  midnight need a future "span" function; for now each day stands alone.
- Late and early-out only apply on workdays (per `work_days`). Overtime
  past `end_time + threshold` is reported regardless of workday — the
  caller can decide whether to count weekend OT.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass(frozen=True)
class ShiftSpec:
    """Pure-data shift definition. The ORM `ShiftRule` adapts to this."""

    start_time: time
    end_time: time
    late_grace_minutes: int = 0
    early_out_grace_minutes: int = 0
    overtime_threshold_minutes: int = 30
    # 7-char binary string indexed Monday..Sunday. "1111100" = Mon-Fri.
    work_days: str = "1111100"


@dataclass(frozen=True)
class DayMetrics:
    """One day's payroll metrics for one employee."""

    date: date
    is_workday: bool
    is_absent: bool
    first_in: datetime | None
    last_out: datetime | None
    worked_minutes: int
    late_minutes: int
    early_out_minutes: int
    overtime_minutes: int


def _is_workday(work_days: str, on_date: date) -> bool:
    """`work_days` is Mon..Sun. Python's `weekday()` returns Mon=0..Sun=6."""
    return work_days[on_date.weekday()] == "1"


def _minutes_between(a: datetime, b: datetime) -> int:
    return int((b - a).total_seconds() // 60)


def compute_day(
    spec: ShiftSpec,
    punches: Iterable[datetime],
    on_date: date,
) -> DayMetrics:
    is_workday = _is_workday(spec.work_days, on_date)

    # Filter to punches that fall on `on_date` (UTC), then sort.
    same_day = sorted(p for p in punches if p.date() == on_date)

    if not same_day:
        return DayMetrics(
            date=on_date,
            is_workday=is_workday,
            is_absent=is_workday,
            first_in=None,
            last_out=None,
            worked_minutes=0,
            late_minutes=0,
            early_out_minutes=0,
            overtime_minutes=0,
        )

    first_in = same_day[0]
    last_out = same_day[-1]
    worked = max(0, _minutes_between(first_in, last_out))

    # Anchor the scheduled start/end to the same tz as the punches so the
    # arithmetic is meaningful. Punches are UTC by the project's contract.
    tz = first_in.tzinfo
    scheduled_start = datetime.combine(on_date, spec.start_time, tzinfo=tz)
    scheduled_end = datetime.combine(on_date, spec.end_time, tzinfo=tz)

    late_overage = _minutes_between(scheduled_start, first_in) - spec.late_grace_minutes
    late_minutes = max(0, late_overage) if is_workday else 0

    early_overage = (
        _minutes_between(last_out, scheduled_end) - spec.early_out_grace_minutes
    )
    early_out_minutes = max(0, early_overage) if is_workday else 0

    ot_overage = (
        _minutes_between(scheduled_end, last_out) - spec.overtime_threshold_minutes
    )
    overtime_minutes = max(0, ot_overage)

    return DayMetrics(
        date=on_date,
        is_workday=is_workday,
        is_absent=False,
        first_in=first_in,
        last_out=last_out,
        worked_minutes=worked,
        late_minutes=late_minutes,
        early_out_minutes=early_out_minutes,
        overtime_minutes=overtime_minutes,
    )
