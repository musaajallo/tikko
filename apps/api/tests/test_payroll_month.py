"""F28 — pure-function tests for monthly aggregation."""

from __future__ import annotations

from datetime import UTC, datetime, time

from tikko.payroll.calc import ShiftSpec, compute_month

NINE_TO_FIVE = ShiftSpec(
    start_time=time(9, 0),
    end_time=time(17, 0),
    late_grace_minutes=0,
    early_out_grace_minutes=0,
    overtime_threshold_minutes=30,
    work_days="1111100",
)


def test_empty_month_marks_every_workday_absent() -> None:
    days, totals = compute_month(NINE_TO_FIVE, [], year=2026, month=5)
    # May 2026 has 31 days; workday count under Mon-Fri = 21.
    assert len(days) == 31
    assert sum(1 for d in days if d.is_workday) == 21
    assert totals.days_worked == 0
    assert totals.days_absent == 21
    assert totals.worked_minutes == 0


def test_month_sums_per_day_metrics() -> None:
    # Two days of punches in May 2026:
    # Thu 2026-05-14 → on time, full day → 0 late/early/OT, 480 min worked.
    # Fri 2026-05-15 → 30 min late, full out → 30 late, 450 worked.
    punches = [
        datetime(2026, 5, 14, 9, 0, tzinfo=UTC),
        datetime(2026, 5, 14, 17, 0, tzinfo=UTC),
        datetime(2026, 5, 15, 9, 30, tzinfo=UTC),
        datetime(2026, 5, 15, 17, 0, tzinfo=UTC),
    ]
    _days, totals = compute_month(NINE_TO_FIVE, punches, year=2026, month=5)
    assert totals.days_worked == 2
    # 21 workdays in May 2026, 2 worked → 19 absent.
    assert totals.days_absent == 19
    assert totals.worked_minutes == 480 + 450
    assert totals.late_minutes == 30
    assert totals.early_out_minutes == 0
    assert totals.overtime_minutes == 0


def test_month_overtime_is_summed_across_days() -> None:
    # Two days, each 60 min of OT past the 30-min threshold.
    punches = [
        datetime(2026, 5, 14, 9, 0, tzinfo=UTC),
        datetime(2026, 5, 14, 18, 30, tzinfo=UTC),
        datetime(2026, 5, 15, 9, 0, tzinfo=UTC),
        datetime(2026, 5, 15, 18, 30, tzinfo=UTC),
    ]
    _days, totals = compute_month(NINE_TO_FIVE, punches, year=2026, month=5)
    assert totals.overtime_minutes == 60 + 60


def test_month_non_workday_punches_do_not_count_as_worked_day() -> None:
    # Punches only on Sat 2026-05-16 (non-workday).
    punches = [
        datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
        datetime(2026, 5, 16, 14, 0, tzinfo=UTC),
    ]
    _days, totals = compute_month(NINE_TO_FIVE, punches, year=2026, month=5)
    # "Worked" here means workday-with-punches; weekend work isn't counted in days_worked.
    assert totals.days_worked == 0
    # 21 workdays in May, none satisfied → 21 absent.
    assert totals.days_absent == 21
    # Worked minutes still tallied — caller decides whether weekend hours count.
    assert totals.worked_minutes == 4 * 60


def test_month_day_list_is_in_chronological_order() -> None:
    days, _ = compute_month(NINE_TO_FIVE, [], year=2026, month=5)
    assert [d.date.day for d in days] == list(range(1, 32))
