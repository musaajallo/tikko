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

import calendar
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
    # F35 holiday calendar. A date in this set turns off late/early/absent
    # accounting (the employee isn't expected to be present on that day) but
    # overtime is still computed — operators want to see "she worked the
    # holiday, so she's owed OT on it".
    holidays: frozenset[date] = frozenset()


@dataclass(frozen=True)
class DayMetrics:
    """One day's payroll metrics for one employee."""

    date: date
    is_workday: bool
    is_holiday: bool
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
    is_holiday = on_date in spec.holidays
    # A holiday short-circuits the "absent on a workday" rule — the employee
    # is off the hook for the day even if it falls on Mon-Fri.
    counts_as_workday = is_workday and not is_holiday

    # Filter to punches that fall on `on_date` (UTC), then sort.
    same_day = sorted(p for p in punches if p.date() == on_date)

    if not same_day:
        return DayMetrics(
            date=on_date,
            is_workday=is_workday,
            is_holiday=is_holiday,
            is_absent=counts_as_workday,
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
    late_minutes = max(0, late_overage) if counts_as_workday else 0

    early_overage = (
        _minutes_between(last_out, scheduled_end) - spec.early_out_grace_minutes
    )
    early_out_minutes = max(0, early_overage) if counts_as_workday else 0

    ot_overage = (
        _minutes_between(scheduled_end, last_out) - spec.overtime_threshold_minutes
    )
    overtime_minutes = max(0, ot_overage)

    return DayMetrics(
        date=on_date,
        is_workday=is_workday,
        is_holiday=is_holiday,
        is_absent=False,
        first_in=first_in,
        last_out=last_out,
        worked_minutes=worked,
        late_minutes=late_minutes,
        early_out_minutes=early_out_minutes,
        overtime_minutes=overtime_minutes,
    )


@dataclass(frozen=True)
class MonthMetrics:
    """Sums + counts across one calendar month for a single employee.

    `days_worked` and `days_absent` only consider workdays. Weekend punches
    add to `worked_minutes` but don't bump `days_worked`; that's a deliberate
    choice so the report tells the operator "the employee filled their
    scheduled days N times" rather than overloading the same counter with
    voluntary weekend work.

    `days_holiday` counts holidays that fell on what would otherwise have
    been workdays — the days the employee got off thanks to the calendar.
    """

    year: int
    month: int
    days_worked: int
    days_absent: int
    days_holiday: int
    worked_minutes: int
    late_minutes: int
    early_out_minutes: int
    overtime_minutes: int


def compute_month(
    spec: ShiftSpec,
    punches: Iterable[datetime],
    year: int,
    month: int,
) -> tuple[list[DayMetrics], MonthMetrics]:
    """Run `compute_day` across every calendar day in the month, then aggregate."""
    materialized = list(punches)
    _, last_day = calendar.monthrange(year, month)

    days: list[DayMetrics] = []
    for day in range(1, last_day + 1):
        days.append(compute_day(spec, materialized, date(year, month, day)))

    totals = MonthMetrics(
        year=year,
        month=month,
        days_worked=sum(
            1 for d in days if d.is_workday and not d.is_holiday and not d.is_absent
        ),
        days_absent=sum(1 for d in days if d.is_workday and d.is_absent),
        days_holiday=sum(1 for d in days if d.is_workday and d.is_holiday),
        worked_minutes=sum(d.worked_minutes for d in days),
        late_minutes=sum(d.late_minutes for d in days),
        early_out_minutes=sum(d.early_out_minutes for d in days),
        overtime_minutes=sum(d.overtime_minutes for d in days),
    )
    return days, totals
