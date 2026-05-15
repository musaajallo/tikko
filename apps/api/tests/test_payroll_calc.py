"""F27 — payroll calc unit tests.

Tests cover pure functions only — no DB, no FastAPI, no fixtures from conftest.
ShiftSpec/punches/dates are constructed inline.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from tikko.payroll.calc import ShiftSpec, compute_day

# A standard 9-to-5 with default grace: 0 late, 0 early-out, OT after +30min.
NINE_TO_FIVE = ShiftSpec(
    start_time=time(9, 0),
    end_time=time(17, 0),
    late_grace_minutes=0,
    early_out_grace_minutes=0,
    overtime_threshold_minutes=30,
    work_days="1111100",  # Mon-Fri
)

# 2026-05-14 was a Thursday (workday under 1111100).
THURSDAY = date(2026, 5, 14)
# 2026-05-16 was a Saturday (non-workday under 1111100).
SATURDAY = date(2026, 5, 16)


def _at(d: date, h: int, m: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, h, m, tzinfo=UTC)


def test_on_time_day_has_no_late_early_or_ot() -> None:
    metrics = compute_day(
        NINE_TO_FIVE,
        [_at(THURSDAY, 9, 0), _at(THURSDAY, 17, 0)],
        THURSDAY,
    )
    assert metrics.is_workday is True
    assert metrics.is_absent is False
    assert metrics.first_in == _at(THURSDAY, 9, 0)
    assert metrics.last_out == _at(THURSDAY, 17, 0)
    assert metrics.worked_minutes == 8 * 60
    assert metrics.late_minutes == 0
    assert metrics.early_out_minutes == 0
    assert metrics.overtime_minutes == 0


def test_late_without_grace_counts_full_lateness() -> None:
    metrics = compute_day(
        NINE_TO_FIVE,
        [_at(THURSDAY, 9, 30), _at(THURSDAY, 17, 0)],
        THURSDAY,
    )
    assert metrics.late_minutes == 30
    assert metrics.early_out_minutes == 0
    assert metrics.worked_minutes == 7 * 60 + 30


def test_late_within_grace_is_zero() -> None:
    spec = ShiftSpec(
        start_time=time(9, 0),
        end_time=time(17, 0),
        late_grace_minutes=10,
        early_out_grace_minutes=0,
        overtime_threshold_minutes=30,
        work_days="1111100",
    )
    # 9:09 with a 10-minute grace → 0 late.
    metrics = compute_day(spec, [_at(THURSDAY, 9, 9), _at(THURSDAY, 17, 0)], THURSDAY)
    assert metrics.late_minutes == 0


def test_late_exactly_at_grace_boundary_is_zero() -> None:
    spec = ShiftSpec(
        start_time=time(9, 0),
        end_time=time(17, 0),
        late_grace_minutes=10,
        early_out_grace_minutes=0,
        overtime_threshold_minutes=30,
        work_days="1111100",
    )
    # 9:10 exact with 10-min grace → still 0.
    metrics = compute_day(spec, [_at(THURSDAY, 9, 10), _at(THURSDAY, 17, 0)], THURSDAY)
    assert metrics.late_minutes == 0


def test_late_one_minute_past_grace_counts_only_overage() -> None:
    spec = ShiftSpec(
        start_time=time(9, 0),
        end_time=time(17, 0),
        late_grace_minutes=10,
        early_out_grace_minutes=0,
        overtime_threshold_minutes=30,
        work_days="1111100",
    )
    metrics = compute_day(spec, [_at(THURSDAY, 9, 25), _at(THURSDAY, 17, 0)], THURSDAY)
    assert metrics.late_minutes == 15  # 25 - 10 grace


def test_early_out_without_grace_counts_full_shortfall() -> None:
    metrics = compute_day(
        NINE_TO_FIVE,
        [_at(THURSDAY, 9, 0), _at(THURSDAY, 16, 30)],
        THURSDAY,
    )
    assert metrics.early_out_minutes == 30
    assert metrics.late_minutes == 0


def test_overtime_below_threshold_is_zero() -> None:
    # 5:20pm out, threshold=30min → 20 minutes past, not OT yet.
    metrics = compute_day(
        NINE_TO_FIVE,
        [_at(THURSDAY, 9, 0), _at(THURSDAY, 17, 20)],
        THURSDAY,
    )
    assert metrics.overtime_minutes == 0


def test_overtime_above_threshold_counts_only_overage() -> None:
    # 6:30pm out, threshold=30 → 90 min past - 30 grace = 60 OT.
    metrics = compute_day(
        NINE_TO_FIVE,
        [_at(THURSDAY, 9, 0), _at(THURSDAY, 18, 30)],
        THURSDAY,
    )
    assert metrics.overtime_minutes == 60


def test_non_workday_with_punches_is_not_absent_but_no_late_or_early() -> None:
    metrics = compute_day(
        NINE_TO_FIVE,
        [_at(SATURDAY, 10, 0), _at(SATURDAY, 14, 0)],
        SATURDAY,
    )
    assert metrics.is_workday is False
    assert metrics.is_absent is False
    assert metrics.late_minutes == 0
    assert metrics.early_out_minutes == 0
    assert metrics.worked_minutes == 4 * 60


def test_workday_with_no_punches_is_absent() -> None:
    metrics = compute_day(NINE_TO_FIVE, [], THURSDAY)
    assert metrics.is_workday is True
    assert metrics.is_absent is True
    assert metrics.worked_minutes == 0
    assert metrics.late_minutes == 0
    assert metrics.early_out_minutes == 0
    assert metrics.overtime_minutes == 0
    assert metrics.first_in is None
    assert metrics.last_out is None


def test_non_workday_with_no_punches_is_not_absent() -> None:
    metrics = compute_day(NINE_TO_FIVE, [], SATURDAY)
    assert metrics.is_workday is False
    assert metrics.is_absent is False
    assert metrics.worked_minutes == 0


def test_single_punch_returns_zero_worked_but_keeps_lateness() -> None:
    # One punch at 9:15 means we know they showed up late and have no out-time.
    metrics = compute_day(NINE_TO_FIVE, [_at(THURSDAY, 9, 15)], THURSDAY)
    assert metrics.first_in == _at(THURSDAY, 9, 15)
    assert metrics.last_out == _at(THURSDAY, 9, 15)
    assert metrics.worked_minutes == 0
    assert metrics.late_minutes == 15
    # Without an out-punch, "early out" treats their position as 9:15.
    # 17:00 - 9:15 = 465 min of shortfall.
    assert metrics.early_out_minutes == 465


def test_unsorted_punches_sort_correctly() -> None:
    metrics = compute_day(
        NINE_TO_FIVE,
        # Two break punches around lunch + reversed in/out order.
        [
            _at(THURSDAY, 13, 0),
            _at(THURSDAY, 17, 0),
            _at(THURSDAY, 9, 0),
            _at(THURSDAY, 12, 0),
        ],
        THURSDAY,
    )
    assert metrics.first_in == _at(THURSDAY, 9, 0)
    assert metrics.last_out == _at(THURSDAY, 17, 0)
    assert metrics.worked_minutes == 8 * 60


def test_early_in_does_not_subtract_from_late() -> None:
    # Punching in at 8:45 should not produce negative late (clamped to 0).
    metrics = compute_day(
        NINE_TO_FIVE,
        [_at(THURSDAY, 8, 45), _at(THURSDAY, 17, 0)],
        THURSDAY,
    )
    assert metrics.late_minutes == 0


def test_workday_lookup_uses_monday_index_zero() -> None:
    # 2026-05-11 is Monday → workday under "1111100".
    monday = date(2026, 5, 11)
    metrics = compute_day(NINE_TO_FIVE, [], monday)
    assert metrics.is_workday is True
    # 2026-05-17 is Sunday → not a workday.
    sunday = date(2026, 5, 17)
    metrics_sun = compute_day(NINE_TO_FIVE, [], sunday)
    assert metrics_sun.is_workday is False


def test_punches_outside_target_date_are_ignored() -> None:
    # An overnight stay: punches span midnight; compute_day(THURSDAY) only
    # considers punches that fall on THURSDAY.
    punches = [
        _at(THURSDAY, 9, 0),
        _at(THURSDAY, 17, 0),
        # Next-day punch — should not affect Thursday metrics.
        datetime(2026, 5, 15, 1, 0, tzinfo=UTC),
    ]
    metrics = compute_day(NINE_TO_FIVE, punches, THURSDAY)
    assert metrics.last_out == _at(THURSDAY, 17, 0)
    assert metrics.worked_minutes == 8 * 60


def test_holiday_on_workday_suppresses_late_early_absent() -> None:
    # THURSDAY is a workday but marked a holiday: no punches → not absent.
    spec = ShiftSpec(
        start_time=time(9, 0),
        end_time=time(17, 0),
        work_days="1111100",
        holidays=frozenset({THURSDAY}),
    )
    metrics = compute_day(spec, [], THURSDAY)
    assert metrics.is_workday is True
    assert metrics.is_holiday is True
    assert metrics.is_absent is False
    assert metrics.late_minutes == 0
    assert metrics.early_out_minutes == 0


def test_holiday_still_records_overtime_when_present() -> None:
    # Working the holiday: 9 to 18:30 should still flag OT past the threshold.
    spec = ShiftSpec(
        start_time=time(9, 0),
        end_time=time(17, 0),
        overtime_threshold_minutes=30,
        work_days="1111100",
        holidays=frozenset({THURSDAY}),
    )
    metrics = compute_day(
        spec,
        [_at(THURSDAY, 9, 0), _at(THURSDAY, 18, 30)],
        THURSDAY,
    )
    assert metrics.is_holiday is True
    assert metrics.is_absent is False
    # 90 min after scheduled end, threshold 30 → OT = 60.
    assert metrics.overtime_minutes == 60
    # Late + early still suppressed by the holiday.
    assert metrics.late_minutes == 0
    assert metrics.early_out_minutes == 0



# ---------------------------------------------------------------------------
# F39 — cross-midnight (overnight) shifts.
# ---------------------------------------------------------------------------

OVERNIGHT_22_TO_6 = ShiftSpec(
    start_time=time(22, 0),
    end_time=time(6, 0),
    late_grace_minutes=0,
    early_out_grace_minutes=0,
    overtime_threshold_minutes=30,
    work_days="1111100",  # Mon-Fri
)

FRIDAY = date(2026, 5, 15)  # Friday, so Thursday is FRIDAY - 1 (workday).


def _at_dt(dt_date: date, h: int, m: int = 0) -> datetime:
    return datetime(dt_date.year, dt_date.month, dt_date.day, h, m, tzinfo=UTC)


def test_overnight_on_time_punches_have_no_late_or_ot() -> None:
    # Thursday is a workday. Shift starts Thu 22:00, ends Fri 06:00.
    punches = [_at_dt(THURSDAY, 22, 0), _at_dt(FRIDAY, 6, 0)]
    metrics = compute_day(OVERNIGHT_22_TO_6, punches, THURSDAY)
    assert metrics.is_workday is True
    assert metrics.is_absent is False
    assert metrics.late_minutes == 0
    assert metrics.early_out_minutes == 0
    assert metrics.overtime_minutes == 0
    # 8 hours from 22:00 -> 06:00.
    assert metrics.worked_minutes == 8 * 60


def test_overnight_late_arrival_counts_against_thursday() -> None:
    # 15 minutes late at the start; clock out on time the next morning.
    punches = [_at_dt(THURSDAY, 22, 15), _at_dt(FRIDAY, 6, 0)]
    metrics = compute_day(OVERNIGHT_22_TO_6, punches, THURSDAY)
    assert metrics.late_minutes == 15
    assert metrics.early_out_minutes == 0


def test_overnight_overtime_past_morning_threshold() -> None:
    # Worked past Friday 06:30 by 30 min → OT minutes accumulate past threshold.
    # Threshold is 30 min, so a 06:45 clock-out is 45 min past end - 30 = 15 min OT.
    punches = [_at_dt(THURSDAY, 22, 0), _at_dt(FRIDAY, 6, 45)]
    metrics = compute_day(OVERNIGHT_22_TO_6, punches, THURSDAY)
    assert metrics.overtime_minutes == 15


def test_overnight_friday_with_no_punches_is_workday_absent() -> None:
    metrics = compute_day(OVERNIGHT_22_TO_6, [], FRIDAY)
    # Friday-as-on_date with no punches in the Friday-night window is absent.
    assert metrics.is_workday is True
    assert metrics.is_absent is True


def test_overnight_does_not_double_count_punches_across_days() -> None:
    # A clock-out Friday 06:00 should attribute to Thursday's shift, not
    # Friday's shift.
    punches = [_at_dt(THURSDAY, 22, 0), _at_dt(FRIDAY, 6, 0)]
    thu = compute_day(OVERNIGHT_22_TO_6, punches, THURSDAY)
    fri = compute_day(OVERNIGHT_22_TO_6, punches, FRIDAY)
    assert thu.worked_minutes == 8 * 60
    # Friday's window starts at Fri 22:00 - 2h = Fri 20:00; nothing in there.
    assert fri.first_in is None
    assert fri.is_absent is True
