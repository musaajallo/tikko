"""`/reports/*` — payroll/attendance reports.

This is the HTTP layer over `tikko.payroll.calc`. Each request:
  1. Resolves the employee + their assigned `ShiftRule`.
  2. Pulls the attendance rows for the requested month.
  3. Adapts rows into the engine's `ShiftSpec` + `list[datetime]` shape.
  4. Calls `compute_month` and serialises the result.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from tikko.auth import require_capability
from tikko.db import SessionDep
from tikko.models.attendance import AttendanceLog
from tikko.models.employee import Employee
from tikko.models.shift_rule import ShiftRule
from tikko.payroll import ShiftSpec, compute_month
from tikko.schemas.report import (
    AttendanceReport,
    AttendanceReportDay,
    AttendanceReportTotals,
    ReportEmployee,
)

router = APIRouter(prefix="/reports", tags=["reports"])

_view_reports = require_capability("view_reports")
_export_reports = require_capability("export_reports")

_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


async def _load_report_context(
    employee_id: str, month: str, session: SessionDep
) -> tuple[Employee, ShiftRule, list[datetime], int, int]:
    """Resolve employee + rule + punches for the requested month, or raise.

    Shared by JSON and CSV endpoints so the failure cases stay consistent.
    """
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="employee not found")
    if employee.shift_rule_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="employee has no assigned shift rule",
        )
    rule = await session.get(ShiftRule, employee.shift_rule_id)
    if rule is None:
        # FK target vanished — treat as misconfigured.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="assigned shift rule not found",
        )

    year_str, month_str = month.split("-")
    year, month_num = int(year_str), int(month_str)

    # Pull attendance for the month range. The range end is the first instant
    # of the next month; lt-comparison keeps the right boundary exclusive.
    start = datetime(year, month_num, 1, tzinfo=UTC)
    if month_num == 12:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(year, month_num + 1, 1, tzinfo=UTC)

    rows = (
        await session.execute(
            select(AttendanceLog.punched_at).where(
                AttendanceLog.device_user_id == employee.employee_code,
                AttendanceLog.punched_at >= start,
                AttendanceLog.punched_at < end,
            )
        )
    ).all()
    punches = [r[0] for r in rows]

    return employee, rule, punches, year, month_num


def _rule_to_spec(rule: ShiftRule) -> ShiftSpec:
    return ShiftSpec(
        start_time=rule.start_time,
        end_time=rule.end_time,
        late_grace_minutes=rule.late_grace_minutes,
        early_out_grace_minutes=rule.early_out_grace_minutes,
        overtime_threshold_minutes=rule.overtime_threshold_minutes,
        work_days=rule.work_days,
    )


@router.get(
    "/attendance",
    response_model=AttendanceReport,
    dependencies=[_view_reports],
)
async def attendance_report(
    session: SessionDep,
    employee_id: str = Query(..., description="Employee UUID"),
    month: str = Query(..., pattern=_MONTH_PATTERN, description="YYYY-MM"),
) -> AttendanceReport:
    employee, rule, punches, year, month_num = await _load_report_context(
        employee_id, month, session
    )
    days, totals = compute_month(_rule_to_spec(rule), punches, year, month_num)
    return AttendanceReport(
        month=month,
        employee=ReportEmployee(
            id=employee.id,
            employee_code=employee.employee_code,
            full_name=employee.full_name,
        ),
        days=[
            AttendanceReportDay(
                date=d.date,
                is_workday=d.is_workday,
                is_absent=d.is_absent,
                first_in=d.first_in,
                last_out=d.last_out,
                worked_minutes=d.worked_minutes,
                late_minutes=d.late_minutes,
                early_out_minutes=d.early_out_minutes,
                overtime_minutes=d.overtime_minutes,
            )
            for d in days
        ],
        totals=AttendanceReportTotals(
            days_worked=totals.days_worked,
            days_absent=totals.days_absent,
            worked_minutes=totals.worked_minutes,
            late_minutes=totals.late_minutes,
            early_out_minutes=totals.early_out_minutes,
            overtime_minutes=totals.overtime_minutes,
        ),
    )


_CSV_HEADER = [
    "date",
    "is_workday",
    "is_absent",
    "worked_minutes",
    "late_minutes",
    "early_out_minutes",
    "overtime_minutes",
]


def _csv_row_for_day(d: object) -> list[str]:
    # `d` is a DayMetrics; cast inline to keep this helper small.
    from tikko.payroll.calc import DayMetrics  # local import to dodge cycle

    assert isinstance(d, DayMetrics)
    return [
        d.date.isoformat(),
        "1" if d.is_workday else "0",
        "1" if d.is_absent else "0",
        str(d.worked_minutes),
        str(d.late_minutes),
        str(d.early_out_minutes),
        str(d.overtime_minutes),
    ]


@router.get("/attendance.csv", dependencies=[_export_reports])
async def attendance_report_csv(
    session: SessionDep,
    employee_id: str = Query(..., description="Employee UUID"),
    month: str = Query(..., pattern=_MONTH_PATTERN, description="YYYY-MM"),
) -> Response:
    employee, rule, punches, year, month_num = await _load_report_context(
        employee_id, month, session
    )
    days, totals = compute_month(_rule_to_spec(rule), punches, year, month_num)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_CSV_HEADER)
    for d in days:
        writer.writerow(_csv_row_for_day(d))
    writer.writerow(
        [
            "TOTAL",
            "",
            "",
            str(totals.worked_minutes),
            str(totals.late_minutes),
            str(totals.early_out_minutes),
            str(totals.overtime_minutes),
        ]
    )

    filename = f"attendance-{employee.employee_code}-{month}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/attendance.xlsx", dependencies=[_export_reports])
async def attendance_report_xlsx(
    session: SessionDep,
    employee_id: str = Query(..., description="Employee UUID"),
    month: str = Query(..., pattern=_MONTH_PATTERN, description="YYYY-MM"),
) -> Response:
    # Local import keeps the openpyxl cost off the cold-start path for
    # operators who only ever pull the JSON or CSV variants.
    import io as _io

    from openpyxl import Workbook

    employee, rule, punches, year, month_num = await _load_report_context(
        employee_id, month, session
    )
    days, totals = compute_month(_rule_to_spec(rule), punches, year, month_num)

    wb = Workbook()

    summary = wb.active
    summary.title = "Summary"
    summary.append(["Employee", f"{employee.full_name} (#{employee.employee_code})"])
    summary.append(["Month", month])
    summary.append([])
    summary.append(["Days worked", totals.days_worked])
    summary.append(["Days absent", totals.days_absent])
    summary.append(["Worked minutes", totals.worked_minutes])
    summary.append(["Late minutes", totals.late_minutes])
    summary.append(["Early-out minutes", totals.early_out_minutes])
    summary.append(["Overtime minutes", totals.overtime_minutes])

    daily = wb.create_sheet("Daily")
    daily.append(_CSV_HEADER)
    for d in days:
        daily.append(
            [
                d.date.isoformat(),
                bool(d.is_workday),
                bool(d.is_absent),
                d.worked_minutes,
                d.late_minutes,
                d.early_out_minutes,
                d.overtime_minutes,
            ]
        )

    buf = _io.BytesIO()
    wb.save(buf)
    filename = f"attendance-{employee.employee_code}-{month}.xlsx"
    return Response(
        content=buf.getvalue(),
        media_type=_XLSX_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
